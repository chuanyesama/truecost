// Cloudflare Worker: forwards Yahoo Finance's chart API to the TrueCost web app.
// Browsers can't call Yahoo directly (no CORS headers), so docs/app/app.js asks this worker instead
// (PRICE_PROXY). It only passes chart requests through, only for TrueCost's own pages, and caches
// each answer for five minutes. No statement data ever reaches it: just a ticker and a range.
const ORIGINS = ["https://chuanyesama.github.io", "http://localhost:8600"];
const CHART = /^\/v8\/finance\/chart\/[^/]+$/;

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get("Origin") || "";
    const cors = { "Access-Control-Allow-Origin": ORIGINS.includes(origin) ? origin : ORIGINS[0], "Vary": "Origin" };
    if (request.method === "OPTIONS") return new Response(null, { headers: { ...cors, "Access-Control-Allow-Methods": "GET" } });
    const url = new URL(request.url);
    if (request.method !== "GET" || !CHART.test(url.pathname) || (origin && !ORIGINS.includes(origin))) {
      return new Response("Not found", { status: 404, headers: cors });
    }
    const upstream = "https://query1.finance.yahoo.com" + url.pathname + url.search;
    const key = new Request(upstream);
    let res = await caches.default.match(key);
    if (!res) {
      const r = await fetch(upstream, { headers: { "User-Agent": "Mozilla/5.0 (TrueCost)" } });
      res = new Response(r.body, { status: r.status,
        headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=300" } });
      if (r.ok) ctx.waitUntil(caches.default.put(key, res.clone()));
    }
    const out = new Response(res.body, res);
    for (const [k, v] of Object.entries(cors)) out.headers.set(k, v);
    return out;
  },
};
