from __future__ import annotations

import threading
import time
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

WEB = Path(__file__).parent / "web"
COOKIE = "emporio_session"


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


class RateLimiter:
    def __init__(self):
        self.events = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str, limit: int) -> None:
        current = time.monotonic()
        with self.lock:
            bucket = self.events[key]
            while bucket and current-bucket[0] >= 60:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(429, "Too many requests. Please wait a minute.", headers={"Retry-After": "60"})
            bucket.append(current)
            # Bound inactive keys for a long-running local service.
            if len(self.events) > 4096:
                for old in [k for k, v in self.events.items() if not v or current-v[-1] > 60]:
                    del self.events[old]


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
        yield

    app = FastAPI(title="KONAET Music", version="2.0.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None)
    limiter = RateLimiter()
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

    @app.middleware("http")
    async def request_boundary(request: Request, call_next):
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
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(WEB / "index.html")

    @app.get("/service-worker.js", include_in_schema=False)
    def service_worker():
        return FileResponse(WEB / "service-worker.js", media_type="application/javascript",
                            headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})

    @app.get("/checkout/{checkout_id}", include_in_schema=False)
    def checkout_page(checkout_id: str, request: Request):
        try:
            request.app.state.agent.commerce.get_checkout(checkout_id)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
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
                "product": "KONAET Music", "version": "2.0.0", "commerce_mode": "demo",
                "human_service": human_service(),
                "data_fingerprint": agent.data_report["fingerprint"], "policy_sha256": agent.policies.sha,
                "snapshot_notice": "Supplied case data; no live carrier or inventory connection."}

    @app.get("/api/session")
    def session(request: Request, response: Response):
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
    def checkout_code(checkout_id: str, request: Request):
        try:
            quote = request.app.state.agent.commerce.get_checkout(checkout_id)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        svg = render_checkout_svg(quote["checkout_url"], quote["id"], money(quote["subtotal_cents"]))
        return Response(svg, media_type="image/svg+xml", headers={"Cache-Control": "no-store",
                        "Content-Disposition": 'inline; filename="konaet-checkout.svg"'})

    app.mount("/static", StaticFiles(directory=WEB), name="static")
    return app
