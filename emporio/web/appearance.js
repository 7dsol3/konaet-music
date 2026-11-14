"use strict";
// One local appearance profile for the music desk and Sound Lab.
(() => {
  const body = document.body;
  const openButton = document.getElementById("appearance-open");
  if (!openButton || !body.matches(".studio-shell, .sound-shell")) return;

  const KEY = "konaet-appearance-v1";
  const SCHEMA = "konaet.appearance.v1";
  const DEFAULTS = Object.freeze({palette:"atelier", finish:"instrument", accent:"", surface:"", radius:8, opacity:90, blur:18, scale:100, contrast:false, motion:false, photo:false});
  const PALETTES = Object.freeze({
    atelier:{name:"Atelier", background:"#e9e4db", surface:"#f4f0e8", panel:"#dcd6ca", ink:"#202925", muted:"#5c6862", accent:"#d95638", edge:"#29383140", stage:"#172320"},
    moss:   {name:"Moss",   background:"#263c3a", surface:"#263a3b", panel:"#304849", ink:"#f2f6ec", muted:"#c5d4c8", accent:"#d8e9bd", edge:"#ffffff42", stage:"#111d1c"},
    ember:  {name:"Ember",  background:"#302c2c", surface:"#302d30", panel:"#463a3b", ink:"#fff3ea", muted:"#e1c9bf", accent:"#ffc09b", edge:"#ffffff42", stage:"#171417"},
    cobalt: {name:"Cobalt", background:"#1c3044", surface:"#1b3043", panel:"#294560", ink:"#eff6ff", muted:"#c1d5e6", accent:"#a8dcff", edge:"#ffffff45", stage:"#0d1d2b"},
    iris:   {name:"Iris",   background:"#2c2841", surface:"#302c48", panel:"#443d60", ink:"#f6f2ff", muted:"#d7cce8", accent:"#dac0ff", edge:"#ffffff45", stage:"#191727"},
    paper:  {name:"Paper",  background:"#e8e2d6", surface:"#f5f0e7", panel:"#ece6db", ink:"#203030", muted:"#52605d", accent:"#a64e37", edge:"#273b3540", stage:"#182321"}
  });
  const hasOwn = (object, name) => Object.prototype.hasOwnProperty.call(object, name);
  const hex = value => typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value) ? value.toLowerCase() : "";
  const clamp = (value, min, max, fallback) => Number.isFinite(Number(value)) ? Math.min(max, Math.max(min, Math.round(Number(value)))) : fallback;
  const prefersReducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches || false;
  function clean(input) {
    const source = input && typeof input === "object" ? input : {};
    return {
      palette:hasOwn(PALETTES, source.palette) ? source.palette : DEFAULTS.palette,
      finish:["instrument", "glass", "soft"].includes(source.finish) ? source.finish : DEFAULTS.finish,
      accent:hex(source.accent), surface:hex(source.surface),
      radius:clamp(source.radius, 4, 24, DEFAULTS.radius),
      opacity:clamp(source.opacity, 0, 100, DEFAULTS.opacity),
      blur:clamp(source.blur, 0, 36, DEFAULTS.blur),
      scale:clamp(source.scale, 90, 120, DEFAULTS.scale),
      contrast:source.contrast === true, motion:source.motion === true,
      photo:source.photo === true
    };
  }
  function read() {
    try { return clean(JSON.parse(localStorage.getItem(KEY) || "null")); }
    catch { return {...DEFAULTS}; }
  }
  let settings = read();
  const dialog = document.createElement("dialog");
  dialog.id = "appearance-dialog";
  dialog.className = "appearance-dialog";
  dialog.setAttribute("aria-labelledby", "appearance-title");
  dialog.innerHTML = `
    <div class="appearance-heading">
      <div><span class="appearance-overline">KONAET / YOUR STUDIO</span><h2 id="appearance-title">Set the mood<span>.</span></h2><p>A personal look for the music desk and Sound Lab. Saved in this browser.</p></div>
      <button type="button" class="appearance-close" aria-label="Close appearance settings">×</button>
    </div>
    <div class="appearance-body">
      <div class="appearance-preview" aria-hidden="true"><div><span>K / M</span><span>STUDIO / VISUAL 01</span></div><strong>Sound has<br><em>a shape.</em></strong><small>COLOR · TYPE · MATERIAL</small></div>
      <section class="appearance-section" aria-labelledby="appearance-palette-title"><div class="appearance-section-head"><span>01 / COLORWAYS</span><h3 id="appearance-palette-title">Choose a direction</h3></div><div class="appearance-palettes" role="group" aria-label="Color palette">
        <button type="button" data-appearance-palette="atelier" aria-pressed="false"><i></i><span>Atelier</span></button>
        <button type="button" data-appearance-palette="moss" aria-pressed="false"><i></i><span>Moss</span></button>
        <button type="button" data-appearance-palette="ember" aria-pressed="false"><i></i><span>Ember</span></button>
        <button type="button" data-appearance-palette="cobalt" aria-pressed="false"><i></i><span>Cobalt</span></button>
        <button type="button" data-appearance-palette="iris" aria-pressed="false"><i></i><span>Iris</span></button>
        <button type="button" data-appearance-palette="paper" aria-pressed="false"><i></i><span>Paper</span></button>
      </div><div class="appearance-colors">
        <label><span><strong>Accent</strong><small>Buttons and details</small></span><input id="appearance-accent" type="color" aria-label="Accent color"></label>
        <label><span><strong>Glass tint</strong><small>Balanced across panels</small></span><input id="appearance-surface" type="color" aria-label="Glass tint color"></label>
      </div></section>
      <section class="appearance-section" aria-labelledby="appearance-material-title"><div class="appearance-section-head"><span>02 / MATERIAL</span><h3 id="appearance-material-title">Shape the space</h3></div><div class="appearance-finishes" role="group" aria-label="Surface finish"><button type="button" data-appearance-finish="instrument" aria-pressed="false"><span aria-hidden="true">▥</span><strong>Instrument</strong><small>Precise, tactile edges</small></button><button type="button" data-appearance-finish="glass" aria-pressed="false"><span aria-hidden="true">◈</span><strong>Glass</strong><small>Light through panels</small></button><button type="button" data-appearance-finish="soft" aria-pressed="false"><span aria-hidden="true">◉</span><strong>Soft</strong><small>Quiet, rounded relief</small></button></div><div class="appearance-ranges">
        <label><span><strong>Surface opacity</strong><output id="appearance-opacity-value"></output></span><input id="appearance-opacity" type="range" min="0" max="100" step="1"></label>
        <label><span><strong>Glass blur</strong><output id="appearance-blur-value"></output></span><input id="appearance-blur" type="range" min="0" max="36" step="1"></label>
        <label><span><strong>Corner radius</strong><output id="appearance-radius-value"></output></span><input id="appearance-radius" type="range" min="4" max="24" step="1"></label>
        <label><span><strong>Reading size</strong><output id="appearance-scale-value"></output></span><input id="appearance-scale" type="range" min="90" max="120" step="1"></label>
      </div></section>
      <section class="appearance-section" aria-labelledby="appearance-comfort-title"><div class="appearance-section-head"><span>03 / COMFORT</span><h3 id="appearance-comfort-title">Make it comfortable</h3></div><div class="appearance-toggles">
        <label><span><strong>Sharper contrast</strong><small>Clearer edges and labels</small></span><input id="appearance-contrast" type="checkbox"></label>
        <label><span><strong>Reduce motion</strong><small>Quiet transitions and hover movement</small></span><input id="appearance-motion" type="checkbox"></label>
        <label><span><strong>Room photography</strong><small>Show the studio in the background</small></span><input id="appearance-photo" type="checkbox"></label>
      </div></section>
      <section class="appearance-section appearance-actions" aria-label="Save or restore appearance"><button id="appearance-export" type="button">Export look ↓</button><button id="appearance-import" type="button">Import look ↑</button><input id="appearance-file" type="file" accept="application/json,.json" hidden><button id="appearance-reset" type="button">Reset</button><p id="appearance-status" role="status" aria-live="polite">Changes save automatically on this device.</p></section>
    </div>`;
  document.body.append(dialog);
  const q = selector => dialog.querySelector(selector);
  const controls = {
    accent:q("#appearance-accent"), surface:q("#appearance-surface"), opacity:q("#appearance-opacity"), blur:q("#appearance-blur"),
    radius:q("#appearance-radius"), scale:q("#appearance-scale"), contrast:q("#appearance-contrast"),
    motion:q("#appearance-motion"), photo:q("#appearance-photo")
  };
  function inkOn(color) {
    const values = [1, 3, 5].map(index => parseInt(color.slice(index, index + 2), 16) / 255);
    const lum = values.map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
    return lum[0] * .2126 + lum[1] * .7152 + lum[2] * .0722 > .42 ? "#172b2b" : "#ffffff";
  }
  function syncControls() {
    q(".appearance-palettes").querySelectorAll("button").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.appearancePalette === settings.palette)));
    q(".appearance-finishes").querySelectorAll("button").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.appearanceFinish === settings.finish)));
    const palette = PALETTES[settings.palette];
    controls.accent.value = settings.accent || palette.accent;
    controls.surface.value = settings.surface || palette.surface;
    for (const key of ["opacity", "blur", "radius", "scale"]) controls[key].value = settings[key];
    for (const key of ["contrast", "motion", "photo"]) controls[key].checked = settings[key];
    q("#appearance-opacity-value").value = settings.opacity + "%";
    q("#appearance-blur-value").value = settings.blur + " px";
    q("#appearance-radius-value").value = settings.radius + " px";
    q("#appearance-scale-value").value = settings.scale + "%";
  }
  function apply(persist = true) {
    const palette = PALETTES[settings.palette], accent = settings.accent || palette.accent;
    const tint = settings.surface;
    const tokens = {
      "--appearance-background":palette.background,
      "--appearance-stage":palette.stage,
      "--appearance-surface":tint ? `color-mix(in srgb, ${tint} 25%, ${palette.surface})` : palette.surface,
      "--appearance-panel":tint ? `color-mix(in srgb, ${tint} 25%, ${palette.panel})` : palette.panel,
      "--appearance-ink":palette.ink,
      "--appearance-muted":palette.muted, "--appearance-accent":accent,
      "--appearance-accent-ink":inkOn(accent), "--appearance-edge":palette.edge,
      "--appearance-opacity":settings.opacity + "%", "--appearance-radius":settings.radius + "px",
      "--appearance-blur":settings.blur + "px",
      "--appearance-scale":String(settings.scale / 100)
    };
    body.dataset.palette = settings.palette;
    body.dataset.finish = settings.finish;
    body.dataset.clearGlass = String(settings.finish === "glass" && settings.opacity < 35 && ["atelier", "paper"].includes(settings.palette) && !settings.photo);
    for (const [name, value] of Object.entries(tokens)) body.style.setProperty(name, value);
    body.classList.toggle("appearance-high-contrast", settings.contrast);
    body.classList.toggle("appearance-reduce-motion", settings.motion || prefersReducedMotion);
    body.classList.toggle("appearance-no-photo", !settings.photo);
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", palette.background);
    syncControls();
    if (persist) { try { localStorage.setItem(KEY, JSON.stringify(settings)); } catch { /* The current tab still works. */ } }
  }
  function update(key, value) { settings[key] = value; apply(); q("#appearance-status").textContent = "Your look is saved on this device."; }
  q(".appearance-palettes").addEventListener("click", event => {
    const button = event.target.closest("[data-appearance-palette]");
    if (!button) return;
    settings = {...settings, palette:button.dataset.appearancePalette, accent:"", surface:""};
    apply(); q("#appearance-status").textContent = PALETTES[settings.palette].name + " palette applied.";
  });
  q(".appearance-finishes").addEventListener("click", event => {
    const button = event.target.closest("[data-appearance-finish]");
    if (!button) return;
    settings.finish = button.dataset.appearanceFinish;
    apply(); q("#appearance-status").textContent = button.querySelector("strong").textContent + " finish applied.";
  });
  document.querySelectorAll("[data-hero-category]").forEach(button => button.addEventListener("click", () => {
    document.querySelector(`.category-tabs [data-category="${button.dataset.heroCategory}"]`)?.click();
    document.getElementById("collection")?.scrollIntoView({behavior:settings.motion || prefersReducedMotion ? "auto" : "smooth"});
  }));
  for (const key of ["accent", "surface", "opacity", "blur", "radius", "scale"]) controls[key].addEventListener("input", event => update(key, key === "accent" || key === "surface" ? hex(event.target.value) : Number(event.target.value)));
  for (const key of ["contrast", "motion", "photo"]) controls[key].addEventListener("change", event => update(key, event.target.checked));
  openButton.addEventListener("click", () => {
    document.querySelectorAll("dialog[open]").forEach(other => { if (other !== dialog) other.close(); });
    if (!dialog.open) dialog.showModal();
  });
  q(".appearance-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
  q("#appearance-reset").addEventListener("click", () => { settings = {...DEFAULTS}; apply(); q("#appearance-status").textContent = "Original studio look restored."; });
  q("#appearance-export").addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify({schema:SCHEMA, ...settings}, null, 2)], {type:"application/json"}));
    const link = document.createElement("a"); link.href = url; link.download = "konaet-appearance.json"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    q("#appearance-status").textContent = "Appearance file downloaded.";
  });
  q("#appearance-import").addEventListener("click", () => q("#appearance-file").click());
  q("#appearance-file").addEventListener("change", async event => {
    const file = event.target.files?.[0]; event.target.value = "";
    if (!file) return;
    try {
      if (file.size > 16384) throw new Error("The appearance file is too large.");
      const data = JSON.parse(await file.text());
      if (data?.schema !== SCHEMA) throw new Error("This is not a KONAET appearance file.");
      settings = clean(data); apply(); q("#appearance-status").textContent = "Appearance imported and saved.";
    } catch (error) { q("#appearance-status").textContent = error.message || "Could not read this file."; }
  });
  window.addEventListener("storage", event => { if (event.key === KEY) { settings = read(); apply(false); } });
  apply(false);
})();
