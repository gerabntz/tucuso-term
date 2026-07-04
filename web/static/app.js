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

  // Favorites + history — device-local only (localStorage); nothing is ever
  // sent to the server, consistent with the anti-surveillance schema (M4/M9).
  var HIST_MAX = 30;

  function load(key) {
    try { return JSON.parse(localStorage.getItem(key)) || []; }
    catch (e) { return []; }
  }
  function save(key, list) {
    try { localStorage.setItem(key, JSON.stringify(list)); } catch (e) {}
  }

  var article = document.querySelector("article.term[data-id]");
  if (article) {
    var entry = {
      id: article.getAttribute("data-id"),
      text: article.getAttribute("data-text"),
      lang: article.getAttribute("data-lang"),
      cp: (document.querySelector(".counterpart.big") || {}).textContent || ""
    };
    // history: most recent first, de-duplicated, capped
    var hist = load("tucuso-hist").slice(0, HIST_MAX)
      .filter(function (h) { return h.id !== entry.id; });
    hist.unshift(entry);
    save("tucuso-hist", hist.slice(0, HIST_MAX));

    // favorite toggle button (JS-only enhancement)
    var favs = load("tucuso-favs");
    function isFav() {
      return favs.some(function (f) { return f.id === entry.id; });
    }
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "fav-btn" + (isFav() ? " on" : "");
    btn.textContent = isFav() ? "★ Guardado" : "☆ Guardar";
    btn.addEventListener("click", function () {
      favs = isFav()
        ? favs.filter(function (f) { return f.id !== entry.id; })
        : [entry].concat(favs);
      save("tucuso-favs", favs);
      btn.className = "fav-btn" + (isFav() ? " on" : "");
      btn.textContent = isFav() ? "★ Guardado" : "☆ Guardar";
    });
    article.insertBefore(btn, article.querySelector("dl"));
  }

  // /guardados page: render both lists from localStorage
  function fillList(ulId, items, emptyMsg) {
    var ul = document.getElementById(ulId);
    if (!ul) return false;
    ul.innerHTML = "";
    if (!items.length) {
      var p = document.createElement("li");
      p.className = "meta";
      p.textContent = emptyMsg;
      ul.appendChild(p);
      return true;
    }
    items.forEach(function (t) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "/term/" + t.id;
      var strong = document.createElement("strong");
      strong.textContent = t.text;
      a.appendChild(strong);
      li.appendChild(a);
      if (t.cp) {
        var span = document.createElement("span");
        span.className = "counterpart";
        span.textContent = t.cp;
        li.appendChild(span);
      }
      ul.appendChild(li);
    });
    return true;
  }
  fillList("fav-list", load("tucuso-favs"), "Aún no ha guardado términos.");
  fillList("hist-list", load("tucuso-hist"), "Aún no ha consultado términos.");

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
