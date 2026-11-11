"""Bounded audio-core reference and music coaching. No audio capture or storage.

The integer model specifies audio_dds.sv and audio_meter.sv. The browser's
pitch/chroma estimates are a separate, heuristic signal-processing path.
"""
from __future__ import annotations

import hashlib
import json
import math
import threading
from pathlib import Path

NOTES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
QUALITIES = {"major": (0, 4, 7), "minor": (0, 3, 7), "sus2": (0, 2, 7),
             "sus4": (0, 5, 7), "diminished": (0, 3, 6)}
RATE = 48_000
GATEWARE = Path(__file__).parent / "gateware"


def note_name(midi):
    return NOTES[midi % 12] + str(midi // 12 - 1)


def triangle(phase):
    address = (phase >> 16) & 0xFFFF
    return 2 * address - 32768 if address < 32768 else 98303 - 2 * address


def dds_trace(vectors):
    """One row per clock: (reset, sample_enable, mute, voice_mask, three steps).

    Exactly the registered output contract; disabled cycles hold the sample.
    Muting is digital zero, not an analog amplifier protection claim.
    """
    phases = [0x40000000] * 3
    sample = 0
    trace = []
    for reset, enable, mute, mask, steps in vectors:
        valid = False
        if reset:
            phases, sample = [0x40000000] * 3, 0
        elif enable:
            valid = True
            sample = 0 if mute else sum(triangle(p) for i, p in enumerate(phases) if mask & (1 << i)) >> 3
            phases = [0x40000000] * 3 if mute else [(p + step) & 0xFFFFFFFF for p, step in zip(phases, steps)]
        trace.append({"valid": valid, "sample": sample})
    return trace


def meter_trace(vectors):
    """64 accepted PCM16 samples per block; reset discards partial blocks."""
    count = peak = energy = clips = 0
    last = {"peak": 0, "energy": 0, "clipped": 0}
    trace = []
    for reset, valid, sample in vectors:
        if type(sample) is not int or not -32768 <= sample <= 32767:
            raise ValueError("Expected signed PCM16")
        done = False
        if reset:
            count = peak = energy = clips = 0
            last = {"peak": 0, "energy": 0, "clipped": 0}
        elif valid:
            peak = max(peak, abs(sample))
            energy += sample * sample
            clips += int(abs(sample) >= 32700)
            count += 1
            if count == 64:
                last = {"peak": peak, "energy": energy, "clipped": clips}
                done = True
                count = peak = energy = clips = 0
        trace.append({"valid": done, **last})
    return trace


def source_hashes():
    files = {"python_reference": Path(__file__), **{name: GATEWARE / (name + ".sv") for name in
             ("audio_dds", "audio_meter", "audio_i2s_tx", "audio_i2s_rx", "konaet_audio_core", "audio_core_tb")}}
    return {name: hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name, path in files.items()}


def validation():
    path = GATEWARE / "audio-validation.json"
    if path.is_file():
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("status") == "PASS" and report.get("sources") == source_hashes():
            return {"status": "source_matched_record", "clock_vectors": report["clock_vectors"],
                    "i2s_frames": report["i2s_frames"], "simulator": report["simulator"],
                    "synthesis": report.get("synthesis", "not_run"), "physical_device_tested": False}
    return {"status": "record_unavailable", "physical_device_tested": False}


def program(root=0, quality="major", octave=3):
    if type(root) is not int or not 0 <= root < 12 or quality not in QUALITIES or type(octave) is not int or not 2 <= octave <= 5:
        raise ValueError("Choose a root, supported triad and octave 2–5")
    notes = [(octave + 1) * 12 + root + interval for interval in QUALITIES[quality]]
    steps = [round(440 * 2 ** ((note - 69) / 12) * 2**32 / RATE) for note in notes]
    rows = dds_trace([(False, True, False, 7, steps)] * 512)
    pcm = [row["sample"] for row in rows]
    blocks = [row for row in meter_trace([(False, True, sample) for sample in pcm]) if row["valid"]]
    return {"schema": "konaet.audio-program.v1", "mode": "python_reference", "core": "KONAET H-01",
            "physical_device_connected": False, "sample_rate": RATE, "master_clock_hz": RATE * 256,
            "waveform": "three triangle oscillators; sum / 8, signed arithmetic shift",
            "root": root, "quality": quality, "octave": octave, "midi": notes, "notes": list(map(note_name, notes)),
            "phase_steps": steps, "voice_mask": 7, "preview_pcm16": pcm, "meter_blocks": blocks,
            "rtl_parameters": "\n".join(f"localparam logic [31:0] STEP_{i} = 32'd{step};" for i, step in enumerate(steps)),
            "validation": validation(), "notice": "The page runs a reference model. No FPGA or DAC is connected to this server."}


class MusicCoach:
    def __init__(self, settings):
        self.settings = settings
        self.slots = threading.BoundedSemaphore(1)

    def explain(self, *, midi=None, hz=None, reference=440.0, root=None, quality=None, neural=False):
        facts = []
        if root is not None and quality is not None:
            intervals = QUALITIES[quality]
            notes = [NOTES[(root + n) % 12] for n in intervals]
            facts.append(f"The browser matched {NOTES[root]} {quality}: " + ", ".join(notes) + ".")
            facts.append("This is a triad-template estimate, not a song identification or a calibrated probability.")
            practice = "Play the root alone, then add the other two notes. Listen for a stable balance; try the same shape one octave higher."
        elif midi is not None and hz is not None:
            target = reference * 2 ** ((midi - 69) / 12)
            cents = 1200 * math.log2(hz / target)
            if abs(cents) > 50.01:
                raise ValueError("Frequency and nearest MIDI note are inconsistent")
            facts.append(f"The browser estimated {note_name(midi)} at {hz:.2f} Hz; target {target:.2f} Hz at A4 = {reference:g} Hz.")
            facts.append(f"Tuning offset: {cents:+.1f} cents. Recheck a single sustained note in a quiet room.")
            practice = "Use small tuning adjustments and recheck after each one. A periodic signal does not establish the instrument or performer."
        else:
            raise ValueError("Provide a complete pitch pair or a complete chord pair")
        result = {"mode": "checked_music_rules", "facts": facts, "practice": practice,
                  "input_origin": "unverified_browser_estimate", "audio_uploaded": False, "model_message": None,
                  "notice": "Signal estimates and generated coaching can be wrong. No clinical or hearing assessment is performed."}
        if neural:
            if self.settings.provider != "openai_compatible":
                result["model_state"] = "not_configured"
                return result
            if not self.slots.acquire(blocking=False):
                result["model_state"] = "busy"
                return result
            try:
                from .planner import ModelPlanner
                from .research import request_json
                ModelPlanner(self.settings)
                body = json.dumps({"model": self.settings.model, "temperature": 0, "max_tokens": 200,
                                   "response_format": {"type": "json_object"}, "chat_template_kwargs": {"enable_thinking": False},
                                   "messages": [{"role": "system", "content": "You are a music practice coach. Return JSON with a message string in English, at most 80 words. Suggest one simple exercise using only the provided music facts. Do not identify a song, invent measurements, claim device access, or give medical advice."},
                                                {"role": "user", "content": json.dumps({"facts": facts})}]}).encode()
                headers = {"Content-Type": "application/json"}
                if self.settings.model_key:
                    headers["Authorization"] = "Bearer " + self.settings.model_key
                payload = request_json(self.settings.model_url, timeout=min(20, self.settings.model_timeout), headers=headers, body=body)
                message = json.loads(payload["choices"][0]["message"]["content"])["message"]
                if not isinstance(message, str) or not 10 <= len(message) <= 1400:
                    raise ValueError("Invalid coach output")
                result.update(mode="rules_with_model_interpretation", model_state="responded", model_message=message,
                              model=self.settings.model, provider=self.settings.provider)
            except (ValueError, KeyError, IndexError, TypeError, OSError, TimeoutError):
                result["model_state"] = "unavailable"
            finally:
                self.slots.release()
        return result
