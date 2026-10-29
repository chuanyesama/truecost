// Anonymous usage counts for the static pages: no cookies, no personal data, nothing typed into
// the calculators. Same PostHog project as the app (a project key is meant to be public).
(function () {
  const KEY = "phc_xkEbroU79xzqYr27ovsFtwwYAA4o6aC8hM4TTd4ss389";
  const HOST = "https://eu.i.posthog.com";
  let id;
  try {
    id = sessionStorage.getItem("tc-id");
    if (!id) { id = "web-" + Math.random().toString(36).slice(2) + Date.now().toString(36); sessionStorage.setItem("tc-id", id); }
  } catch (e) { id = "web-anon"; }
  const qs = new URLSearchParams(location.search);
  const base = {
    page: location.pathname.includes("/app/") ? "app" : location.pathname.split("/").pop() || "index.html",
    ref: document.referrer ? new URL(document.referrer).hostname : "",
    utm: qs.get("utm_source") || qs.get("src") || "",
    mobile: matchMedia("(max-width: 760px)").matches,
    $process_person_profile: false,
  };
  const sent = new Set();
  window.tcTrack = function (event, props, once) {
    const tag = event + JSON.stringify(props || {});
    if (once && sent.has(tag)) return;
    sent.add(tag);
    if (/localhost|127\.0\.0\.1/.test(location.hostname)) return console.debug("[track]", event, props);
    const body = JSON.stringify({ api_key: KEY, event, distinct_id: id,
      properties: { ...base, lang: document.documentElement.lang, ...props } });
    try { navigator.sendBeacon(HOST + "/i/v0/e/", body) || fetch(HOST + "/i/v0/e/", { method: "POST", body, keepalive: true }); }
    catch (e) {}
  };
  addEventListener("load", () => tcTrack("site_view"));
  // every link to the app counts as a CTA click, a link to the Stripe checkout as a founder click;
  // data-where says which button
  document.addEventListener("click", e => {
    const a = e.target.closest("a.app-link, a[data-where]");
    if (!a) return;
    if (a.hostname === "buy.stripe.com")
      return tcTrack("founder_click", { where: a.dataset.where || "", plan: a.dataset.plan || "" });
    tcTrack("site_cta", { where: a.dataset.where || "", to: a.classList.contains("app-link") ? "app" : a.getAttribute("href") });
  });
})();
