"use strict";
// Loaded only by the standalone build. The Python application keeps its API.
(() => {
  const base = new URL("../", document.currentScript.src);
  let storage;
  try { storage = window.localStorage; } catch { storage = {getItem(){return null;},setItem(){throw Error("Storage unavailable");}}; }
  let runtime;
  const ready = Promise.all([
    import(new URL("browser-runtime.mjs", document.currentScript.src).href),
    fetch(new URL("catalog.json", base)).then(r => { if (!r.ok) throw Error("The bundled catalog could not load. Refresh this page."); return r.json(); })
  ]).then(([module, catalog]) => runtime = module.createRuntime({catalog, base, storage, crypto, fetch:window.fetch.bind(window), qrcode:window.qrcode}));
  window.KonaetRuntime = {
    async request(path, options) { return (await ready).request(path, options); },
    codeURL(quote, theme) { return runtime.codeURL(quote, theme); },
    checkoutId() { return runtime?.checkoutId(); }
  };
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-browser-notice]").forEach(n => n.textContent = "GitHub / browser demo · no real charges · data stays on this device");
  }, {once:true});
})();
