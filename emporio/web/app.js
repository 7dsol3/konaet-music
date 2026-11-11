"use strict";
// No generated HTML from catalog, chat, provider output or customer input.
const $ = (selector) => document.querySelector(selector);
const make = (tag, cls = "", text) => {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text !== undefined) el.textContent = text;
  return el;
};
const action = (text, cls, handler) => {
  const b = make("button", cls, text); b.type = "button"; b.addEventListener("click", handler); return b;
};
const money = (cents) => new Intl.NumberFormat("en-US", { style: "currency", currency: "BRL" }).format(cents / 100);
const art = (p) => "/static/instrument-" + (p.category_id === 3 ? "drums" : p.category_id === 4 ? "keys" : [6, 7].includes(p.category_id) ? "wind" : [1, 2].includes(p.category_id) ? "electric" : "guitar") + ".svg";
const imageFor = (p) => { const img = make("img"); img.src = art(p); img.alt = "Instrument family illustration, not a product photograph"; img.loading = "lazy"; return img; };
const state = { products: [], cache: new Map(), shown: 12, category: "", compared: new Set(), cart: null, busy: false,
  history: [], lastProducts: [], checkoutAttempt: null, catalogController: null, recognition: null, listening: false, quoteTimer: null };
let toastTimer;
let cartQueue = Promise.resolve();
let installPrompt = null;
window.addEventListener("beforeinstallprompt", event => { event.preventDefault(); installPrompt = event; $("#install-app").hidden = false; });
window.addEventListener("appinstalled", () => { installPrompt = null; $("#install-app").hidden = true; });

async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 65000);
  const abort = () => controller.abort();
  options.signal?.addEventListener("abort", abort, { once: true });
  if (options.signal?.aborted) controller.abort();
  try {
    const response = await fetch(path, { credentials: "same-origin", ...options, signal: controller.signal,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) } });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Please check your request and try again.");
    return data;
  } finally { clearTimeout(timer); options.signal?.removeEventListener("abort", abort); }
}
function toast(text) {
  clearTimeout(toastTimer);
  const box = $("#toast"); (document.querySelector("dialog[open]") || document.body).append(box);
  box.textContent = text; box.hidden = false; toastTimer = setTimeout(() => { box.hidden = true; }, 4000);
}
function openDialog(id) {
  for (const d of document.querySelectorAll("dialog[open]")) if (d.id !== id) d.close();
  const dialog = $("#" + id); if (!dialog.open) dialog.showModal();
}
function cacheProducts(products) {
  const categories = { 1: "Electric guitars", 2: "Bass guitars", 3: "Drums & percussion", 4: "Keys & pianos", 5: "Acoustic guitars", 6: "Woodwinds", 7: "Brass", 8: "Orchestral strings", 9: "Ukuleles" };
  for (const p of products) { p.category = categories[p.category_id] || p.category; state.cache.set(p.id, p); }
}
function availability(p) { return p.available ? "Available in the case catalog" : p.status === "coming_soon" ? "Coming soon" : p.status === "discontinued" ? "Discontinued" : "Out of stock"; }
function stockLabel(p) { const el = make("p", "stock-label"); if (p.available) el.append(make("span", "status-dot")); el.append(document.createTextNode(availability(p))); return el; }
function priceNode(p) {
  const el = make("div", "product-price");
  if (p.discount_percent) el.append(make("span", "old-price", money(p.price_cents)));
  el.append(document.createTextNode(money(p.sale_cents))); return el;
}

function productCard(p) {
  const card = make("article", "product-card");
  const visual = make("div", "product-art"); visual.append(imageFor(p));
  const detail = action("", "detail-trigger", () => showProduct(p)); detail.setAttribute("aria-label", "View " + p.name); visual.append(detail);
  if (p.discount_percent) visual.append(make("span", "product-badge promotion", p.discount_percent + "% active offer"));
  else if (!p.available) visual.append(make("span", "product-badge", p.status === "coming_soon" ? "Coming soon" : "Unavailable"));
  const compare = action(state.compared.has(p.id) ? "✓" : "+", "compare-check", () => toggleCompare(p.id));
  compare.setAttribute("aria-label", "Compare " + p.name); compare.setAttribute("aria-pressed", String(state.compared.has(p.id))); compare.dataset.compareId = p.id; visual.append(compare);
  const meta = make("div", "product-meta"); meta.append(make("p", "product-category", p.category));
  meta.append(action(p.name, "product-name", () => showProduct(p)));
  const row = make("div", "product-price-row"); row.append(priceNode(p));
  const add = action("+", "add-small", () => addToBag(p.id, add)); add.setAttribute("aria-label", "Add " + p.name + " to bag"); add.disabled = !p.available; row.append(add);
  meta.append(row, stockLabel(p)); card.append(visual, meta); return card;
}
function renderCatalog() {
  const grid = $("#catalog-grid"); grid.replaceChildren();
  const shown = state.products.slice(0, state.shown);
  for (const p of shown) grid.append(productCard(p));
  if (!shown.length) { const empty = make("div", "empty-state"); empty.append(make("h3", "", "A different direction?"), make("p", "", "Try another model, category or budget. We only show what is in the supplied catalog.")); grid.append(empty); }
  $("#catalog-count").textContent = "Showing " + shown.length + " of " + state.products.length + " instruments";
  $("#load-more").hidden = state.shown >= state.products.length;
}
async function loadCatalog() {
  state.catalogController?.abort(); const controller = new AbortController(); state.catalogController = controller;
  const params = new URLSearchParams({ sort: $("#catalog-sort").value, available_only: String($("#available-only").checked) });
  if (state.category) params.set("category_id", state.category);
  if ($("#catalog-query").value.trim()) params.set("query", $("#catalog-query").value.trim());
  if ($("#catalog-budget").value) params.set("max_price_brl", $("#catalog-budget").value);
  $("#catalog-error").hidden = true; $("#catalog-count").textContent = "Checking the catalog…";
  if (!state.products.length) $("#catalog-grid").replaceChildren(...Array.from({ length: 8 }, () => make("div", "skeleton")));
  try {
    const data = await api("/api/shop?" + params, { signal: controller.signal });
    state.products = data.products; state.shown = 12; cacheProducts(data.products); renderCatalog();
  } catch (error) {
    if (error.name === "AbortError") return;
    $("#catalog-grid").replaceChildren(); $("#load-more").hidden = true;
    $("#catalog-count").textContent = "The collection could not be loaded.";
    $("#catalog-error").textContent = error.message; $("#catalog-error").hidden = false;
  }
}
function showProduct(p) {
  const grid = make("div", "product-detail-grid"), visual = make("div", "detail-art"); visual.append(imageFor(p));
  const copy = make("div", "detail-copy"); copy.append(make("p", "eyebrow", p.category));
  const title = make("h2", "", p.name); title.id = "product-title"; copy.append(title, priceNode(p), stockLabel(p));
  if (p.discount_percent) copy.append(make("p", "small", "An active " + p.discount_percent + "% promotion is already included. PIX discounts do not stack."));
  const specs = make("dl", "detail-specs");
  for (const [key, value] of Object.entries(p.specs)) specs.append(make("dt", "", specLabel(key)), make("dd", "", specValue(value)));
  copy.append(specs);
  const add = action("Add to bag ↗", "button primary", () => addToBag(p.id, add)); add.disabled = !p.available;
  copy.append(add, action(state.compared.has(p.id) ? "Remove from comparison" : "Add to comparison", "text-button", () => { toggleCompare(p.id); showProduct(p); }));
  copy.append(make("p", "small", "Recorded catalog details. Illustrations show the instrument family. No stock reservation is made."));
  grid.append(visual, copy); $("#product-detail").replaceChildren(grid); openDialog("product-dialog");
}
function specLabel(key) { return ({ material: "Material", body: "Body", strings: "Strings", frets: "Frets", color: "Color", type: "Type", size: "Size", keys: "Keys", pickups: "Pickups", finish: "Finish", neck: "Neck", scale: "Scale" })[key] || key.replaceAll("_", " "); }
function specValue(value) { return value === null || value === undefined ? "Not recorded" : typeof value === "object" ? JSON.stringify(value) : String(value); }
function toggleCompare(id) {
  if (state.compared.has(id)) state.compared.delete(id);
  else if (state.compared.size < 3) state.compared.add(id);
  else { toast("Choose up to three instruments to compare."); return; }
  renderCompareTray();
}
function renderCompareTray() {
  $("#compare-tray").hidden = !state.compared.size; $("#compare-nav-count").textContent = String(state.compared.size);
  $("#compare-open").disabled = state.compared.size < 2;
  const picks = $("#compare-picked"); picks.replaceChildren();
  for (const id of state.compared) {
    const p = state.cache.get(id), el = make("span", "", p?.name || "Instrument " + id);
    const remove = action("×", "", () => toggleCompare(id)); remove.setAttribute("aria-label", "Remove " + (p?.name || id) + " from comparison"); el.append(remove); picks.append(el);
  }
  for (const button of document.querySelectorAll("[data-compare-id]")) {
    const selected = state.compared.has(Number(button.dataset.compareId)); button.textContent = selected ? "✓" : "+"; button.setAttribute("aria-pressed", String(selected));
  }
}
async function showComparison() {
  if (state.compared.size < 2) { toast("Choose two or three instruments using the + on each card."); return; }
  try {
    const data = await api("/api/compare?ids=" + [...state.compared].join(",")); cacheProducts(data.products);
    const table = make("table", "comparison-table"), caption = make("caption", "sr-only", "Recorded specifications of selected instruments"); table.append(caption);
    const head = make("thead"), top = make("tr"); top.append(make("th", "", "Instrument"));
    for (const p of data.products) { const td = make("td"); td.append(imageFor(p), make("h3", "", p.name)); top.append(td); } head.append(top); table.append(head);
    const body = make("tbody");
    const rows = [["Category", (p) => p.category], ["Current price", (p) => money(p.sale_cents)], ["Active discount", (p) => p.discount_percent ? p.discount_percent + "%" : "None"], ["Availability", availability], ...data.spec_keys.map(key => [specLabel(key), p => specValue(p.specs[key])])];
    for (const [label, value] of rows) { const tr = make("tr"), th = make("th", "", label); th.scope = "row"; tr.append(th); for (const p of data.products) tr.append(make("td", "", value(p))); body.append(tr); }
    const buttons = make("tr"); buttons.append(make("th", "", "Your choice"));
    for (const p of data.products) { const td = make("td"), b = action("Add to bag ↗", "button primary", () => addToBag(p.id, b)); b.disabled = !p.available; td.append(b); buttons.append(td); } body.append(buttons); table.append(body);
    const scroll = make("div", "comparison-scroll"); scroll.append(table);
    $("#compare-content").replaceChildren(scroll, make("p", "comparison-note", data.notice)); openDialog("compare-dialog");
  } catch (error) { toast(error.message); }
}

async function refreshBag() { state.cart = await api("/api/cart"); $("#bag-count").textContent = String(state.cart.quantity); renderBag(); }
async function addToBag(id, button) {
  if (button) button.disabled = true;
  const run = () => performAddToBag(id, button);
  cartQueue = cartQueue.then(run, run);
  return cartQueue;
}
async function performAddToBag(id, button) {
  try {
    // Always read current cart before incrementing. The server checks stock.
    const current = await api("/api/cart"), previous = current.items.find(i => i.product.id === id);
    state.cart = await api("/api/cart", { method: "PUT", body: JSON.stringify({ product_id: id, quantity: (previous?.quantity || 0) + 1 }) });
    state.checkoutAttempt = null; $("#bag-count").textContent = String(state.cart.quantity); renderBag(); toast("Added to your bag.");
  } catch (error) { toast(error.message); } finally { if (button) button.disabled = false; }
}
async function changeQuantity(id, quantity, button) {
  button.disabled = true;
  try { state.cart = await api("/api/cart", { method: "PUT", body: JSON.stringify({ product_id: id, quantity }) }); state.checkoutAttempt = null; $("#bag-count").textContent = String(state.cart.quantity); renderBag(); }
  catch (error) { toast(error.message); button.disabled = false; }
}
function renderBag() {
  if (!state.cart) return;
  const root = $("#cart-items"); root.replaceChildren();
  if (!state.cart.items.length) { const empty = make("div", "empty-state"); empty.append(make("h3", "", "Room for a new sound."), make("p", "", "Find an instrument you love and add it to your bag.")); root.append(empty); }
  for (const item of state.cart.items) {
    const p = item.product, row = make("article", "cart-item"), copy = make("div"); row.append(imageFor(p));
    copy.append(make("h3", "", p.name), make("p", "", money(item.line_total_cents)));
    if (!item.available) copy.append(make("p", "inline-error", "This quantity is no longer available. Update your bag."));
    const controls = make("div", "cart-quantity");
    const minus = action("−", "", () => changeQuantity(p.id, item.quantity - 1, minus)); minus.setAttribute("aria-label", "Decrease quantity of " + p.name);
    const plus = action("+", "", () => changeQuantity(p.id, item.quantity + 1, plus)); plus.setAttribute("aria-label", "Increase quantity of " + p.name); plus.disabled = item.quantity >= Math.min(20, p.stock);
    const remove = action("Remove", "remove-item", () => changeQuantity(p.id, 0, remove));
    controls.append(minus, make("span", "", item.quantity), plus, remove); copy.append(controls); row.append(copy); root.append(row);
  }
  $("#cart-subtotal").textContent = money(state.cart.subtotal_cents); $("#checkout-button").disabled = !state.cart.checkout_available;
}
async function showBag() { try { await refreshBag(); openDialog("cart-dialog"); } catch (error) { toast(error.message); } }
async function checkout() {
  const button = $("#checkout-button"); button.disabled = true;
  try {
    const method = document.querySelector('[name="checkout-method"]:checked').value;
    if (!state.checkoutAttempt || state.checkoutAttempt.method !== method) state.checkoutAttempt = { request_key: crypto.randomUUID(), method };
    const quote = await api("/api/checkout", { method: "POST", body: JSON.stringify(state.checkoutAttempt) }); showQuote(quote);
  } catch (error) { toast(error.message); state.checkoutAttempt = null; }
  finally { button.disabled = !state.cart?.checkout_available; }
}
function showQuote(quote) {
  clearInterval(state.quoteTimer);
  const grid = make("div", "checkout-grid"), info = make("div", "checkout-info"), visual = make("div", "checkout-code");
  info.append(make("span", "pill", "CHECKOUT PREVIEW · NO CHARGE"), make("h3", "", "A little closer to your next sound."));
  const lines = make("ul", "checkout-lines");
  for (const item of quote.items) { const li = make("li"); li.append(make("span", "", item.quantity + " × " + item.name), make("span", "", money(item.line_total_cents))); lines.append(li); }
  const total = make("div", "checkout-total"); total.append(make("span", "", "Instrument total"), make("strong", "", money(quote.subtotal_cents)));
  info.append(lines, total, make("p", "", quote.method === "pix" ? "PIX pricing is included where eligible. Promotional offers are never combined with an extra PIX discount." : "List or active promotional prices. No card details are collected."), make("p", "", quote.shipping), make("p", "", "This is a demonstration quote, not a purchase, payment request or stock reservation."));
  const expiry = make("span", "checkout-expiry"); info.append(expiry);
  const img = make("img"); img.src = "/api/checkout/" + quote.id + "/code.svg"; img.alt = "Unique KONAET Code that opens this checkout preview"; visual.append(img);
  const links = make("div", "code-actions"), download = make("a", "", "Download SVG"); download.href = img.src; download.download = "konaet-" + quote.id.slice(-10) + ".svg";
  const copy = action("Copy checkout link", "", async () => { try { await navigator.clipboard.writeText(quote.checkout_url); toast("Checkout link copied."); } catch { toast("Copy the checkout link shown below."); } }); links.append(download, copy); visual.append(links);
  const link = make("a", "checkout-link", quote.checkout_url); link.href = quote.checkout_url; link.target = "_blank"; link.rel = "noopener"; info.append(link);
  if (["localhost", "127.0.0.1", "::1"].includes(new URL(quote.checkout_url).hostname)) info.append(make("p", "small", "This link uses a local address. A public HTTPS domain is needed to scan it from a different device."));
  grid.append(info, visual); $("#checkout-content").replaceChildren(grid); openDialog("checkout-dialog");
  const tick = () => {
    const remaining = Math.max(0, Math.ceil((Date.parse(quote.expires_at) - Date.now()) / 1000));
    expiry.textContent = remaining ? "Expires in " + Math.floor(remaining / 60) + ":" + String(remaining % 60).padStart(2, "0") + " · Reference " + quote.id.slice(-10).toUpperCase() : "This quote has expired. Prepare a new checkout.";
    if (!remaining) { clearInterval(state.quoteTimer); img.hidden = true; download.removeAttribute("href"); link.removeAttribute("href"); state.checkoutAttempt = null; }
  }; tick(); state.quoteTimer = setInterval(tick, 1000);
}

function openAssistant() { openDialog("assistant-dialog"); $("#message-input").focus(); }
function sourceNode(source) {
  const node = make(source.type === "policy" ? "a" : "span", "source-chip", source.label);
  if (source.type === "policy" && Number.isInteger(source.page)) { node.href = "/manual#page=" + source.page; node.target = "_blank"; node.rel = "noopener"; }
  return node;
}
function appendMessage(role, text, result) {
  $("#assistant-welcome").hidden = true;
  const item = make("article", "message " + role); item.append(make("div", "role", role === "user" ? "YOU" : "KONAET"), make("div", "message-text", text));
  if (result?.sources?.length) { const refs = make("div", "message-meta"); for (const s of result.sources) refs.append(sourceNode(s)); item.append(refs); }
  if (result?.results) {
    const products = result.results.filter(r => r.kind === "catalog").flatMap(r => r.products);
    if (products.length) { state.lastProducts = [...new Map(products.map(p => [p.id, p])).values()].slice(0, 8); cacheProducts(state.lastProducts); }
    for (const p of products.slice(0, 3)) {
      const row = make("div", "assistant-product"), copy = make("div"); copy.append(make("strong", "", p.name), make("span", "", money(p.sale_cents)));
      const b = action("View ↗", "", () => showProduct(p)); row.append(copy, b); item.append(row);
    }
  }
  if (result?.tools?.length) {
    const detail = make("details", "tool-details"); detail.append(make("summary", "", "See what was checked"), make("p", "", result.tools.map(t => t.tool.replaceAll("_", " ") + ": " + t.status.replaceAll("_", " ")).join(" · ")),
      make("p", "", (result.mode === "openai_compatible" ? "Model-selected, validated tools" : result.mode === "local_fallback" ? "Local fallback after model planning" : "Local rules") + " · " + Math.round(result.latency_ms) + " ms · Receipt " + result.audit_hash.slice(0, 12))); item.append(detail);
  }
  $("#messages").append(item); $("#messages").scrollTop = $("#messages").scrollHeight; return item;
}
function speak(text) {
  if (!$("#read-aloud").checked || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel(); const utterance = new SpeechSynthesisUtterance(text.slice(0, 1400)); utterance.lang = "en-US"; utterance.rate = 1;
  const voice = window.speechSynthesis.getVoices().find(v => /^en[-_]/i.test(v.lang)); if (voice) utterance.voice = voice; window.speechSynthesis.speak(utterance);
}
async function localCommand(text) {
  const clean = text.trim().toLowerCase().replace(/[.!?]+$/, "");
  if (/^(?:show|open)(?: me)?(?: my| the)? (?:bag|cart)$/.test(clean)) { await showBag(); return true; }
  if (/^(?:prepare|open|start)(?: my| the)? checkout$/.test(clean)) { await showBag(); toast("Review your bag and choose Continue to checkout."); return true; }
  const compare = clean.match(/^compare (?:the )?(?:first )?(two|three|2|3)(?: (?:ones|results|instruments))?$/);
  if (compare) {
    const count = ["three", "3"].includes(compare[1]) ? 3 : 2;
    if (state.lastProducts.length < count) { toast("Ask for a few instruments first, then compare those results."); return true; }
    state.compared = new Set(state.lastProducts.slice(0, count).map(p => p.id)); renderCompareTray(); await showComparison(); return true;
  }
  const add = clean.match(/^add (?:the )?(first|second|third)(?: one| instrument| result)? to (?:my |the )?(?:bag|cart)$/);
  if (add) {
    const index = { first: 0, second: 1, third: 2 }[add[1]], p = state.lastProducts[index];
    if (!p) toast("Ask for instruments first so I know which result you mean."); else await addToBag(p.id);
    return true;
  }
  return false;
}
async function send(text) {
  text = text.trim(); if (!text || state.busy) return;
  state.busy = true;
  try { if (await localCommand(text)) { state.busy = false; $("#message-input").value = ""; return; } }
  catch (error) { state.busy = false; toast(error.message); return; }
  openAssistant(); $("#send-button").disabled = true; $("#new-chat").disabled = true; $("#chat-error").hidden = true;
  $("#message-input").value = ""; const userItem = appendMessage("user", text); state.history.push({ role: "user", content: text });
  const thinking = make("div", "thinking", "Checking the catalog and store guide…"); $("#messages").append(thinking);
  try {
    const result = await api("/api/chat", { method: "POST", body: JSON.stringify({ message: text, locale: "en" }) });
    thinking.remove(); appendMessage("assistant", result.message, result); state.history.push({ role: "assistant", content: result.message });
    $("#assistant-mode").textContent = result.mode === "openai_compatible" ? "MODEL + VERIFIED TOOLS" : result.mode === "local_fallback" ? "LOCAL FALLBACK" : "LOCAL RULES + VERIFIED TOOLS"; speak(result.message);
  } catch (error) { thinking.remove(); userItem.remove(); state.history.pop(); $("#chat-error").textContent = error.name === "AbortError" ? "That took too long. Please try again." : error.message; $("#chat-error").hidden = false; $("#message-input").value = text; if (!state.history.length) $("#assistant-welcome").hidden = false; }
  finally { state.busy = false; $("#send-button").disabled = false; $("#new-chat").disabled = false; }
}
function setupVoice() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) { $("#microphone-button").disabled = true; $("#voice-status").textContent = "Voice input is not supported by this browser. You can type every command."; return; }
  const recognition = new Recognition(); state.recognition = recognition; recognition.lang = "en-US"; recognition.interimResults = true; recognition.continuous = false; recognition.maxAlternatives = 1;
  recognition.onstart = () => { state.listening = true; $("#microphone-button").setAttribute("aria-pressed", "true"); $("#microphone-button").setAttribute("aria-label", "Stop voice input"); $("#voice-status").textContent = "Listening in English… Your words will appear below."; $("#voice-status").classList.add("listening"); window.speechSynthesis?.cancel(); };
  recognition.onresult = (event) => { const text = Array.from(event.results).map(r => r[0].transcript).join(" "); $("#message-input").value = text.slice(0, 2000); };
  recognition.onerror = (event) => { $("#voice-status").textContent = event.error === "not-allowed" ? "Microphone permission was not granted. Type your message instead." : "Voice could not complete. Please try again or type your message."; };
  recognition.onend = () => { state.listening = false; $("#microphone-button").setAttribute("aria-pressed", "false"); $("#microphone-button").setAttribute("aria-label", "Start voice input"); $("#voice-status").classList.remove("listening"); if ($("#voice-status").textContent.startsWith("Listening")) $("#voice-status").textContent = "Review your words, then send. Nothing was submitted automatically."; };
  $("#microphone-button").addEventListener("click", () => { if (state.listening) recognition.stop(); else { try { recognition.start(); } catch { toast("Voice is already starting. Please wait."); } } });
}

async function showGuide() {
  try {
    const policies = await api("/api/policies?locale=en"), root = $("#policy-list"); root.replaceChildren();
    for (const p of policies) { const d = make("details"), link = make("a", "", "Original manual · pages " + p.pages.join(", ") + " ↗"); link.href = "/manual#page=" + p.pages[0]; link.target = "_blank"; link.rel = "noopener"; d.append(make("summary", "", p.title), make("p", "", p.summary), link); root.append(d); } openDialog("guide-dialog");
  } catch (error) { toast(error.message); }
}
for (const b of document.querySelectorAll("[data-close]")) b.addEventListener("click", () => $("#" + b.dataset.close).close());
for (const d of document.querySelectorAll("dialog")) d.addEventListener("click", e => { if (e.target === d) { const rect = d.getBoundingClientRect(); if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) d.close(); } });
$("#assistant-dialog").addEventListener("close", () => { state.recognition?.abort(); window.speechSynthesis?.cancel(); });
$("#checkout-dialog").addEventListener("close", () => clearInterval(state.quoteTimer));
$("#install-app").addEventListener("click", async () => { if (!installPrompt) return; await installPrompt.prompt(); await installPrompt.userChoice; installPrompt = null; $("#install-app").hidden = true; });
for (const id of ["voice-open", "hero-ask", "banner-ask", "assistant-launcher"]) $("#" + id).addEventListener("click", openAssistant);
for (const id of ["guide-button", "footer-guide"]) $("#" + id).addEventListener("click", showGuide);
$("#about-button").addEventListener("click", () => openDialog("about-dialog"));
for (const id of ["bag-button", "code-story-button"]) $("#" + id).addEventListener("click", showBag);
for (const id of ["compare-nav", "compare-open"]) $("#" + id).addEventListener("click", showComparison);
$("#compare-clear").addEventListener("click", () => { state.compared.clear(); renderCompareTray(); });
$("#catalog-form").addEventListener("submit", e => { e.preventDefault(); loadCatalog(); });
for (const id of ["catalog-sort", "available-only"]) $("#" + id).addEventListener("change", loadCatalog);
for (const b of document.querySelectorAll("[data-category]")) b.addEventListener("click", () => { state.category = b.dataset.category; for (const other of document.querySelectorAll("[data-category]")) { const on = other === b; other.classList.toggle("active", on); other.setAttribute("aria-pressed", String(on)); } loadCatalog(); });
$("#load-more").addEventListener("click", () => { state.shown += 12; renderCatalog(); });
$("#checkout-button").addEventListener("click", checkout);
$("#chat-form").addEventListener("submit", e => { e.preventDefault(); send($("#message-input").value); });
$("#message-input").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(e.target.value); } });
for (const b of document.querySelectorAll("[data-command]")) b.addEventListener("click", () => send(b.dataset.command));
$("#read-aloud").addEventListener("change", () => { if (!$("#read-aloud").checked) window.speechSynthesis?.cancel(); if (!("speechSynthesis" in window)) { $("#read-aloud").checked = false; toast("Spoken replies are not supported in this browser."); } });
$("#verify-button").addEventListener("click", () => { $("#verify-result").textContent = ""; openDialog("verify-dialog"); });
$("#verify-form").addEventListener("submit", async e => {
  e.preventDefault(); const button = e.target.querySelector('[type="submit"]'); button.disabled = true;
  try {
    const id = Number($("#order-id").value), r = await api("/api/verify", { method: "POST", body: JSON.stringify({ order_id: id, email: $("#purchase-email").value }) });
    $("#purchase-email").value = ""; $("#verify-result").textContent = r.message;
    if (r.verified) { $("#verify-dialog").close(); await send("What is the status of order #" + id + "?"); }
  } catch (error) { $("#verify-result").textContent = error.message; } finally { button.disabled = false; }
});
$("#new-chat").addEventListener("click", async () => {
  if (state.busy) return;
  try { await api("/api/session", { method: "DELETE" }); state.history = []; state.lastProducts = []; state.checkoutAttempt = null; $("#messages").replaceChildren(); $("#assistant-welcome").hidden = false; $("#chat-error").hidden = true; await refreshBag(); toast("New conversation. Your previous session and bag were cleared."); }
  catch (error) { toast(error.message); }
});
$("#export-button").addEventListener("click", () => {
  if (!state.history.length) { toast("Start a conversation first."); return; }
  const text = "# KONAET Music conversation\n\n" + state.history.map(m => "**" + (m.role === "user" ? "You" : "KONAET") + ":** " + m.content).join("\n\n");
  const url = URL.createObjectURL(new Blob([text], { type: "text/markdown;charset=utf-8" })), a = make("a"); a.href = url; a.download = "konaet-music-conversation.md"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});

async function initialize() {
  setupVoice(); loadCatalog();
  if ("serviceWorker" in navigator && window.isSecureContext) navigator.serviceWorker.register("/service-worker.js").catch(() => { /* The full online application still works without installation. */ });
  try {
    // Session creation is sequential: two fresh simultaneous requests must not
    // create different cookies for cart and conversation on the first visit.
    const session = await api("/api/session"); state.history = session.history; for (const m of state.history) appendMessage(m.role, m.content);
    await refreshBag(); const health = await api("/api/health");
    $("#assistant-mode").textContent = health.provider === "local" ? "LOCAL RULES + VERIFIED TOOLS" : "MODEL PLANNER CONFIGURED";
    const match = location.pathname.match(/^\/checkout\/([A-Za-z0-9_-]{32})$/);
    if (match) showQuote(await api("/api/checkout/" + match[1]));
  } catch (error) { $("#assistant-mode").textContent = "CONNECTION UNAVAILABLE"; toast(error.message); }
}
initialize();
