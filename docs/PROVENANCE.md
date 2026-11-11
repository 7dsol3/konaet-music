# Component provenance

## Separate product evolution

KONAET Music 2.0 continues the original submitted source at
`7dsol3/emporio-musica-ai-agent`, revision
`aefc6f54191eb00c52d7a9f8df85c1c3a201c5b6`, in a separate repository.
That submitted default branch was not changed for this work. The Python service
is extended with commerce and guardrails; the English interface, glass layer,
vector instrument illustrations and checkout composition are new project code.
Segno encodes the QR standard; its authorship is not attributed to KONAET.

The old screenshot/UI report files are historical records from the original
case. New event/packaging tests are identified separately and do not claim a
new browser visual check.

## Reused Konaet source

- Source repository: `https://github.com/7dsolv/Konaet-IA`.
- Observed source revision: `2881c97f421e14731afb4f3405dcd2b580074a23` (local checkout).
- Original path: `konaet/knowledge.py`.
- Frozen destination: `emporio/vendor/konaet_knowledge.py`.
- SHA-256 of the frozen source:
  `a22588b3e554b08278441361fe27bc5cedbefe3b3200d26009e201582442611d`.
- Adaptation: the module is copied unchanged. Application-specific query
  expansion, PDF normalization, version guards and summaries live outside it.
- License: original Konaet Research and Commercial License 1.0, retained in full
  at `emporio/vendor/KONAET_LICENSE`. The evaluation use is noncommercial.

The `teste codex/arc3_causal` and `anti-cheater` directories were inspected at
the user's request. Their game-control semantics and telemetry models do not
serve conversational instrument-store questions. They informed the separation
between proposed actions, authoritative observations and evidence receipts;
their code/assets/models are not vendored here. The audit implementation is
specific to this application and uses atomic SQLite transactions.

## Local external model

- Publisher/repository: `Qwen/Qwen3-0.6B-GGUF`.
- Revision: `23749fefcc72300e3a2ad315e1317431b06b590a`.
- File: `Qwen3-0.6B-Q8_0.gguf` (639,446,688 bytes).
- SHA-256: `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
- License: Apache-2.0, as stated by the [official model repository](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF).
- Scope: inference only; no fine-tuning, distillation or weight merge.

Inference server: official `ggml-org/llama.cpp`, pinned Windows CPU build `b12024`.
Archive SHA-256:
`a8a1bc0167c594c377255e54aab617b288a38e09efb50f39ac5bd087e4398f72`.
The download helper records these identities in `var/model/manifest.json` and
requires checksum verification. Binary/model artifacts are not Git content.

The [llama.cpp function-calling documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md)
describes the native protocol and Jinja configuration. The application verifies
actual returned calls rather than assuming that a provider obeys a prompt flag.

