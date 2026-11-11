from __future__ import annotations

import threading
import time
import hmac
import ipaddress
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, ConfigDict, Field

from .config import Settings
from .hours import human_service
from .service import AgentService
from .konaet_code import render_checkout_svg
from .tools import money
from .research import ResearchEngine
from .payments import TestPayments
from .shield import RequestShield
from .hardware import simulate as simulate_gateware, validation as gateware_validation
from .audio import MusicCoach, program as audio_program, validation as audio_validation

WEB = Path(__file__).parent / "web"
COOKIE = "emporio_session"


class WebStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        # Windows registry MIME associations differ between developer/CI hosts.
        # ES modules require a JavaScript MIME with nosniff enabled.
        if path.endswith(".mjs") and response.status_code in {200, 206, 304}:
            response.headers["Content-Type"] = "text/javascript; charset=utf-8"
        return response


class MessageBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=2000)
    locale: Literal["en", "pt"] = "en"


class VerificationBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    order_id: int = Field(ge=1)
    email: str = Field(min_length=3, max_length=254)


class CartBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=0, le=20)


class CheckoutBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request_key: str = Field(min_length=16, max_length=80)
    method: Literal["pix", "card"] = "pix"


class ResearchBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: str = Field(min_length=3, max_length=240)
    scope: Literal["open", "knowledge", "science", "code", "web"] = "open"
    synthesize: bool = False


class TestIntentBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    checkout_id: str = Field(pattern=r"^[A-Za-z0-9_-]{32}$")
    request_key: str = Field(pattern=r"^[A-Za-z0-9_-]{16,80}$")


class TestConfirmBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    decision: Literal["approve", "decline"]


class HardwareBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    cycles: int = Field(default=96, ge=16, le=192)
    capacity: int = Field(default=8, ge=1, le=32)
    refill_every: int = Field(default=5, ge=1, le=32)
    burst: int = Field(default=40, ge=1, le=192)


class AudioProgramBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    root: int = Field(default=0, ge=0, le=11)
    quality: Literal["major", "minor", "sus2", "sus4", "diminished"] = "major"
    octave: int = Field(default=3, ge=2, le=5)


class MusicExplainBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    midi: int | None = Field(default=None, ge=24, le=100)
    hz: float | None = Field(default=None, ge=30, le=3000)
    reference: float = Field(default=440.0, ge=430, le=450)
    root: int | None = Field(default=None, ge=0, le=11)
    quality: Literal["major", "minor", "sus2", "sus4", "diminished"] | None = None
    neural: bool = False


class RateLimiter:
    def __init__(self, max_keys=4096):
        self.events = defaultdict(deque)
        self.lock = threading.Lock()
        self.max_keys = max_keys
        self.next_cleanup = 0

    def check(self, key: str, limit: int) -> None:
        current = time.monotonic()
        with self.lock:
            if key not in self.events and len(self.events) >= self.max_keys:
                if current >= self.next_cleanup:
                    for old in [k for k,v in self.events.items() if not v or current-v[-1] >= 60]:
                        del self.events[old]
                    self.next_cleanup = current + 1
                if len(self.events) >= self.max_keys:
                    raise HTTPException(503, "Request tracking is at capacity. Please retry shortly.", headers={"Retry-After":"5"})
            bucket = self.events[key]
            while bucket and current-bucket[0] >= 60:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(429, "Too many requests. Please wait a minute.", headers={"Retry-After": "60"})
            bucket.append(current)


def set_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(COOKIE, session_id, httponly=True, samesite="strict", max_age=86400)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    def session_cookie(response: Response, session_id: str) -> None:
        response.set_cookie(COOKIE, session_id, httponly=True, samesite="strict", max_age=86400,
                            secure=settings.public_url.startswith("https://"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.agent = AgentService(settings)
        app.state.research = ResearchEngine(settings)
        app.state.test_payments = TestPayments(app.state.agent.store, app.state.agent.commerce, settings.state_dir)
        app.state.music_coach = MusicCoach(settings)
        yield

    app = FastAPI(title="KONAET Music", version="2.2.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None)
    limiter = RateLimiter()
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

    @app.middleware("http")
    async def request_boundary(request: Request, call_next):
        if settings.gateway_secret:
            if not hmac.compare_digest(request.headers.get("x-konaet-gateway", ""), settings.gateway_secret):
                return JSONResponse({"detail":"Use the published KONAET workspace URL."},403,headers={"Cache-Control":"no-store"})
            # This header is accepted only after authenticating our gateway.
            try:
                client_ip = str(ipaddress.ip_address(request.headers.get("x-konaet-client-ip", "")))
                request.scope["client"] = (client_ip, 0)
            except ValueError:
                pass
        # Local prototype: reject cross-site writes and DNS rebinding to an unexpected Host.
        if request.url.hostname not in {"127.0.0.1", "localhost", "::1", "testserver", urlparse(settings.public_url).hostname}:
            return JSONResponse({"detail": "This demo only accepts loopback hosts."}, 400)
        if request.method in {"POST", "DELETE", "PUT", "PATCH"}:
            origin = request.headers.get("origin")
            allowed_origins = {request.url.scheme + "://" + request.headers.get("host", ""), settings.public_url}
            if origin and origin not in allowed_origins:
                return JSONResponse({"detail": "Cross-origin writes are not allowed."}, 403)
            try:
                if int(request.headers.get("content-length", "0")) > 16_384:
                    return JSONResponse({"detail": "Request is too large."}, 413)
            except ValueError:
                return JSONResponse({"detail": "Invalid request length."}, 400)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=(self)"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(WEB / "index.html")

    @app.get("/sound-lab", include_in_schema=False)
    def sound_lab():
        return FileResponse(WEB / "sound-lab.html")

    @app.get("/service-worker.js", include_in_schema=False)
    def service_worker():
        return FileResponse(WEB / "service-worker.js", media_type="application/javascript",
                            headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})

    @app.get("/checkout/{checkout_id}", include_in_schema=False)
    def checkout_page(checkout_id: str, request: Request):
        try:
            request.app.state.agent.commerce.get_checkout(checkout_id)
        except ValueError as exc:
            return FileResponse(WEB / "checkout-unavailable.html", status_code=410 if "expired" in str(exc).lower() else 404,
                                headers={"Cache-Control":"no-store"})
        return FileResponse(WEB / "index.html")

    @app.get("/docs", include_in_schema=False)
    def api_docs():
        return FileResponse(WEB / "api.html")

    @app.get("/manual", include_in_schema=False)
    def manual():
        return FileResponse(settings.data_dir / "políticas_da_loja.pdf", media_type="application/pdf")

    @app.get("/api/health")
    def health(request: Request):
        agent = request.app.state.agent
        return {"status": "ok", "provider": settings.provider, "counts": agent.data_report["counts"],
                "product": "KONAET Music", "version": "2.2.0", "commerce_mode": "demo",
                "human_service": human_service(),
                "data_fingerprint": agent.data_report["fingerprint"], "policy_sha256": agent.policies.sha,
                "snapshot_notice": "Supplied case data; no live carrier or inventory connection."}

    @app.get("/api/capabilities")
    def capabilities(request: Request, probe_model: bool = False):
        model_state = "configured_not_probed" if settings.provider == "openai_compatible" else "local_tools_ready"
        if probe_model and settings.provider == "openai_compatible":
            limiter.check("model_probe:" + (request.client.host if request.client else "local"), 10)
            from .research import request_json
            try:
                if not settings.model_url.endswith("/chat/completions"):
                    raise ValueError("This model endpoint has no supported discovery route")
                headers = {"Authorization": "Bearer " + settings.model_key} if settings.model_key else {}
                found = request_json(settings.model_url.removesuffix("/chat/completions") + "/models", timeout=2, headers=headers)
                model_state = "connected" if settings.model in {m.get("id") for m in found.get("data", [])} else "responding_model_unconfirmed"
            except (ValueError, TypeError, KeyError, OSError, TimeoutError):
                model_state = "unavailable"
        return {"product": "KONAET Music", "version": "2.2.0", "backend": "ready",
                "catalog": {"count": request.app.state.agent.data_report["counts"]["products"], "mode": "case_snapshot"},
                "agent": {"provider": settings.provider, "model": settings.model if settings.provider == "openai_compatible" else None,
                          "state": model_state,
                          "training": "No neural weight training is performed by this application"},
                "research": request.app.state.research.capabilities(),
                "checkout": {"mode": "sandbox", "can_charge_real_money": False, "receipt_seal": "HMAC-SHA256; server verification only",
                             "links_shareable": settings.public_url.startswith("https://")},
                "protection": {"body_limit_bytes": 16384, "read_timeout_seconds": 5, "max_inflight_per_process": 24,
                               "edge_ddos": "not_provisioned"},
                "sovereign": {"mode": "commitment_export", "network_finalized": False},
                "hardware": {"mode": "simulation", "physical_device_connected": False, "validation": gateware_validation()},
                "sound_lab": {"mode": "browser_dsp", "audio_upload": False, "microphone": "explicit_opt_in",
                              "chord_recognition": "heuristic_triads_only", "audio_core": audio_validation()}}

    @app.post("/api/audio/program")
    def make_audio_program(body: AudioProgramBody, request: Request):
        limiter.check("audio_program:" + (request.client.host if request.client else "local"), 30)
        return audio_program(**body.model_dump())

    @app.post("/api/music/explain")
    def music_explain(body: MusicExplainBody, request: Request):
        limiter.check("music_explain:" + (request.client.host if request.client else "local"), 10)
        complete_pitch = body.midi is not None and body.hz is not None
        complete_chord = body.root is not None and body.quality is not None
        if complete_pitch == complete_chord or (body.midi is None) != (body.hz is None) or (body.root is None) != (body.quality is None):
            raise HTTPException(422, "Send exactly one complete pitch pair or chord pair")
        try:
            return request.app.state.music_coach.explain(**body.model_dump())
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/hardware/simulate")
    def hardware(body: HardwareBody, request: Request):
        limiter.check("hardware:" + (request.client.host if request.client else "local"), 20)
        try:
            return simulate_gateware(body.cycles, body.capacity, body.refill_every, body.burst)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/research")
    def research(body: ResearchBody, request: Request):
        limiter.check("research:" + (request.client.host if request.client else "local"), 6)
        try:
            return request.app.state.research.query(body.query, body.scope, body.synthesize)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    def owned_session(request):
        agent = request.app.state.agent
        session_id = request.cookies.get(COOKIE, "")
        from datetime import datetime, timezone
        with agent.store.connect() as db:
            state = db.execute("SELECT id FROM sessions WHERE id=? AND expires>?", (session_id, datetime.now(timezone.utc).isoformat())).fetchone() if len(session_id) <= 128 else None
        if not state:
            raise HTTPException(401, "Open a workspace session first")
        return state["id"]

    @app.get("/api/sandbox/wallet")
    def test_wallet(request: Request):
        return request.app.state.test_payments.wallet(owned_session(request))

    @app.post("/api/sandbox/wallet/topup")
    def test_topup(request: Request):
        limiter.check("test_topup:" + (request.client.host if request.client else "local"), 5)
        try:
            return request.app.state.test_payments.wallet(owned_session(request), topup=True)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/api/sandbox/intents")
    def test_intent(body: TestIntentBody, request: Request):
        limiter.check("test_intent:" + (request.client.host if request.client else "local"), 10)
        try:
            return request.app.state.test_payments.create(owned_session(request), body.checkout_id, body.request_key)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/api/sandbox/intents/{intent_id}/confirm")
    def test_confirm(intent_id: str, body: TestConfirmBody, request: Request):
        limiter.check("test_confirm:" + (request.client.host if request.client else "local"), 10)
        try:
            return request.app.state.test_payments.confirm(owned_session(request), intent_id, body.decision)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/api/sandbox/intents/{intent_id}")
    def read_test_intent(intent_id: str, request: Request):
        try:
            return request.app.state.test_payments.get(owned_session(request), intent_id)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/api/session")
    def session(request: Request, response: Response):
        limiter.check("session:" + (request.client.host if request.client else "local"), 20)
        agent = request.app.state.agent
        with agent.lock:
            state = agent.store.session(request.cookies.get(COOKIE))
        session_cookie(response, state["id"])
        return {"history": state["history"], "verified": state["customer_id"] is not None}

    @app.delete("/api/session")
    def reset(request: Request, response: Response):
        agent = request.app.state.agent
        with agent.lock:
            agent.store.forget_session(request.cookies.get(COOKIE, ""))
            state = agent.store.session()
        session_cookie(response, state["id"])
        return {"status": "cleared"}

    @app.post("/api/chat")
    def chat(body: MessageBody, request: Request, response: Response):
        limiter.check("chat:" + (request.client.host if request.client else "local"), 40)
        try:
            result = request.app.state.agent.turn(body.message, request.cookies.get(COOKIE), locale=body.locale)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        session_cookie(response, result.pop("session_id"))
        return result

    @app.post("/api/verify")
    def verify(body: VerificationBody, request: Request, response: Response):
        limiter.check("verify:" + (request.client.host if request.client else "local"), 5)
        agent = request.app.state.agent
        with agent.lock:
            state = agent.store.session(request.cookies.get(COOKIE))
            valid = agent.store.verify_order(state, body.order_id, body.email)
            if valid:
                state["context"]["last_order"] = body.order_id
                agent.store.save_session(state)
            agent.store.audit(state["id"], "verify_order", [], "verified" if valid else "unavailable")
        session_cookie(response, state["id"])
        return {"verified": valid, "message": "Order verified for this session." if valid else "Could not verify those details. Please check the order number and purchase email."}

    @app.get("/api/catalog")
    def catalog(request: Request, query: str = "", category_id: int | None = None):
        try:
            return request.app.state.agent.tools.execute("search_products", {
                "query": query, "category_id": category_id, "available_only": False, "limit": 8})
        except ValueError as exc:
            raise HTTPException(422, "Invalid catalog filter") from exc

    @app.get("/api/policies")
    def policies(request: Request, locale: Literal["en", "pt"] = "en"):
        from .policies import CARDS
        from .i18n import POLICIES_PT
        return [{"topic": topic, "title": title, "summary": summary, "pages": pages}
                if locale == "en" else {"topic": topic, "title": POLICIES_PT[topic][0], "summary": POLICIES_PT[topic][1], "pages": pages}
                for topic, (title, pages, summary) in CARDS.items()]

    @app.get("/api/shop")
    def shop(request: Request, query: str = "", category_id: int | None = None,
             max_price_brl: str | None = None, available_only: bool = False,
             sort: Literal["featured", "price_asc", "price_desc", "name"] = "featured"):
        if len(query) > 160 or max_price_brl is not None and len(max_price_brl) > 20:
            raise HTTPException(422, "Catalog filter is too long")
        if category_id is not None and not 1 <= category_id <= 9:
            raise HTTPException(422, "Unknown category")
        try:
            return request.app.state.agent.commerce.catalog(query, category_id, max_price_brl, available_only, sort)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/compare")
    def compare(request: Request, ids: str = ""):
        if len(ids) > 40:
            raise HTTPException(422, "Choose up to three instruments")
        try:
            return request.app.state.agent.commerce.compare([int(i) for i in ids.split(",")])
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/cart")
    def get_cart(request: Request, response: Response):
        agent = request.app.state.agent
        with agent.lock:
            state = agent.store.session(request.cookies.get(COOKIE))
            result = agent.commerce.cart(state["id"])
        session_cookie(response, state["id"])
        return result

    @app.put("/api/cart")
    def set_cart(body: CartBody, request: Request, response: Response):
        limiter.check("cart:" + (request.client.host if request.client else "local"), 60)
        agent = request.app.state.agent
        with agent.lock:
            state = agent.store.session(request.cookies.get(COOKIE))
            try:
                result = agent.commerce.set_item(state["id"], body.product_id, body.quantity)
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
        session_cookie(response, state["id"])
        return result

    @app.post("/api/checkout")
    def prepare_checkout(body: CheckoutBody, request: Request, response: Response):
        limiter.check("checkout:" + (request.client.host if request.client else "local"), 10)
        agent = request.app.state.agent
        with agent.lock:
            state = agent.store.session(request.cookies.get(COOKIE))
            try:
                result = agent.commerce.checkout(state["id"], body.request_key, body.method)
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from exc
        session_cookie(response, state["id"])
        return result

    @app.get("/api/checkout/{checkout_id}")
    def read_checkout(checkout_id: str, request: Request):
        try:
            return request.app.state.agent.commerce.get_checkout(checkout_id)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/api/checkout/{checkout_id}/code.svg")
    def checkout_code(checkout_id: str, request: Request, theme: Literal["signature", "orbit", "studio"] = "signature"):
        try:
            quote = request.app.state.agent.commerce.get_checkout(checkout_id)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        svg = render_checkout_svg(quote["checkout_url"], quote["id"], money(quote["subtotal_cents"]), theme)
        return Response(svg, media_type="image/svg+xml", headers={"Cache-Control": "no-store",
                        "Content-Disposition": 'inline; filename="konaet-checkout.svg"'})

    app.mount("/static", WebStaticFiles(directory=WEB), name="static")
    app.add_middleware(RequestShield)
    return app
