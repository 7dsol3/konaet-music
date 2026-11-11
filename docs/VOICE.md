# Voice and responsive app contract

The English UI accepts typed commands and optional browser speech recognition.
Clicking **Ask KONAET** opens the assistant; it does not activate the microphone.
Only clicking the microphone starts capture. Recognition ends after the utterance
or an explicit stop, and closing the assistant aborts capture. The transcript is
a draft. It is never sent to the agent automatically.

SpeechRecognition is not uniformly supported. Some implementations use a remote
browser speech service. Permission, availability, accent/noise quality and
network behavior depend on the browser. The UI discloses that boundary and keeps
typing available. Do not present this implementation as verified offline ASR.
[MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition).

Reading answers uses optional browser speech synthesis, starts only when the
customer selects **Read replies aloud**, and stops when that setting is disabled
or the assistant closes. Installed English voices vary by device. No voice
cloning, wake-word daemon, always-on recording or custom audio model is shipped.

The same explicit customer commands can display a comparison, add an already
displayed product to the bag, or open checkout review. A language-model tool call
cannot charge or alter a bank account. Checkout still requires a separate
customer action. Corrections to voice text use the ordinary text editor.

## PWA and performance

The manifest declares standalone display and an English application name.
On supporting browsers an install control appears after `beforeinstallprompt`;
other browsers may provide Add to Home Screen in their menus. That event is not
universally supported. [MDN install event](https://developer.mozilla.org/en-US/docs/Web/API/BeforeInstallPromptEvent).

The service worker caches only a fixed allowlist of public UI files. No API,
chat, identity response, checkout preview, QR or payment state is cached or queued.
Offline loading can show the public shell, with unavailable data reported
explicitly. It cannot manufacture current stock or complete an offline checkout.

The glass treatment uses gradients and static original SVGs. Backdrop blur is
restricted to the header and comparison tray, with opaque fallbacks. Product
cards use ordinary translucent backgrounds. There is no continuous rendering
loop; transitions use short transforms, and reduced-motion/transparency styles
disable or simplify effects.

`scripts/verify_frontend.py` enforces 150 KB raw / 45 KB compressed source budgets
for the active HTML/CSS/JS/SVG/PWA files. This measures source transfer potential,
not real first-load network traffic, frame rate or battery consumption.

`tests/ui/interface.test.mjs` exercises six event contracts with Happy DOM and
controlled API/browser doubles. Those tests verify opt-in capture, draft-only
transcription, typed fallback, catalog filters, bag/quote behavior and text-safe
rendering. They do not perform actual speech recognition or pixel layout.

Native app and browser-control bridges were unavailable during this change.
The following device acceptance remains open: keyboard/screen-reader traversal,
375/390/768/1440-pixel layouts, contrast on glass, zoom, safe-area keyboards,
real iOS/Android installation, permission denial, noisy-room speech, offline
transitions and responsiveness on a modest device. No iPhone comparison was measured.
