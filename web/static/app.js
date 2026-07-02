/* Progressive enhancement only — every page works without JS (low-end
   Android reality). This file: offline banner + client-side search fallback
   over the cached snapshot when the network is gone (M5). */
(function () {
  "use strict";

  var banner = document.getElementById("offline-banner");

  function setOffline(off) {
    if (banner) banner.hidden = !off;
  }
  window.addEventListener("online", function () { setOffline(false); });
  window.addEventListener("offline", function () { setOffline(true); });
  setOffline(!navigator.onLine);

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").then(function (reg) {
      if (navigator.onLine && reg.active) reg.active.postMessage("refresh-snapshot");
    });
  }
  // Ask the browser not to evict our offline glossary under storage pressure (M11)
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist();

  // Offline search fallback: intercept the search form and query the cached
  // snapshot if the server is unreachable.
  var form = document.getElementById("search-form");
  if (!form) return;

  function deaccent(s) {
    return s.normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function snapshotSearch(q, done) {
    caches.open("tucuso-data").then(function (cache) {
      return cache.match("/api/export/terms.json");
    }).then(function (resp) {
      if (!resp) return done(null);
      resp.json().then(function (data) {
        var needle = deaccent(q.toLowerCase());
        var hits = data.terms.filter(function (t) {
          return deaccent((t.text + " " + (t.example || "")).toLowerCase())
            .indexOf(needle) !== -1;
        }).slice(0, 20);
        var byConcept = {};
        data.terms.forEach(function (t) {
          (byConcept[t.concept_id] = byConcept[t.concept_id] || []).push(t);
        });
        hits.forEach(function (t) {
          t.counterparts = (byConcept[t.concept_id] || []).filter(function (c) {
            return c.lang !== t.lang;
          });
        });
        var el = document.getElementById("snapshot-date");
        if (el && data.generated) el.textContent = " (datos del " + data.generated + ")";
        done(hits);
      });
    }).catch(function () { done(null); });
  }

  function render(hits) {
    var ul = document.getElementById("results");
    ul.innerHTML = "";
    hits.forEach(function (t) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "/term/" + t.id;
      var strong = document.createElement("strong");
      strong.textContent = t.text;
      a.appendChild(strong);
      li.appendChild(a);
      (t.counterparts || []).forEach(function (c) {
        var span = document.createElement("span");
        span.className = "counterpart";
        span.textContent = "⇄ " + c.text + " (" + c.lang + ")";
        li.appendChild(span);
      });
      var meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = t.category;
      li.appendChild(meta);
      ul.appendChild(li);
    });
  }

  form.addEventListener("submit", function (ev) {
    if (navigator.onLine) return; // normal server-rendered flow
    ev.preventDefault();
    setOffline(true);
    snapshotSearch(document.getElementById("q").value, function (hits) {
      if (hits) render(hits);
    });
  });
})();
