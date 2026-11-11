# External runtimes: comparison before a ranking

The user-provided reference is
[`FareedKhan-dev/kimi-k3-in-c`](https://github.com/FareedKhan-dev/kimi-k3-in-c/tree/81bb6c23ccee2154bc35cad922588ab66494a9a9),
reviewed at `81bb6c23ccee2154bc35cad922588ab66494a9a9` on 2026-11-11.
Its README describes a C99 inference engine with streamed model weights and
weightless reference tests. The stated checkpoint storage is approximately
1.56 TB; the low-RAM setting does not remove that disk requirement. Its documented
limitations include tool use and HTTP serving. Source is Apache-2.0, while model
weights have separate terms. Those are upstream descriptions, not measurements
reproduced by this project. No source or weights were copied into KONAET Music.

KONAET Music is an application with authoritative commerce tools, browser audio
DSP, a digital hardware core and an optional external inference provider. It does
not implement an equivalent large-model engine. Feature counts, a tiny-model
download, synthetic audio tests or faster deterministic rules cannot establish
superiority over a different model/runtime.

## Paired evaluation protocol

1. Fix both source revisions, model/checkpoint hashes, tokenizers, quantization,
   sampling settings and licenses. Record CPU, RAM, storage and OS independently.
2. Use the same authorized data and a frozen, externally reviewed task set.
   Separate general text, tool-use correctness, private-data denial, musical
   perception and hardware behavior; report each task's applicable metric.
3. Measure cold start, warm p50/p95 latency, token throughput, process peak RSS,
   disk bytes, timeout/error/fallback rate and answer quality. State what each
   measurement includes. Report unsuccessful attempts too.
4. Keep direct-model quality separate from application tools and fallback rules.
   A successful deterministic fallback is application success and model failure
   or abstention, not evidence of correct model planning.
5. Publish prompts, authorized ground truth, raw per-case records, repetitions
   and analysis scripts. Independent replication is needed for a ranking.

No Kimi checkpoint was downloaded or executed here. Its CLI would need a
separately tested serving/tool bridge before the site's existing compatible-HTTP
adapter could use it. No Kimi-vs-KONAET result, speedup or accuracy percentage
is claimed. The current added contribution is functioning audio software and
verified digital logic, with the evidence scoped to those implementations.
