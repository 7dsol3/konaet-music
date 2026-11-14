"use strict";
// Shared, local appearance controls. The original glass room is the default.
(() => {
  const body = document.body;
  const triggers = [...document.querySelectorAll("[data-glass-open]")];
  if (!triggers.length) return;
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  const originalThemeColor = themeMeta?.getAttribute("content") || "#263b3a";

  const KEY = "konaet-liquid-glass-v1";
  const SCHEMA = "konaet.liquid-glass.v1";
  const DEFAULTS = Object.freeze({palette:"original", accent:"", tint:"", opacity:68, blur:28, radius:30, photo:true, contrast:false, motion:false});
  const THEMES = Object.freeze({
    original:{name:"Original", room:"#263b3a", tint:"#243133", accent:"#d1e7be"},
    amber:{name:"Amber", room:"#3e3030", tint:"#392d2c", accent:"#ffd1a8"},
    cobalt:{name:"Cobalt", room:"#20384b", tint:"#1d3348", accent:"#a9dbff"},
    violet:{name:"Violet", room:"#342d45", tint:"#302942", accent:"#ddc0ff"},
    mono:{name:"Mono", room:"#27302f", tint:"#202828", accent:"#f1f1ea"}
  });
  const hasOwn = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  const validHex = value => typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value) ? value.toLowerCase() : "";
  const bounded = (value, low, high, fallback) => Number.isFinite(Number(value)) ? Math.min(high, Math.max(low, Math.round(Number(value)))) : fallback;
  function clean(input) {
    const source = input && typeof input === "object" ? input : {};
    return {
      palette:hasOwn(THEMES, source.palette) ? source.palette : DEFAULTS.palette,
      accent:validHex(source.accent), tint:validHex(source.tint),
      opacity:bounded(source.opacity, 0, 100, DEFAULTS.opacity),
      blur:bounded(source.blur, 0, 40, DEFAULTS.blur),
      radius:bounded(source.radius, 12, 42, DEFAULTS.radius),
      photo:source.photo !== false, contrast:source.contrast === true, motion:source.motion === true
    };
  }
  function read() {
    try { return clean(JSON.parse(localStorage.getItem(KEY) || "null")); }
    catch { return {...DEFAULTS}; }
  }
  function inkOn(hex) {
    const rgb = [1,3,5].map(index => parseInt(hex.slice(index,index+2),16) / 255);
    const light = rgb.map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
    return light[0] * .2126 + light[1] * .7152 + light[2] * .0722 > .42 ? "#203a31" : "#ffffff";
  }

  const dialog = document.createElement("dialog");
  dialog.id = "glass-settings-dialog";
  dialog.className = "glass-settings-dialog";
  dialog.setAttribute("aria-labelledby", "glass-settings-title");
  dialog.innerHTML = `
    <div class="glass-settings-head"><div><small>KONAET / LIQUID GLASS</small><h2 id="glass-settings-title">Make the room yours.</h2><p>The original glass design stays one click away. Changes are saved in this browser and shared with Sound Lab.</p></div><button class="glass-settings-close" type="button" aria-label="Close appearance settings">×</button></div>
    <div class="glass-settings-body">
      <div class="glass-settings-preview" aria-hidden="true"><span>LIVE MATERIAL PREVIEW / KONAET</span><strong>Sound through <em>glass.</em></strong></div>
      <section class="glass-settings-section" aria-labelledby="glass-palette-title"><small>01 / COLOR</small><h3 id="glass-palette-title">Choose a palette</h3><div class="glass-palette-grid" role="group" aria-label="Color palette">
        <button type="button" data-glass-palette="original" aria-pressed="false"><i></i><span>Original</span></button>
        <button type="button" data-glass-palette="amber" aria-pressed="false"><i></i><span>Amber</span></button>
        <button type="button" data-glass-palette="cobalt" aria-pressed="false"><i></i><span>Cobalt</span></button>
        <button type="button" data-glass-palette="violet" aria-pressed="false"><i></i><span>Violet</span></button>
        <button type="button" data-glass-palette="mono" aria-pressed="false"><i></i><span>Mono</span></button>
      </div><div class="glass-color-grid"><label><span><strong>Accent</strong><small>Light and actions</small></span><input id="glass-accent" type="color" aria-label="Accent color"></label><label><span><strong>Glass tint</strong><small>Panels and frame</small></span><input id="glass-tint" type="color" aria-label="Glass tint color"></label></div></section>
      <section class="glass-settings-section" aria-labelledby="glass-material-title"><small>02 / GLASS</small><h3 id="glass-material-title">Tune the material</h3><div class="glass-range-list">
        <label><span><strong>Transparency</strong><output id="glass-opacity-value"></output></span><input id="glass-opacity" type="range" min="0" max="100" step="1"></label>
        <label><span><strong>Background blur</strong><output id="glass-blur-value"></output></span><input id="glass-blur" type="range" min="0" max="40" step="1"></label>
        <label><span><strong>Corner shape</strong><output id="glass-radius-value"></output></span><input id="glass-radius" type="range" min="12" max="42" step="1"></label>
      </div></section>
      <section class="glass-settings-section" aria-labelledby="glass-comfort-title"><small>03 / COMFORT</small><h3 id="glass-comfort-title">See it your way</h3><div class="glass-switches">
        <label><span><strong>Room background</strong><small>Show the studio behind the glass</small></span><input id="glass-photo" type="checkbox"></label>
        <label><span><strong>Sharper outlines</strong><small>Increase separation between panels</small></span><input id="glass-contrast" type="checkbox"></label>
        <label><span><strong>Reduce motion</strong><small>Quiet transitions and hover movement</small></span><input id="glass-motion" type="checkbox"></label>
      </div></section>
      <section class="glass-settings-section glass-settings-actions" aria-label="Save or restore settings"><button id="glass-export" type="button">Export look ↓</button><button id="glass-import" type="button">Import look ↑</button><input id="glass-file" type="file" accept="application/json,.json" hidden><button id="glass-reset" type="button">Restore original</button><p id="glass-status" role="status" aria-live="polite">Changes save automatically on this device.</p></section>
    </div>`;
  body.append(dialog);
  const q = selector => dialog.querySelector(selector);
  const inputs = {
    accent:q("#glass-accent"), tint:q("#glass-tint"), opacity:q("#glass-opacity"),
    blur:q("#glass-blur"), radius:q("#glass-radius"), photo:q("#glass-photo"),
    contrast:q("#glass-contrast"), motion:q("#glass-motion")
  };
  let settings = read();
  let opener = null;
  const prefersReducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches || false;
  function sync() {
    const theme = THEMES[settings.palette];
    q(".glass-palette-grid").querySelectorAll("button").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.glassPalette === settings.palette)));
    inputs.accent.value = settings.accent || theme.accent;
    inputs.tint.value = settings.tint || theme.tint;
    for (const name of ["opacity","blur","radius"]) inputs[name].value = settings[name];
    for (const name of ["photo","contrast","motion"]) inputs[name].checked = settings[name];
    q("#glass-opacity-value").value = settings.opacity + "%";
    q("#glass-blur-value").value = settings.blur + " px";
    q("#glass-radius-value").value = settings.radius + " px";
  }
  function apply(save = true) {
    const theme = THEMES[settings.palette];
    const accent = settings.accent || theme.accent;
    const materialChanged = settings.palette !== "original" || !!settings.tint || settings.opacity !== DEFAULTS.opacity || settings.blur !== DEFAULTS.blur || settings.radius !== DEFAULTS.radius;
    const accentChanged = settings.palette !== "original" || !!settings.accent;
    body.dataset.glassMaterial = String(materialChanged);
    body.dataset.glassAccent = String(accentChanged);
    body.style.setProperty("--kg-room", theme.room);
    body.style.setProperty("--kg-tint", settings.tint || theme.tint);
    body.style.setProperty("--kg-accent", accent);
    body.style.setProperty("--kg-accent-ink", inkOn(accent));
    body.style.setProperty("--kg-opacity", settings.opacity + "%");
    body.style.setProperty("--kg-blur", settings.blur + "px");
    body.style.setProperty("--kg-radius", settings.radius + "px");
    body.classList.toggle("glass-no-photo", !settings.photo);
    body.classList.toggle("glass-high-contrast", settings.contrast);
    body.classList.toggle("glass-reduce-motion", settings.motion || prefersReducedMotion);
    themeMeta?.setAttribute("content", materialChanged ? theme.room : originalThemeColor);
    sync();
    if (save) { try { localStorage.setItem(KEY, JSON.stringify(settings)); } catch { /* Controls still work for this tab. */ } }
  }
  function update(name, value) { settings[name] = value; apply(); q("#glass-status").textContent = "Saved on this device."; }
  triggers.forEach(button => button.addEventListener("click", () => {
    opener = button;
    document.querySelectorAll("dialog[open]").forEach(other => { if (other !== dialog) other.close(); });
    dialog.showModal();
  }));
  q(".glass-settings-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener("close", () => opener?.focus());
  q(".glass-palette-grid").addEventListener("click", event => {
    const button = event.target.closest("[data-glass-palette]");
    if (!button) return;
    settings = {...settings, palette:button.dataset.glassPalette, accent:"", tint:""};
    apply(); q("#glass-status").textContent = THEMES[settings.palette].name + " palette applied.";
  });
  for (const name of ["accent","tint","opacity","blur","radius"]) inputs[name].addEventListener("input", event => update(name, name === "accent" || name === "tint" ? validHex(event.target.value) : Number(event.target.value)));
  for (const name of ["photo","contrast","motion"]) inputs[name].addEventListener("change", event => update(name, event.target.checked));
  q("#glass-reset").addEventListener("click", () => { settings = {...DEFAULTS}; apply(); q("#glass-status").textContent = "Original glass room restored."; });
  q("#glass-export").addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify({schema:SCHEMA,...settings},null,2)],{type:"application/json"}));
    const link = document.createElement("a"); link.href = url; link.download = "konaet-glass-look.json"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    q("#glass-status").textContent = "Appearance file downloaded.";
  });
  q("#glass-import").addEventListener("click", () => q("#glass-file").click());
  q("#glass-file").addEventListener("change", async event => {
    const file = event.target.files?.[0]; event.target.value = "";
    if (!file) return;
    try {
      if (file.size > 16384) throw new Error("The file is too large.");
      const data = JSON.parse(await file.text());
      if (data?.schema !== SCHEMA) throw new Error("This is not a KONAET glass look.");
      settings = clean(data); apply(); q("#glass-status").textContent = "Look imported and saved.";
    } catch (error) { q("#glass-status").textContent = error.message || "Could not read this file."; }
  });
  window.addEventListener("storage", event => { if (event.key === KEY) { settings = read(); apply(false); } });
  apply(false);
})();
