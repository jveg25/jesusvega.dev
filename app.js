/* Tab navigation and the English/Spanish switch.
 *
 * Progressive enhancement throughout: the markup is a normal page with five
 * sections and in-page anchors, and <body> ships with data-lang="en" already
 * set. With JavaScript disabled the page is still fully readable in English and
 * every link still works. This script adds the tabbing behaviour and lets the
 * reader change language.
 */

(function () {
  "use strict";

  /* ── language ─────────────────────────────────────────────────────── */

  var LANGS = ["en", "es"];
  var STORE_KEY = "jv-lang";
  var langButtons = Array.prototype.slice.call(
    document.querySelectorAll("[data-set-lang]")
  );

  // localStorage throws in private-mode Safari and when cookies are blocked,
  // so every access is guarded. A failure here should cost the reader nothing.
  function stored(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (e) {
      return null;
    }
  }

  function setLang(lang, remember) {
    if (LANGS.indexOf(lang) === -1) lang = "en";

    document.body.setAttribute("data-lang", lang);
    document.documentElement.lang = lang;

    langButtons.forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.setLang === lang));
    });

    if (remember) stored(STORE_KEY, lang);
  }

  /* Preference order: an explicit ?lang= in the URL (so a link can point at a
     specific language), then a previous choice, then the browser's own
     setting — a visitor whose browser is Spanish should land in Spanish. */
  function initialLang() {
    var fromQuery = new URLSearchParams(location.search).get("lang");
    if (LANGS.indexOf(fromQuery) !== -1) return fromQuery;

    var saved = stored(STORE_KEY);
    if (LANGS.indexOf(saved) !== -1) return saved;

    /* navigator.languages is the reader's whole ordered preference list, not
       just their top choice — so someone set to Portuguese, then Spanish, then
       English gets Spanish rather than falling through to English. Region
       subtags are dropped: es-PE, es-419 and es all count as Spanish. */
    var preferred = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || "en"];

    for (var i = 0; i < preferred.length; i++) {
      var base = String(preferred[i]).toLowerCase().split("-")[0];
      if (LANGS.indexOf(base) !== -1) return base;
    }

    return "en";   // anything else: German, Japanese, … falls back to English
  }

  langButtons.forEach(function (b) {
    b.addEventListener("click", function () {
      setLang(b.dataset.setLang, true);
    });
  });

  setLang(initialLang(), false);

  /* ── tabs ─────────────────────────────────────────────────────────── */

  var links = Array.prototype.slice.call(document.querySelectorAll(".tabs a"));
  var panels = Array.prototype.slice.call(document.querySelectorAll(".panel"));

  if (links.length && panels.length) {
    var names = panels.map(function (p) { return p.id; });
    document.body.classList.add("tabbed");

    var show = function (name, updateHash) {
      if (names.indexOf(name) === -1) name = names[0];

      panels.forEach(function (p) {
        p.classList.toggle("is-active", p.id === name);
      });
      links.forEach(function (a) {
        // aria-current is what the active-tab underline hangs off in CSS, and
        // what a screen reader announces.
        if (a.dataset.tab === name) a.setAttribute("aria-current", "page");
        else a.removeAttribute("aria-current");
      });

      if (updateHash && history.replaceState) {
        history.replaceState(null, "", "#" + name);
      }
    };

    links.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        show(a.dataset.tab, true);
        // Jump, don't glide: switching tabs replaces the content outright, so a
        // smooth scroll just shows the reader a section they didn't ask for.
        window.scrollTo({ top: 0, behavior: "auto" });
      });
    });

    // Back/forward and pasted #hash links land on the right tab.
    window.addEventListener("hashchange", function () {
      show(location.hash.replace("#", ""), false);
    });

    show(location.hash.replace("#", ""), false);
  }

  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
