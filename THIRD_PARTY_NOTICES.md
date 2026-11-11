# Attribution and licensing

The project-authored Empório and KONAET Music application files are distributed under the MIT license in
`LICENSE`. That grant does not relicense the following materials.

| Component | Origin and terms | Use |
| --- | --- | --- |
| Frozen `emporio/vendor/konaet_knowledge.py` | Adilson Oliveira / Konaet, Konaet Research and Commercial License 1.0; full text in `emporio/vendor/KONAET_LICENSE` | SQLite FTS5 policy indexing and retrieval; noncommercial evaluation is permitted |
| Frozen `emporio/vendor/sovereign_receipt.py` | `7dsol3/konaet-sovereign-spec`, commit `3ccf7a96b701b3b17e58694ef227af4e83cb7d22`, `polyglot/python/receipt.py`; ISC, full text in `emporio/vendor/SOVEREIGN_LICENSE` | Exact commitment frame compatibility; no validator or wallet runtime copied |
| Supplied CSVs and `políticas_da_loja.pdf` | Fictional Artefact technical-case inputs; no independent ownership or general redistribution license claimed | Evaluation fixtures, preserved unchanged |
| Qwen3-0.6B-GGUF, Q8_0 | [Qwen model repository](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF), Apache-2.0 | Optional external language-model inference; weights are downloaded locally, not committed |
| llama.cpp | [Official project](https://github.com/ggml-org/llama.cpp), MIT | Optional local inference server; binaries are downloaded locally, not committed |
| FastAPI | MIT | HTTP API and validation integration |
| Starlette | BSD-3-Clause | ASGI implementation beneath FastAPI |
| Pydantic | MIT | Typed input and tool argument validation |
| Uvicorn | BSD-3-Clause | Local ASGI server |
| pypdf | BSD-3-Clause | Text extraction from the supplied manual |
| Segno | BSD-3-Clause | Standard QR matrix encoding; the renderer and checkout binding are project code |
| Pillow | MIT-CMU | Development-only raster checks |
| ZXing-C++ | Apache-2.0 | Independent development-only QR decoding |
| Happy DOM | MIT | Development-only DOM event tests; not browser rendering |
| Python / SQLite | PSF / public domain | Application runtime and database |
| pytest / HTTPX | MIT / BSD-3-Clause | Automated development checks |
| Playwright | Apache-2.0 | Optional isolated-browser development checks |
| ReportLab / PyMuPDF | BSD / AGPL-3.0 or commercial terms | Local documentation build and PDF rendering only; not application runtime dependencies |

The interface uses system fonts, CSS, and project-authored SVGs. It makes no CDN
requests. The Sentinel anti-cheat and ARC research runtimes were inspected for
architectural context; their models, assets, game logic and proprietary source
were not incorporated into this service. The provenance record identifies the
one frozen source component that is actually used.

Sound Lab DSP, generated study/graphics and H-01 RTL are project-authored MIT
code. Equal temperament, phase accumulation, Fourier analysis and I²S are
established methods/protocols, not claimed as new mathematical inventions.
The I²S timing implementation references NXP UM11732. Icarus Verilog and Yosys
are development-only validation tools; their binaries are not embedded in the
application distribution. `FareedKhan-dev/kimi-k3-in-c` was inspected as an
external comparison reference; none of its source, fixtures or weights is included.

Konaet is the application/orchestration identity here. Qwen remains named as an
external model; it is not presented as a Konaet-trained neural model. No neural
training, weight merging or distillation was performed for this prototype.
