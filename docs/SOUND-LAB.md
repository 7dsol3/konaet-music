# Sound Lab 2.2

Open `/sound-lab` on the running application. The page is linked from the music
desk and the GitHub Pages entrance. It loads its own assets only when visited;
the existing home-page transfer budget stays below 150 kB raw / 45 kB gzip.
The separate Sound Lab budget is 70 kB raw / 22 kB gzip. These are source-byte
budgets, not measured phone performance.

## Working paths

| Input | Processing | Output |
| --- | --- | --- |
| Named key / triad | Web Audio, equal temperament, a short sine envelope | Audible reference, local waveform and estimates |
| Original four-chord study | C–Am–F–G, project-authored synthesized voicing | Playback and mono PCM16 WAV export |
| Explicit microphone start | Native permission, no speaker monitoring | Local tuning and triad-template estimates |
| Local file | Browser media playback, at most 8 MiB and 90 seconds | Playback, progress and local analysis; no upload |
| Latest valid pitch / chord | Strict typed API, deterministic music rules | Note relationships, tuning offset, a practice exercise |
| Explicit model option | Only validated music facts to the configured endpoint | A named, unverified model suggestion alongside the rules |
| Chord program | Integer Python reference and browser recurrence | Three phase increments, reference PCM, block metrics and `.svh` constants |

An 8-beat synthesized metronome loops at 40–200 BPM. Tap tempo uses the median
of recent valid intervals. Audio starts only after an explicit action. Playback
level defaults low. Stop releases active microphone tracks. Hidden-page and
page-exit handlers stop audio, invalidate pending microphone permission results,
cancel API requests and release local object URLs. No recording is saved.

## Mathematics and honest uncertainty

Equal temperament uses `f(m) = A4 × 2^((m−69)/12)`; tuning deviation is
`1200 log2(f_measured / f_target)` cents. The tuner uses a cumulative normalized
difference (YIN-style) estimator. It abstains on quiet/nonperiodic frames and
supports fundamentals from approximately 32 to 1,300 Hz. A periodicity score
describes the frame; it is not an instrument classifier or calibrated confidence.

A Hann-windowed radix-2 FFT contributes spectral peaks to twelve pitch classes.
Triad templates cover major, minor, sus2, sus4 and diminished shapes. A result
needs all three pitch classes, sufficient coverage and a margin over the next
template. Equivalent suspended inversions can be ambiguous and are withheld.
The score is a template similarity, not a probability. Full songs, noisy rooms,
overtones, inversions and multiple simultaneous instruments can fail.

Browser analysis reads at most five frames per second, each 16,384 native samples.
A low-pass branch feeds the analyzer; playback follows its separate gain path.
The pure DSP reduces a frame to at most 4,096 analysis samples. This is an
educational estimator, not a studio-grade anti-aliased resampler or transcription
system. No song/artist identification, source separation, speech transcription,
learned music embeddings or hearing assessment is implemented.

## Evidence

`tests/sound-dsp.test.mjs` generates independent sinusoidal fixtures: seven pitches
at three sample rates, slight detuning, silence, DC, deterministic noise, 24 clean
major/minor triads, ambiguity rejection, fractional study lengths, PCM headers,
integer recurrence and a measured Node timing sample. Passing synthetic fixtures
does not establish accuracy on real recordings. `tests/ui/sound-lab.test.mjs`
executes real handlers with DOM/audio doubles; those tests verify opt-in/lifecycle,
typed requests, file bounds, parameter freshness and plain-text rendering.

`tests/test_audio.py` checks signed boundaries, block-reset behavior, phase
increments, strict API schemas, checked coaching and model-failure fallback.
The full Python, UI, QR, packaging and RTL suites remain required.

No browser rendering, physical microphone/speaker playback, device PWA install,
accessibility certification or mobile latency measurement is asserted by these
source/DOM tests. The runtime can serve the page while these device checks remain
open. See the release's validation record for the exact revision and run links.

Implementation references: [Web Audio specification](https://webaudio.github.io/web-audio-api/),
[native microphone permissions](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia),
and [NXP I²S specification](https://www.nxp.com/docs/en/user-manual/UM11732.pdf).
