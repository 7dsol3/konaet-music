import asyncio

import pytest
from fastapi.testclient import TestClient

from emporio.api import create_app
from emporio.api import RateLimiter
from fastapi import HTTPException
from emporio.hardware import simulate, trace_model
from emporio.shield import RequestShield


def test_chunked_oversize_is_rejected_before_downstream_parsing():
    async def run():
        called=[];sent=[];events=iter([{"type":"http.request","body":b"x"*10000,"more_body":True},{"type":"http.request","body":b"x"*10000,"more_body":False}])
        async def receive():return next(events)
        async def send(value):sent.append(value)
        async def downstream(*args):called.append(True)
        shield=RequestShield(downstream)
        await shield({"type":"http","method":"POST","headers":[]},receive,send)
        assert not called and sent[0]["status"]==413 and shield.inflight==0
    asyncio.run(run())


def test_slow_body_times_out_and_releases_admission_slot():
    async def run():
        sent=[]
        async def receive():await asyncio.sleep(1)
        async def send(value):sent.append(value)
        async def app(*args):pytest.fail("Slow body reached the application")
        shield=RequestShield(app,read_timeout=.01)
        await shield({"type":"http","method":"POST","headers":[]},receive,send)
        assert sent[0]["status"]==408 and shield.inflight==0
    asyncio.run(run())


def test_concurrency_admission_is_bounded():
    async def run():
        entered=asyncio.Event();release=asyncio.Event();sent=[]
        async def app(scope,receive,send):entered.set();await release.wait()
        async def receive():return {"type":"http.disconnect"}
        async def send(value):sent.append(value)
        shield=RequestShield(app,max_inflight=1)
        first=asyncio.create_task(shield({"type":"http","method":"GET","headers":[]},receive,send))
        await entered.wait()
        await shield({"type":"http","method":"GET","headers":[]},receive,send)
        assert sent[0]["status"]==503
        release.set();await first
        assert shield.inflight==0
    asyncio.run(run())


def test_rate_limiter_cannot_grow_without_bound_under_new_client_keys():
    limiter=RateLimiter(max_keys=2)
    limiter.check("client-one",3);limiter.check("client-two",3)
    with pytest.raises(HTTPException) as error:limiter.check("client-three",3)
    assert error.value.status_code==503 and len(limiter.events)==2
    limiter.check("client-one",3)


def test_public_origin_requires_the_gateway_secret_and_does_not_expose_it(settings):
    from dataclasses import replace
    secret="test-gateway-credential-"+"a"*32
    configured=replace(settings,gateway_secret=secret)
    assert secret not in repr(configured)
    with TestClient(create_app(configured)) as c:
        assert c.get("/api/health").status_code==403
        assert c.get("/api/health",headers={"X-Konaet-Gateway":"forged"}).status_code==403
        response=c.get("/api/capabilities",headers={"X-Konaet-Gateway":secret,"X-Konaet-Client-IP":"203.0.113.7"})
        assert response.status_code==200 and secret not in response.text


def test_logical_gate_limits_bursts_and_refills_without_overflow():
    rows=trace_model([(True,False)]*12+[(False,True)]*20,8)
    assert sum(r["admitted"] for r in rows)==8 and sum(r["rejected"] for r in rows)==4
    assert rows[-1]["credits"]==8
    assert all(0<=r["credits"]<=8 and not(r["admitted"] and r["rejected"]) for r in rows)
    assert trace_model([(True,False),(True,True)],1)[-1]["admitted"]


def test_hardware_endpoint_is_simulation_and_rejects_unbounded_inputs(settings):
    with TestClient(create_app(settings)) as c:
        response=c.post("/api/hardware/simulate",json={"cycles":96,"capacity":8,"burst":40,"refill_every":5})
        assert response.status_code==200 and len(response.json()["trace"])==96
        assert response.json()["physical_device_connected"] is False
        assert c.post("/api/hardware/simulate",json={"cycles":100000}).status_code==422
        assert c.post("/api/hardware/simulate",json={"cycles":16,"burst":40}).status_code==422
        assert c.post("/api/hardware/simulate",json={"capacity":True}).status_code==422
