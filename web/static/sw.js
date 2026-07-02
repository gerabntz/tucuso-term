/* Service worker (T10, M5/M11): app shell precache + checksum-style guarded
   glossary snapshot swap + offline navigation fallback. */
"use strict";

var SHELL_CACHE = "tucuso-shell-v1";
var DATA_CACHE = "tucuso-data";
var SNAPSHOT = "/api/export/terms.json";
var SHELL = ["/", "/static/style.css", "/static/app.js", "/static/manifest.json",
             "/static/icon.svg", "/submit", "/status"];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(SHELL_CACHE).then(function (c) { return c.addAll(SHELL); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    Promise.all([
      caches.keys().then(function (keys) {
        return Promise.all(keys.filter(function (k) {
          return k !== SHELL_CACHE && k !== DATA_CACHE;
        }).map(function (k) { return caches.delete(k); }));
      }),
      self.registration.navigationPreload ? Promise.resolve() : Promise.resolve(),
      // Best-effort persistent storage so low-storage Androids don't evict us (M11)
      self.clients.claim()
    ])
  );
});

/* Snapshot swap (M11): only replace the cached snapshot after the new body
   parses as JSON and contains a terms array — a truncated download must
   never clobber a good copy. */
function refreshSnapshot() {
  return fetch(SNAPSHOT).then(function (resp) {
    if (!resp.ok) throw new Error("bad status");
    return resp.clone().json().then(function (data) {
      if (!data || !Array.isArray(data.terms)) throw new Error("malformed snapshot");
      return caches.open(DATA_CACHE).then(function (c) {
        return c.put(SNAPSHOT, resp);
      });
    });
  });
}

self.addEventListener("fetch", function (e) {
  var url = new URL(e.request.url);

  if (url.pathname === SNAPSHOT) {
    // opportunistic refresh, cached fallback
    e.respondWith(
      fetch(e.request).then(function (resp) {
        return resp.clone().json().then(function (data) {
          if (data && Array.isArray(data.terms)) {
            var copy = resp.clone();
            caches.open(DATA_CACHE).then(function (c) { c.put(SNAPSHOT, copy); });
          }
          return resp;
        }).catch(function () { return resp; });
      }).catch(function () {
        return caches.match(SNAPSHOT);
      })
    );
    return;
  }

  if (e.request.mode === "navigate" || SHELL.indexOf(url.pathname) !== -1) {
    e.respondWith(
      fetch(e.request).catch(function () {
        return caches.match(e.request, { ignoreSearch: true }).then(function (r) {
          return r || caches.match("/");
        });
      })
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then(function (r) { return r || fetch(e.request); })
  );
});

/* Opportunistic snapshot refresh whenever the SW wakes online (sync-oportunista). */
self.addEventListener("message", function (e) {
  if (e.data === "refresh-snapshot") e.waitUntil(refreshSnapshot().catch(function () {}));
});
