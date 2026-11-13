"use strict";
// Only the public UI shell is cached. Never cache API replies, chats,
// verification data, manuals, checkout pages or codes. No offline writes queue.
const CACHE = "konaet-music-shell-2.3.2-type";
const ASSETS = ["/", "/static/style.css", "/static/glass.css", "/static/workspace.css", "/static/workspace.js", "/static/app.js", "/static/mark.svg",
  "/static/studio-shell.js", "/static/studio-room.webp",
  "/static/typography.css", "/static/manrope-latin.woff2", "/static/waveform.svg",
  "/static/app-icon.svg", "/static/logic-map.svg", "/static/app.webmanifest", "/static/code-identity.svg", "/static/instrument-guitar.svg",
  "/static/instrument-electric.svg", "/static/instrument-keys.svg", "/static/instrument-drums.svg", "/static/instrument-wind.svg"];
self.addEventListener("install", event => { event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", event => { event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith("konaet-music-shell-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin || url.search || !ASSETS.includes(url.pathname)) return;
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok) { const copy = response.clone(); event.waitUntil(caches.open(CACHE).then(cache => cache.put(event.request, copy))); }
    return response;
  }).catch(() => caches.match(event.request).then(response => response || Response.error())));
});
