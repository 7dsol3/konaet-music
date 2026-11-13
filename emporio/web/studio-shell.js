"use strict";
// Navigation for the glass studio. Commerce, research and audio keep their own engines.
(() => {
  const body = document.body;
  if (!body.classList.contains("studio-shell")) return;
  const q = selector => document.querySelector(selector);
  const views = new Set(["discover", "research", "guide"]);
  const targets = new Set(["wallet-open", "hardware-open", "bag-button", "connections-open"]);
  function view(name, focus = false) {
    if (!views.has(name)) return;
    body.dataset.deskView = name;
    document.querySelectorAll("[data-desk-view-button]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.deskViewButton === name)));
    if (focus && name === "research") q("#workspace-query").focus();
  }
  document.querySelectorAll("[data-desk-view-button]").forEach(button => button.addEventListener("click", () => view(button.dataset.deskViewButton, true)));
  document.querySelectorAll("[data-studio-target]").forEach(button => button.addEventListener("click", () => {
    if (targets.has(button.dataset.studioTarget)) q("#" + button.dataset.studioTarget).click();
  }));
  document.querySelectorAll('a[href="#collection"]').forEach(link => link.addEventListener("click", () => view("discover")));
  q("#research-focus").addEventListener("click", () => view("research", true));
  q("#studio-search").addEventListener("submit", event => {
    event.preventDefault();
    view("discover");
    q("#catalog-query").value = q("#studio-query").value.trim();
    q("#catalog-form").dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    q("#collection").scrollIntoView?.({ block: "start", behavior: "auto" });
  });
  document.addEventListener("keydown", event => {
    if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey || /INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName || "") || q("dialog[open]")) return;
    event.preventDefault(); q("#studio-query").focus();
  });
  function lighting() {
    q("#studio-light").setAttribute("aria-pressed", String(body.classList.contains("ambient")));
    try { localStorage.setItem("konaet-studio-light", body.classList.contains("ambient") ? "soft" : "clear"); } catch { /* Device storage is optional. */ }
  }
  try { body.classList.toggle("ambient", localStorage.getItem("konaet-studio-light") === "soft"); } catch { /* Keep the default material. */ }
  q("#ambient-toggle").setAttribute("aria-pressed", String(body.classList.contains("ambient")));
  q("#ambient-toggle").addEventListener("click", lighting);
  q("#studio-light").addEventListener("click", () => q("#ambient-toggle").click());
  q("#studio-light").setAttribute("aria-pressed", String(body.classList.contains("ambient")));
  // Research replies can originate in the voice drawer, not just the research page.
  const results = q("#research-panel");
  new MutationObserver(() => { if (!results.hidden) view("research"); }).observe(results, { attributes: true, attributeFilter: ["hidden"] });
  view("discover");
})();
