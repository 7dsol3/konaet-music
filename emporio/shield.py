"""Application admission limits, not volumetric network DDoS mitigation."""
import asyncio
import json


class RequestShield:
    def __init__(self, app, max_body=16_384, max_inflight=24, read_timeout=5):
        self.app, self.max_body = app, max_body
        self.max_inflight, self.read_timeout = max_inflight, read_timeout
        self.inflight = 0

    async def reject(self, send, status, detail):
        payload = json.dumps({"detail": detail}).encode()
        await send({"type": "http.response.start", "status": status, "headers": [
            (b"content-type", b"application/json"), (b"cache-control", b"no-store"),
            (b"x-content-type-options", b"nosniff"), (b"retry-after", b"5")]})
        await send({"type": "http.response.body", "body": payload})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        if len(scope.get("raw_path", b"")) + len(scope.get("query_string", b"")) > 4096:
            return await self.reject(send, 414, "Request URL is too long")
        if sum(len(k)+len(v) for k, v in scope.get("headers", [])) > 32_768:
            return await self.reject(send, 431, "Request headers are too large")
        lengths = [v for k,v in scope.get("headers", []) if k.lower() == b"content-length"]
        try:
            if len(lengths) > 1 or lengths and int(lengths[0]) < 0:
                return await self.reject(send, 400, "Invalid request length")
            if lengths and int(lengths[0]) > self.max_body:
                return await self.reject(send, 413, "Request body is too large")
        except ValueError:
            return await self.reject(send, 400, "Invalid request length")
        # A single event loop admits and increments without an await between them.
        # Limits are per process; an upstream edge is needed for internet traffic.
        if self.inflight >= self.max_inflight:
            return await self.reject(send, 503, "The workspace is busy. Please retry shortly.")
        self.inflight += 1
        try:
            if scope["method"] in {"POST", "PUT", "PATCH", "DELETE"}:
                body = bytearray()
                try:
                    async with asyncio.timeout(self.read_timeout):
                        while True:
                            event = await receive()
                            if event["type"] == "http.disconnect":
                                return
                            if event["type"] != "http.request":
                                continue
                            chunk = event.get("body", b"")
                            if len(body) + len(chunk) > self.max_body:
                                return await self.reject(send, 413, "Request body is too large")
                            body.extend(chunk)
                            if not event.get("more_body", False):
                                break
                except TimeoutError:
                    return await self.reject(send, 408, "Request body timed out")
                original_receive, delivered = receive, False
                async def buffered_receive():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": bytes(body), "more_body": False}
                    return await original_receive()
                receive = buffered_receive
            return await self.app(scope, receive, send)
        finally:
            self.inflight -= 1
