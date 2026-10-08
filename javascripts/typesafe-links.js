/* Open all typesafe.ai links in a new tab (incl. Material instant navigation). */
(function () {
  function isTypeSafeHost(hostname) {
    return hostname === "typesafe.ai" || hostname.endsWith(".typesafe.ai");
  }

  function markTypeSafeLinks(root) {
    (root || document).querySelectorAll("a[href]").forEach(function (anchor) {
      var href = anchor.getAttribute("href");
      if (!href || href.startsWith("#") || href.startsWith("mailto:")) {
        return;
      }
      try {
        var url = new URL(href, window.location.href);
        if (!isTypeSafeHost(url.hostname)) {
          return;
        }
        anchor.target = "_blank";
        var rel = (anchor.getAttribute("rel") || "").split(/\s+/).filter(Boolean);
        ["noopener", "noreferrer"].forEach(function (token) {
          if (rel.indexOf(token) === -1) {
            rel.push(token);
          }
        });
        anchor.setAttribute("rel", rel.join(" "));
      } catch (_) {
        /* ignore invalid URLs */
      }
    });
  }

  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(function () {
      markTypeSafeLinks(document);
    });
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      markTypeSafeLinks(document);
    });
  } else {
    markTypeSafeLinks(document);
  }
})();
