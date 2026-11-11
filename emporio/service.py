from __future__ import annotations

import threading
import time
from datetime import date, datetime, timedelta, timezone

from .config import Settings
from .hours import human_service
from .i18n import MESSAGES_PT, render_pt
from .planner import LocalPlanner, ModelPlanner, redact
from .policies import PolicyBook, topics_for
from .renderer import render
from .storage import Store
from .tools import Tools
from .commerce import Commerce


class AgentService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = Store(settings.state_dir / "store.sqlite3")
        self.data_report = self.store.import_data(settings.data_dir)
        self.policies = PolicyBook(settings.data_dir, settings.state_dir / "policies.sqlite3")
        self.tools = Tools(self.store, self.policies)
        self.commerce = Commerce(self.store, self.tools, settings)
        self.local = LocalPlanner(self.store)
        self.model = ModelPlanner(settings) if settings.provider != "local" else None
        self.lock = threading.RLock()

    def turn(self, text: str, session_id: str | None = None, *, today: date | None = None, locale: str = "en") -> dict:
        if locale not in {"en", "pt"}:
            raise ValueError("Language must be en or pt")
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValueError("Send a message between 1 and 2,000 characters")
        started = time.perf_counter()
        today = today or datetime.now(timezone(timedelta(hours=-4))).date()
        with self.lock:
            session = self.store.session(session_id)
            text = redact(text.strip())
            plan = self.local.plan(text, session["context"], today)
            # Private order requests do not need an external planning round.
            if self.model and plan.calls and not any(c.name == "get_order" for c in plan.calls):
                try:
                    model_plan = self.model.plan(text, session["context"], session["history"], today)
                    explicit_tools = {c.name for c in plan.calls} & {"search_products", "get_product", "get_order", "quote_payment", "quote_shipping", "assess_return"}
                    if explicit_tools and any(c.name not in explicit_tools for c in model_plan.calls):
                        raise ValueError("Model plan conflicts with an explicitly resolved customer intent")
                    # The model may plan retrieval, but cannot supply missing customer facts.
                    for model_call in model_plan.calls:
                        if model_call.name == "search_products":
                            expected_calls = [c for c in plan.calls if c.name == "search_products"]
                            if not expected_calls:
                                raise ValueError("Unrequested catalog intent")
                            expected = self.tools_argument_defaults(expected_calls[0])
                            supplied = self.tools_argument_defaults(model_call)
                            for field in ("category_id", "max_price_brl"):
                                if expected[field] is not None and supplied[field] != expected[field]:
                                    raise ValueError("Model changed an explicit catalog filter")
                            if expected["query"] and supplied["query"] != expected["query"]:
                                raise ValueError("Model changed an explicit brand or model")
                            if expected["available_only"] and not supplied["available_only"]:
                                raise ValueError("Model dropped availability")
                        if model_call.name == "search_policies":
                            expected = set(topics_for(text))
                            supplied = set(topics_for(model_call.arguments.get("query", "")))
                            selected_topic = model_call.arguments.get("topic")
                            supplied.add(selected_topic)
                            if expected and selected_topic is not None and selected_topic not in expected:
                                raise ValueError("Model added an unrelated policy topic")
                            if not expected.issubset(supplied):
                                raise ValueError("Model dropped an explicit policy topic")
                        if model_call.name == "assess_return":
                            model_call.arguments = dict(session["context"].get("return_facts", {}))
                        if model_call.name in {"get_product", "get_order", "quote_payment", "quote_shipping"}:
                            matching = [c for c in plan.calls if c.name == model_call.name]
                            if not any(model_call.arguments == self.tools_argument_defaults(c) for c in matching):
                                raise ValueError("Model changed an explicit transaction argument")
                    plan = model_plan
                except Exception:
                    # Never leak provider URLs, keys, raw response bodies or identity details.
                    plan.mode, plan.fallback_reason = "local_fallback", "Model planning unavailable, invalid or inconsistent with explicit facts; local rules used."
            results, traces, sources, messages = [], [], [], []
            if plan.message:
                messages.append(MESSAGES_PT.get(plan.message, plan.message) if locale == "pt" else plan.message)
            for call in plan.calls:
                try:
                    result = self.tools.execute(call.name, call.arguments, session["customer_id"], today)
                except (ValueError, TypeError):
                    messages.append("Não consegui validar esses dados. Confira o modelo, valor ou data e tente novamente." if locale == "pt" else "I could not validate those details. Please check the model, amount or date and try again.")
                    traces.append({"tool": call.name, "status": "invalid_arguments"})
                    continue
                results.append(result)
                messages.append(render_pt(result) if locale == "pt" else render(result))
                sources.extend(result.get("sources", []))
                traces.append({"tool": call.name, "status": result.get("status", "checked"), "arguments": call.arguments})
                if result["kind"] == "catalog" and result["products"]:
                    session["context"]["last_products"] = [p["id"] for p in result["products"]]
                if result["kind"] == "return" and result["status"] not in {"needs_information", "invalid_date"}:
                    session["context"].pop("return_pending", None)
                    session["context"].pop("return_facts", None)
            message = "\n\n".join(messages)
            sources = list({s["id"]: s for s in sources}.values())
            session["history"] += [{"role": "user", "content": text}, {"role": "assistant", "content": message}]
            self.store.save_session(session)
            audit_hash = self.store.audit(session["id"], ",".join(c.name for c in plan.calls) or "conversation",
                                         [s["id"] for s in sources], plan.mode)
        return {"session_id": session["id"], "message": message, "sources": sources, "results": results,
                "human_service": human_service(),
                "locale": locale,
                "tools": traces, "mode": plan.mode, "fallback_reason": plan.fallback_reason,
                "latency_ms": round((time.perf_counter()-started)*1000, 1), "audit_hash": audit_hash}

    @staticmethod
    def tools_argument_defaults(call) -> dict:
        from .tools import TOOL_MODELS
        return TOOL_MODELS[call.name].model_validate(call.arguments).model_dump()
