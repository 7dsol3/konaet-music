import hashlib
import json
import urllib.error
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from emporio.api import create_app
from emporio.research import NoRedirect, ResearchEngine, public_link
from emporio.storage import canonical


def fake_public_api(url, **kwargs):
    if "w/api.php" in url:
        return {"query":{"pages":[{"title":"Quantum computing","extract":"Quantum computing uses quantum mechanics to process information."}]}}
    if "wikipedia.org" in url:
        return {"pages":[{"title":"Quantum computing","key":"Quantum_computing","excerpt":"An <span>introductory</span> excerpt."}]}
    if "crossref.org" in url:
        return {"message":{"items":[{"title":["Quantum research"],"DOI":"10.1234/example","publisher":"Example publisher","type":"journal-article","published":{"date-parts":[[2026,11,1]]}}]}}
    if "api.github.com" in url:
        return {"items":[{"full_name":"example/tinyml","html_url":"https://github.com/example/tinyml","description":"A public repository","updated_at":"2026-11-01T00:00:00Z"}]}
    if "api.search.brave.com" in url:
        assert kwargs["headers"]["X-Subscription-Token"] == "test-only-key"
        return {"web":{"results":[{"title":"Official docs","url":"https://example.org/docs","description":"Documented example"},{"title":"bad","url":"javascript:alert(1)","description":"bad"}]}}
    raise AssertionError("Unexpected provider URL")


def test_federated_sources_have_receipts_and_cached_results_keep_their_identity(settings, monkeypatch):
    monkeypatch.setattr("emporio.research.request_json", fake_public_api)
    engine=ResearchEngine(settings)
    first=engine.query("quantum computing")
    assert len(first["sources"])==2
    assert first["sources"][0]["excerpt"].startswith("Quantum computing uses")
    assert all(p["status"]=="ok" for p in first["providers"])
    assert first["sources"][1]["published_at"]=="2026-11-01"
    again=engine.query("quantum computing")
    assert again["from_cache"] and not first["from_cache"]
    for result in (first,again):
        payload={k:v for k,v in result.items() if k not in {"receipt_sha256","from_cache","latency_ms"}}
        assert hashlib.sha256(canonical(payload).encode()).hexdigest()==result["receipt_sha256"]
    again["sources"].clear()
    assert engine.query("quantum computing")["sources"]


@pytest.mark.parametrize("value",["javascript:alert(1)","http://example.org","https://localhost/private","https://127.0.0.1/","https://[::1]/","https://user:password@example.org/","https://example.org:444/","https://example.internal/x","https://example.org/\nsecret"])
def test_unsafe_links_are_omitted(value):
    assert public_link(value) is None


@pytest.mark.parametrize("query",["x","a"*241,"person@example.org","status of order #123","ghp_abc123456","-----BEGIN PRIVATE KEY-----","abc\x00def"])
def test_private_or_invalid_queries_never_reach_a_provider(settings, monkeypatch, query):
    monkeypatch.setattr("emporio.research.request_json",lambda *a,**k:pytest.fail("Private query was transmitted"))
    with pytest.raises(ValueError):
        ResearchEngine(settings).query(query)


def test_web_search_is_honestly_unconfigured_without_a_key(settings, monkeypatch):
    monkeypatch.setattr("emporio.research.request_json",lambda *a,**k:pytest.fail("Unconfigured provider was called"))
    result=ResearchEngine(settings).query("public example","web")
    assert not result["sources"] and result["providers"][0]["status"]=="not_configured"


def test_configured_web_provider_keeps_keys_out_of_returned_results(settings, monkeypatch):
    monkeypatch.setattr("emporio.research.request_json",fake_public_api)
    result=ResearchEngine(replace(settings,brave_search_key="test-only-key")).query("public docs","web")
    assert len(result["sources"])==1
    assert "test-only-key" not in json.dumps(result)


def test_provider_failure_is_partial_and_never_invented(settings, monkeypatch):
    def fail_one(url,**kwargs):
        if "crossref.org" in url:raise urllib.error.HTTPError(url,429,"rate limit",{},None)
        return fake_public_api(url,**kwargs)
    monkeypatch.setattr("emporio.research.request_json",fail_one)
    r=ResearchEngine(settings).query("quantum computing")
    assert len(r["sources"])==1 and r["providers"][1]["status"]=="rate_limited"


def test_provider_calls_are_bounded_even_with_different_queries(settings, monkeypatch):
    monkeypatch.setattr("emporio.research.request_json",fake_public_api)
    engine=ResearchEngine(settings)
    for i in range(8):engine.query("topic "+str(i),"code")
    assert engine.query("topic nine","code")["providers"][0]["status"]=="rate_limited"


@pytest.mark.parametrize("valid",[True,False])
def test_model_synthesis_is_labeled_and_unknown_citations_fall_back(settings, monkeypatch, valid):
    s=replace(settings,provider="openai_compatible",model_url="http://127.0.0.1:9999/v1/chat/completions",model="test-model")
    def model(url,**kwargs):
        if url.endswith("chat/completions"):
            request=json.loads(kwargs["body"])
            assert "email" not in str(request).lower() and "history" not in request
            assert request["response_format"]=={"type":"json_object"}
            return {"choices":[{"message":{"content":json.dumps({"message":"A sourced statement [S1]." if valid else "An invented citation [S99]."})}}]}
        return fake_public_api(url,**kwargs)
    monkeypatch.setattr("emporio.research.request_json",model)
    r=ResearchEngine(s).query("quantum computing","knowledge",True)
    assert r["mode"]==("research_model" if valid else "research_excerpts")
    assert r["synthesis_status"]==("completed" if valid else "unavailable_used_source_brief")


def test_redirects_are_rejected_instead_of_forwarding_provider_credentials():
    with pytest.raises(ValueError,match="redirect"):
        NoRedirect().redirect_request(None,None,302,"redirect",{},"http://localhost/private")


def test_research_http_contract_capabilities_and_cross_site_boundary(settings, monkeypatch):
    monkeypatch.setattr("emporio.research.request_json",fake_public_api)
    with TestClient(create_app(settings)) as c:
        caps=c.get("/api/capabilities").json()
        assert caps["checkout"]["can_charge_real_money"] is False
        assert caps["hardware"]["physical_device_connected"] is False
        assert c.post("/api/research",json={"query":"quantum computing"}).json()["sources"]
        assert c.post("/api/research",json={"query":"quantum computing","session_id":"forged"}).status_code==422
        assert c.post("/api/research",json={"query":"quantum computing"},headers={"Origin":"https://evil.example"}).status_code==403
        assert c.post("/api/research",json={"query":"Find order #123"}).status_code==422
