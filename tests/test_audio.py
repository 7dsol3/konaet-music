import json
import math
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from emporio.api import create_app
from emporio.audio import MusicCoach, dds_trace, meter_trace, program, triangle, validation


def test_meter_covers_signed_extremes_and_drops_partial_blocks():
    rows = meter_trace([(False, True, -32768)] * 64)
    assert sum(row["valid"] for row in rows) == 1
    assert rows[-1] == {"valid": True, "peak": 32768, "energy": 2**36, "clipped": 64}
    rows = meter_trace([(False, True, 32767)] * 63 + [(True, True, -32768)] + [(False, True, 1)] * 64)
    assert sum(row["valid"] for row in rows) == 1
    assert rows[-1] == {"valid": True, "peak": 1, "energy": 64, "clipped": 0}


def test_meter_valid_gaps_and_clip_threshold():
    rows = meter_trace([(False, i % 2 == 0, -32700 if i < 64 else 32699) for i in range(128)])
    assert rows[-2]["valid"] and not rows[-1]["valid"]
    assert rows[-1]["clipped"] == 32
    with pytest.raises(ValueError):
        meter_trace([(False, True, 32768)])


def test_dds_quadrants_wrapping_mute_and_clock_enable():
    assert [triangle(phase) for phase in (0, 0x40000000, 0x80000000, 0xC0000000, 0xFFFFFFFF)] == [-32768, 0, 32767, -1, -32767]
    step = [0x40000000] * 3
    rows = dds_trace([(False, True, False, 7, step)] * 5)
    assert [row["sample"] for row in rows] == [0, 12287, -1, -12288, 0]
    rows += dds_trace([(False, True, True, 7, step), (False, False, False, 7, step)])
    assert rows[-1] == {"valid": False, "sample": 0}


def test_program_uses_checked_frequency_increments_and_exact_meters():
    result = program(9, "minor", 3)
    assert result["notes"] == ["A3", "C4", "E4"]
    assert result["phase_steps"] == [round(hz * 2**32 / 48000) for hz in (220, 261.6255653005986, 329.6275569128699)]
    assert result["physical_device_connected"] is False
    assert len(result["preview_pcm16"]) == 512 and len(result["meter_blocks"]) == 8
    for i, block in enumerate(result["meter_blocks"]):
        chunk = result["preview_pcm16"][i * 64:(i + 1) * 64]
        assert block["energy"] == sum(v * v for v in chunk)
        assert block["peak"] == max(map(abs, chunk))
    assert validation()["physical_device_tested"] is False


def test_audio_api_is_strict_and_has_a_dedicated_page(settings):
    with TestClient(create_app(settings)) as client:
        page = client.get("/sound-lab")
        assert page.status_code == 200 and 'lang="en"' in page.text
        assert "media-src 'self' blob:" in page.headers["content-security-policy"]
        assert 'microphone=(self)' in page.headers['permissions-policy']
        assert client.get('/static/sound-lab.mjs').status_code == 200
        assert client.get('/static/sound-dsp.mjs').headers['content-type'].startswith(('text/javascript', 'application/javascript'))
        assert client.post('/api/audio/program', json={'root': 9, 'quality': 'minor', 'octave': 3}).json()['notes'] == ['A3', 'C4', 'E4']
        for body in ({'root': True}, {'root': 12}, {'quality': 'unknown'}, {'audio': [0]}, {'octave': '3'}):
            assert client.post('/api/audio/program', json=body).status_code == 422
        assert client.get('/api/capabilities').json()['sound_lab']['audio_upload'] is False


def test_coach_checks_complete_pairs_and_pitch_consistency(settings):
    with TestClient(create_app(settings)) as client:
        result = client.post('/api/music/explain', json={'midi': 69, 'hz': 440.0}).json()
        assert result['audio_uploaded'] is False and result['mode'] == 'checked_music_rules'
        assert 'A4' in result['facts'][0]
        for body in ({}, {'midi': 69}, {'midi': 69, 'hz': 100.0}, {'root': 0}, {'root': 0, 'quality': 'major', 'midi': 69, 'hz': 440.0}, {'filename': 'private.wav'}, {'midi': True, 'hz': 440.0}):
            assert client.post('/api/music/explain', json=body).status_code == 422


def test_neural_coach_receives_public_music_facts_only(settings, monkeypatch):
    configured = replace(settings, provider='openai_compatible', model_url='http://localhost:8081/v1/chat/completions', model='test-model')
    sent = []
    def model(url, **kwargs):
        payload = json.loads(kwargs['body']); sent.append(payload)
        assert url == configured.model_url
        assert 'C, E, G' in payload['messages'][1]['content']
        return {'choices': [{'message': {'content': '{"message":"Play C, then E and G slowly, one note at a time."}'}}]}
    monkeypatch.setattr('emporio.research.request_json', model)
    coach = MusicCoach(configured)
    response = coach.explain(root=0, quality='major', neural=True)
    assert response['model_state'] == 'responded' and response['model'] == 'test-model'
    assert response['mode'] == 'rules_with_model_interpretation'
    assert len(sent) == 1 and set(json.loads(sent[0]['messages'][1]['content'])) == {'facts'}


@pytest.mark.parametrize('failure', ['bad_json', 'transport', 'shape'])
def test_model_failure_preserves_checked_rules(settings, monkeypatch, failure):
    configured = replace(settings, provider='openai_compatible', model_url='http://localhost:8081/v1/chat/completions', model='test-model')
    def model(*args, **kwargs):
        if failure == 'transport':
            raise OSError('unavailable')
        return {'choices': [{'message': {'content': 'not JSON' if failure == 'bad_json' else '{}'}}]}
    monkeypatch.setattr('emporio.research.request_json', model)
    result = MusicCoach(configured).explain(midi=69, hz=440, neural=True)
    assert result['model_state'] == 'unavailable' and result['facts'] and result['model_message'] is None
