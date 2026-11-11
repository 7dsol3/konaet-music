import json
from dataclasses import replace
from datetime import date

import pytest

from emporio.planner import Call, Plan, ModelPlanner
from emporio.service import AgentService


@pytest.mark.parametrize("condition", [
    "It is unused without original packaging.",
    "Está sem uso, mas sem a embalagem original.",
    "It is unused in original packaging, but the manual and accessories are missing.",
])
def test_missing_packaging_or_materials_is_not_a_clear_return(agent, condition):
    answer = agent.turn("I want to return an online purchase. I received it on 2026-11-10. " + condition, today=date(2026,11,11))
    assert answer["results"][0]["status"] == "human_review"


@pytest.mark.parametrize("arguments", [
    {"category_id": 1, "max_price_brl": None},
    {"category_id": 5, "max_price_brl": "9999"},
    {"category_id": 5, "max_price_brl": "1000", "available_only": False},
])
def test_model_cannot_broaden_explicit_catalog_constraints(settings, arguments):
    agent = AgentService(replace(settings, provider="openai_compatible", model="stub", model_url="http://127.0.0.1:1/v1/chat/completions"))
    agent.model.plan = lambda *_: Plan([Call("search_products", arguments)], mode="openai_compatible")
    answer = agent.turn("Show acoustic guitars under BRL 1,000")
    assert answer["mode"] == "local_fallback"
    assert answer["results"][0]["products"]
    assert all(p["category_id"] == 5 and p["sale_cents"] <= 100000 and p["available"] for p in answer["results"][0]["products"])


def test_private_context_and_order_history_are_not_sent_to_provider(settings, monkeypatch):
    captured = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def read(self, _): return json.dumps({"choices": [{"message": {"tool_calls": [{"function": {"name": "search_products", "arguments": "{}"}}]}}]}).encode()
    def urlopen(request, **_):
        captured.append(json.loads(request.data)); return Response()
    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    planner = ModelPlanner(replace(settings, provider="openai_compatible", model="stub", model_url="http://127.0.0.1:1/v1/chat/completions"))
    planner.plan("Find an instrument", {"category": 5, "last_products": [83], "last_order": 8, "customer_id": 987654321,
                 "return_facts": {"received_date": "2026-11-10"}}, [{"role": "user", "content": "Where is order #8? private@example.com"}], date(2026,11,11))
    sent = captured[0]
    context = json.loads(sent["messages"][0]["content"].split("Public conversation context: ",1)[1])
    assert set(context) == {"category", "last_products"}
    payload = json.dumps(sent)
    assert "order #8" not in payload and "987654321" not in payload and "private@example.com" not in payload and "2026-11-10" not in payload


def test_private_order_does_not_invoke_model(settings):
    agent = AgentService(replace(settings, provider="openai_compatible", model="stub", model_url="http://127.0.0.1:1/v1/chat/completions"))
    called = []
    def plan(*_):
        called.append(True)
        raise RuntimeError("Unexpected provider call")
    agent.model.plan = plan
    result = agent.turn("Where is order 8?")
    assert not called and result["mode"] == "local" and result["results"][0]["status"] == "verification_required"


def test_number_leading_model_remains_selected_for_pix_followup(agent):
    first = agent.turn("What is the price and availability of Taylor 110e Dreadnought Natural?")
    assert [p["id"] for p in first["results"][0]["products"]] == [94]
    second = agent.turn("What would the PIX price be?", first["session_id"])
    assert second["results"][0]["kind"] == "payment"
    assert second["results"][0]["total_cents"] == 551908
