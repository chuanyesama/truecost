// TrueCost web app. The analysis runs in py-worker.js (Python in the browser); this file draws what
// app/web.py returns — a list of blocks per tab — and keeps the inputs in `state.p`. Changing an
// input re-runs the open tab, like a Streamlit rerun; morphdom patches the page so focus and
// open sections survive.
(function () {
  // A Cloudflare Worker that forwards Yahoo's chart API with CORS (see worker/). Empty: the price chart
  // shows the sample account's cached daily prices only.
  const PRICE_PROXY = "";

  // shown while the engine loads (the same words come from app/i18n.py once it has)
  const BOOT = {
    en: {
      title: "Did your IBKR profit come from trading — or from the exchange rate?",
      sub: "Upload your IBKR statement and see, in your home currency: where your money really came from, your true cost after trading around positions, and how much fees are eating.",
      pills: ["💱 Trading vs currency", "🎯 Real cost after round trips", "💸 Every fee counted", "📈 Charts with your buys & sells"],
      drop: "Drop your IBKR Activity Statement (CSV) here",
      private: "🔒 Read inside your browser — your statement never leaves your device. Free, no sign-up.",
      upload: "Upload statement", settings: "Settings", home: "Website",
      booting: "Starting TrueCost…",
      boot_note: "First visit: about 10 seconds to load the calculator into your browser. After that it opens in a moment.",
      python: "Loading Python…", packages: "Loading the data tools…", engine: "Loading TrueCost…", ready: "Analysing the sample account…",
      failed: "TrueCost couldn't start in this browser. Check your connection and reload the page.",
      working: "Working…", reading: "Reading your statement…",
    },
    zh: {
      title: "你在 IBKR 赚的钱，是交易赚的，还是汇率给的？",
      sub: "上传 IBKR 对账单，用你的本币看清：钱到底从哪来、做 T 之后的真实成本、佣金吃掉了多少。",
      pills: ["💱 交易 vs 汇率", "🎯 做 T 后的真实成本", "💸 每一笔费用", "📈 K 线上的买卖点"],
      drop: "把 IBKR 活动对账单（CSV）拖到这里",
      private: "🔒 在你的浏览器里读取，对账单不会离开你的设备。免费，不用注册。",
      upload: "上传对账单", settings: "设置", home: "官网",
      booting: "TrueCost 启动中…",
      boot_note: "第一次打开大约需要 10 秒，把计算引擎加载到你的浏览器里；之后再打开会快很多。",
      python: "正在加载 Python…", packages: "正在加载数据工具…", engine: "正在加载 TrueCost…", ready: "正在分析示例账户…",
      failed: "TrueCost 没能在这个浏览器里启动。请检查网络后刷新页面。",
      working: "计算中…", reading: "正在读取对账单…",
    },
  };
  const STEPS = { python: 25, packages: 55, engine: 85, ready: 95 };
  const TABS = ["home", "overview", "cost", "chart", "rounds", "calc", "fees", "style", "fx", "trades"];

  const $ = (id) => document.getElementById(id);
  const qs = new URLSearchParams(location.search);
  const state = {
    lang: (() => {
      const q = qs.get("lang");
      if (q === "zh" || q === "en") return q;
      try { const s = localStorage.getItem("tc-lang"); if (s === "zh" || s === "en") return s; } catch (e) {}
      return (navigator.language || "").toLowerCase().startsWith("zh") ? "zh" : "en";
    })(),
    tab: TABS.includes(location.hash.slice(1)) ? location.hash.slice(1) : "home",
    p: {},          // input values by widget id, sent to Python
    ui: {},         // purely local state: picked plan, opened offer, sent forms
    method: "lot_ibkr", source: "ecb",
    info: null, page: null, blocks: [], error: null, ready: false,
  };
  const b = (k) => BOOT[state.lang][k];

  // ---------- engine ----------
  const worker = new Worker("py-worker.js");
  const pending = new Map();
  let seq = 0;
  worker.onmessage = (e) => {
    const d = e.data;
    if (d.progress) return progress(d.progress);
    const cb = pending.get(d.id);
    pending.delete(d.id);
    if (d.error) cb.reject(new Error(d.error)); else cb.resolve(JSON.parse(d.result));
  };
  worker.onerror = () => bootFailed();
  function call(fn, args, file) {
    return new Promise((resolve, reject) => {
      const id = ++seq;
      pending.set(id, { resolve, reject });
      worker.postMessage({ id, fn, args, file }, file ? [file] : []);
    });
  }
  function progress(step) {
    if (state.ready) return;
    $("boot-bar").style.width = (STEPS[step] || 5) + "%";
    $("boot").querySelector("b").textContent = b(step) || b("booting");
  }
  function bootFailed() {
    $("boot").innerHTML = `<div class="msg error">${esc(b("failed"))}</div>`;
    tcTrack("app_boot_failed", {}, true);
  }

  // ---------- helpers ----------
  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  marked.use({ renderer: { html: (h) => esc(typeof h === "string" ? h : h.text) } });  // no raw HTML from data
  const md = (s) => marked.parse(String(s ?? ""));
  const mdInline = (s) => marked.parseInline(String(s ?? ""));
  const help = (tip) => tip ? `<button type="button" class="help" data-tip="${esc(tip)}" aria-label="${esc(tip)}">?</button>` : "";
  function bucket(n) {
    for (const [hi, label] of [[50, "<50"], [200, "50-200"], [1000, "200-1000"], [5000, "1000-5000"]]) if (n < hi) return label;
    return "5000+";
  }
  function fmtNum(v, decimals) {
    if (v === null || v === undefined || v === "") return "";
    return decimals === null || decimals === undefined ? String(+(+v).toPrecision(10)) : (+v).toFixed(decimals);
  }

  // ---------- blocks -> HTML ----------
  let figs = [], downloads = [];
  function blocks(list) { return (list || []).map(block).join(""); }
  function block(x) {
    switch (x.k) {
      case "h": return `<h${x.level}>${esc(x.text)}</h${x.level}>`;
      case "md": return `<div class="md">${md(x.md)}</div>`;
      case "cap": return `<div class="cap md">${md(x.md)}</div>`;
      case "msg": return `<div class="msg ${x.level}">${md(x.md)}</div>`;
      case "hr": return "<hr>";
      case "metrics": return `<div class="metrics${x.stack ? " stack" : ""}">${x.items.map(metric).join("")}</div>`;
      case "cols": return `<div class="cols" style="grid-template-columns:${x.widths.map((w) => w + "fr").join(" ")}">${
        x.cols.map((c) => `<div>${blocks(c)}</div>`).join("")}</div>`;
      case "card": return `<div class="card">${blocks(x.blocks)}</div>`;
      case "expander": return `<details class="exp" id="exp-${esc(slug(x.title))}"><summary>${esc(x.title)}</summary><div class="blocks">${blocks(x.blocks)}</div></details>`;
      case "table": return table(x);
      case "chart": figs.push(x.fig); return `<div class="chart" id="chart-${figs.length - 1}"></div>`;
      case "select": return `<div class="field field-sm"><label>${esc(x.label)}${help(x.help)}</label><select data-w="${esc(x.id)}">${
        x.options.map(([v, l]) => `<option value="${esc(v)}"${v === x.value ? " selected" : ""}>${esc(l)}</option>`).join("")}</select></div>`;
      case "seg": return `<div class="field">${x.label ? `<label>${esc(x.label)}</label>` : ""}<div class="seg">${
        x.options.map(([v, l]) => `<button type="button" data-seg="${esc(x.id)}" data-v="${esc(v)}" class="${v === x.value ? "on" : ""}">${esc(l)}</button>`).join("")}</div></div>`;
      case "number": return `<div class="field"><label>${esc(x.label)}${help(x.help)}</label><input type="text" inputmode="decimal" autocomplete="off" data-num="${esc(x.id)}" value="${esc(fmtNum(x.value, x.decimals))}" placeholder="${esc(x.placeholder || "")}"></div>`;
      case "slider": return `<div class="field"><label>${esc(x.label)} <span class="range-val">${(+x.value).toFixed(2)}</span></label><input type="range" data-range="${esc(x.id)}" min="${x.min}" max="${x.max}" step="${x.step}" value="${x.value}"></div>`;
      case "grid": return grid(x);
      case "multi": return `<div class="field"><label>${esc(x.label)}</label><div class="chips">${
        x.options.map(([v, l]) => `<button type="button" class="chip${x.value.includes(v) ? " on" : ""}" data-multi="${esc(x.id)}" data-v="${esc(v)}">${esc(l)}</button>`).join("")}</div></div>`;
      case "download": downloads.push(x); return `<button type="button" class="btn btn-ghost btn-sm" data-dl="${downloads.length - 1}">⬇ ${esc(x.label)}</button>`;
      case "founder": return founder(x);
      case "offer": return offer(x);
      case "feedback": return feedback(x);
      case "survey": return survey(x);
      default: return "";
    }
  }
  const slug = (s) => String(s).replace(/[^\w一-鿿]+/g, "-").slice(0, 40);
  function metric(m) {
    let delta = "";
    if (m.delta) {
      const up = !m.delta.startsWith("-") && !m.delta.startsWith("−");
      const cls = m.delta_color === "off" ? "off" : (up !== (m.delta_color === "inverse") ? "up" : "down");
      delta = `<div class="delta ${cls}">${m.delta_color === "off" ? "" : up ? "↑ " : "↓ "}${esc(m.delta)}</div>`;
    }
    return `<div class="metric"><div class="lab">${esc(m.label)}${help(m.help)}</div><div class="val">${esc(m.value)}</div>${delta}</div>`;
  }
  function table(x) {
    const head = x.cols.map((c, i) => `<th class="${x.right[i] ? "r" : ""}">${esc(c)}</th>`).join("");
    const rows = x.rows.map((r) => `<tr>${r.map((v, i) => `<td class="${x.right[i] ? "r" : ""}">${esc(v)}</td>`).join("")}</tr>`).join("");
    const max = x.max_rows ? ` style="max-height:${38 * (x.max_rows + 1) + 4}px"` : "";
    return `<div class="tbl"${max}><table><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }
  function grid(x) {
    const rows = (x.rows || []).map((r, i) => `<tr>${x.cols.map((_, j) =>
      `<td><input type="text" inputmode="decimal" autocomplete="off" data-grid="${esc(x.id)}" data-r="${i}" data-c="${j}" value="${esc(fmtNum(r[j], x.decimals[j]))}"></td>`).join("")
      }<td><button type="button" class="x" data-grid-del="${esc(x.id)}" data-r="${i}" aria-label="remove">×</button></td></tr>`).join("");
    return `<div class="grid-edit"><table><thead><tr>${x.cols.map((c) => `<th>${esc(c)}</th>`).join("")}<th></th></tr></thead><tbody>${rows}</tbody></table>
      <button type="button" class="add" data-grid-add="${esc(x.id)}">+</button></div>`;
  }

  // offers and forms: answered in the page, counted in analytics
  function founder(x) {
    const picked = state.ui["founder_" + x.where];
    const pl = x.plans.find((p) => p.plan === picked);
    return `<div class="form"><div class="plan-btns">${x.plans.map((p) =>
      `<button type="button" class="btn ${p.primary ? "btn-primary" : "btn-ghost"}" data-founder="${esc(x.where)}" data-plan="${esc(p.plan)}">${esc(p.label)}</button>`).join("")}</div>${
      pl ? `<div class="msg info">${md(pl.terms)}</div><div class="plan-btns"><a class="btn btn-primary" href="${esc(pl.url)}?client_reference_id=app_${esc(x.where)}_${esc(pl.plan)}">${esc(x.pay)}</a></div>` : ""}</div>`;
  }
  function offer(x) {
    const key = "offer_" + x.where, st = state.ui[key];
    let more = "";
    if (st === "sent") more = `<div class="msg success">${esc(x.thanks)}</div>`;
    else if (st) more = `<div class="msg info">${md(x.soon)}</div>
      <div class="field"><label>${esc(x.email)}</label><input type="email" data-keep id="${key}-email" placeholder="you@example.com"></div>
      ${st === "bad" ? `<div class="msg warning">${esc(x.bad_email)}</div>` : ""}
      <button type="button" class="btn btn-ghost btn-sm" data-offer-send="${esc(x.where)}">${esc(x.notify)}</button>`;
    return `<div class="form"><div class="plan-btns"><button type="button" class="btn btn-ghost" data-offer="${esc(x.where)}">${esc(x.label)}</button></div>${more}</div>`;
  }
  function feedback(x) {
    const key = "feedback_" + x.where;
    return `<div class="form">
      <div class="field"><label>${esc(x.label)}</label><textarea data-keep id="${key}-text" maxlength="1000" placeholder="${esc(x.placeholder)}"></textarea></div>
      <div class="field"><label>${esc(x.email)}</label><input type="email" data-keep id="${key}-email" placeholder="you@example.com"></div>
      <button type="button" class="btn btn-primary btn-sm" data-feedback="${esc(x.where)}">${esc(x.send)}</button>
      ${state.ui[key] ? `<div class="msg success">${esc(x.thanks)}</div>` : ""}</div>`;
  }
  function survey(x) {
    if (state.ui.survey_done) return `<div class="msg success">${esc(x.thanks)}</div>`;
    const q = x.questions.map((q) => {
      const name = "sv-" + q.id;
      if (q.type === "radio") return `<div class="field"><label>${esc(q.label)}</label><div class="radio${q.horizontal ? " h" : ""}">${
        q.options.map(([v, l]) => `<label><input type="radio" data-keep name="${name}" id="${name}-${esc(v)}" value="${esc(v)}"> <span>${esc(l)}</span></label>`).join("")}</div></div>`;
      if (q.type === "steps") return `<div class="field"><label>${esc(q.label)}</label><div class="radio h">${
        q.options.map(([v, l]) => `<label><input type="radio" data-keep name="${name}" id="${name}-${v}" value="${v}"${v === q.value ? " checked" : ""}> <span>${esc(l)}</span></label>`).join("")}</div></div>`;
      if (q.type === "multi") return `<div class="field"><label>${esc(q.label)}</label><div class="radio">${
        q.options.map(([v, l]) => `<label><input type="checkbox" data-keep name="${name}" id="${name}-${esc(v)}" value="${esc(v)}"> <span>${esc(l)}</span></label>`).join("")}</div></div>`;
      if (q.type === "email") return `<div class="field"><label>${esc(q.label)}</label><input type="email" data-keep id="${name}" placeholder="you@example.com"></div>`;
      return `<div class="field"><label>${esc(q.label)}</label><textarea data-keep id="${name}" maxlength="1000" placeholder="${esc(q.placeholder || "")}"></textarea></div>`;
    }).join("");
    return `<div class="form" id="survey" data-base="${esc(x.base)}" data-demo="${x.demo}">${q}<button type="button" class="btn btn-primary" data-survey>${esc(x.send)}</button></div>`;
  }

  // ---------- charts ----------
  function themed(fig) {
    const cs = getComputedStyle(document.documentElement);
    const v = (n) => cs.getPropertyValue(n).trim();
    const tokens = { "@pos": v("--pos"), "@neg": v("--neg"), "@ink2": v("--muted"), "@grid": v("--line") };
    const swap = (o) => Array.isArray(o) ? o.map(swap) : o && typeof o === "object"
      ? Object.fromEntries(Object.entries(o).map(([k, x]) => [k, swap(x)])) : (typeof o === "string" && tokens[o]) || o;
    const small = innerWidth < 640, size = small ? 12 : 14;
    const data = swap(fig.data).map((t) => {
      if (["bar", "scatter", "waterfall"].includes(t.type)) t.cliponaxis = false;
      if (t.text && !(t.textfont && t.textfont.size)) t.textfont = { ...(t.textfont || {}), size };
      return t;
    });
    const layout = swap(fig.layout);
    Object.assign(layout, {
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: "Inter, 'PingFang SC', 'Microsoft YaHei', sans-serif", size, color: v("--ink") },
      hoverlabel: { font: { size } },
      height: small ? Math.min(layout.height || 420, 520) : layout.height,
    });
    if (layout.title) layout.title.font = { size: size + 3 };
    for (const ax of new Set(["xaxis", "yaxis", ...Object.keys(layout).filter((k) => /^[xy]axis\d*$/.test(k))])) {
      layout[ax] = { gridcolor: v("--line"), zerolinecolor: v("--muted"), automargin: true, ...(layout[ax] || {}) };
    }
    if (small && layout.margin) layout.margin = { ...layout.margin, r: Math.min(layout.margin.r || 10, 50) };
    return [data, layout, { displayModeBar: false, responsive: true }];
  }
  function drawCharts(force) {
    if (!window.Plotly) return setTimeout(() => drawCharts(force), 200);
    document.querySelectorAll("#content .chart").forEach((div) => {
      const fig = figs[+div.id.split("-")[1]];
      if (!fig) return;
      const key = JSON.stringify(fig);
      if (!force && div._key === key) return;
      div._key = key;
      const args = themed(fig);
      div.style.height = (args[1].height || 420) + 14 + "px";  // responsive charts fill their box: give it the height
      Plotly.react(div, ...args);
    });
  }

  // ---------- drawing ----------
  function morph(el, html) {
    morphdom(el, `<${el.tagName.toLowerCase()} class="${el.className}" id="${el.id}">${html}</${el.tagName.toLowerCase()}>`, {
      onBeforeElUpdated(from, to) {
        if (from.classList.contains("chart")) return false;  // Plotly owns its DOM; redrawn in drawCharts
        if (from.tagName === "DETAILS") to.open = from.open;
        if (from.hasAttribute("data-keep")) {  // what the viewer typed or ticked in a form
          if (from.type === "radio" || from.type === "checkbox") to.checked = from.checked; else to.value = from.value;
        } else if (from === document.activeElement && /^(INPUT|TEXTAREA|SELECT)$/.test(from.tagName)) {
          if (from.type === "range") to.value = from.value; else return false;  // keep the field being typed in
        }
        return true;
      },
    });
  }
  function drawContent() {
    figs = []; downloads = [];
    const err = state.error ? `<div class="msg error">${md(state.error)}</div>` : "";
    morph($("content"), err + blocks(state.blocks));
    drawCharts(false);
  }
  function drawChrome() {
    document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
    document.title = state.lang === "zh" ? "TrueCost — 用本币看清你在 IBKR 的真实盈亏" : "TrueCost — your real IBKR profit, in your own currency";
    $("lang").textContent = state.lang === "zh" ? "English" : "中文";
    const pg = state.page, tx = pg ? pg.text : null;
    document.querySelectorAll("[data-b]").forEach((el) => { el.textContent = b(el.dataset.b) || ""; });
    if (tx) {
      document.querySelector('#hero h1').textContent = tx.hero_title;
      document.querySelector('#hero .lead').textContent = tx.hero_sub;
      document.querySelector('#drop b').textContent = tx.hero_upload;
      document.querySelector('#hero .drop-note').textContent = tx.hero_private;
      $("scroll-note").innerHTML = md(tx.hero_or);
      $("foot-note").textContent = tx.disclaimer;
    }
    $("pills").innerHTML = (tx ? tx.hero_pills : b("pills")).map((p) => `<li>${esc(p)}</li>`).join("");
    const demo = !pg || pg.demo;
    $("hero").hidden = !demo;
    $("scroll-note").hidden = !pg;
    $("head").hidden = demo;
    if (pg && !demo) {
      morph($("head"), `<div class="head-row"><h1>TrueCost</h1><div class="head-links">
          <label class="btn btn-ghost btn-sm" for="file">${esc(tx.web_upload_other)}</label>
          <button type="button" class="btn btn-ghost btn-sm" id="to-sample">${esc(tx.web_sample)}</button></div></div>
        <div class="blocks" style="margin-top:12px">${blocks(pg.header)}</div>`);
    }
    if (!pg) return;
    $("tabbar").hidden = false;
    $("tabs").innerHTML = pg.tabs.map(([k, name]) =>
      `<button type="button" role="tab" data-tab="${k}" class="${k === state.tab ? "on" : ""}" aria-selected="${k === state.tab}">${esc(name)}</button>`).join("");
    $("settings-btn").hidden = false;
    $("settings").innerHTML = blocks(pg.settings).replace(/field field-sm/g, "field");
    $("pro").innerHTML = `<div class="card blocks"><h4>⭐ ${esc(tx.pro_title)}</h4><div class="cap">${esc(tx.pro_pitch)}</div>${blocks(pg.pro)}
      <div class="cap md">${md(tx.sidebar_footer)}</div></div>`;
  }

  // ---------- reruns ----------
  let running = false, dirty = false, dirtyPage = false, busyTimer = null;
  const barCache = new Map();
  function rerun(withPage) {
    dirty = true;
    dirtyPage = dirtyPage || !!withPage;
    if (running) return;
    running = true;
    busyTimer = setTimeout(() => { $("busy-text").textContent = b("working"); $("busy").hidden = false; }, 400);
    (async () => {
      try {
        while (dirty) {
          dirty = false;
          const wp = dirtyPage;
          dirtyPage = false;
          if (wp || !state.page) { state.page = await call("page", { lang: state.lang, p: state.p }); drawChrome(); }
          const name = state.tab;
          const bars = name === "chart" ? await chartBars() : null;
          const out = await call("tab", { name, lang: state.lang, p: state.p, bars });
          if (name !== state.tab) { dirty = true; continue; }
          state.blocks = out;
          drawContent();
        }
      } catch (e) {
        console.error(e);
        state.blocks = [{ k: "msg", level: "error", md: String(e.message || e) }];
        drawContent();
      } finally {
        running = false;
        clearTimeout(busyTimer);
        $("busy").hidden = true;
      }
    })();
  }
  let typing = null;
  const rerunSoon = () => { clearTimeout(typing); typing = setTimeout(() => rerun(false), 180); };

  async function chartBars() {
    if (!PRICE_PROXY) return null;
    const tg = await call("chart_target", { lang: state.lang, p: state.p });
    if (!tg.query) return null;
    if (barCache.has(tg.query)) return barCache.get(tg.query);
    let text = "";
    try {
      const r = await fetch(PRICE_PROXY + tg.query);
      if (r.ok) text = await r.text();
    } catch (e) {}
    if (text) barCache.set(tg.query, text);
    return text;
  }

  // ---------- statements ----------
  async function analyse(file) {
    $("busy-text").textContent = b("reading");
    $("busy").hidden = false;
    try {
      const info = await call("load_file", { path: file ? "/tmp/statement.csv" : null, method: state.method, source: state.source }, file);
      if (!info.ok) {
        tcTrack("statement_error", { error: info.error });
        state.error = state.page ? state.page.text.parse_error : "⚠️";
        drawContent();
        scrollTo({ top: 0, behavior: "smooth" });
        return;
      }
      state.error = null;
      state.info = info;
      state.p = {};
      state.source = info.source;
      if (file) {
        tcTrack("statement_uploaded", { base: info.base, markets: info.markets, trades: bucket(info.trades), reconciles: info.reconciles });
        if (state.tab === "chart" && !PRICE_PROXY) state.tab = "home";
      }
      rerun(true);
      scrollTo({ top: 0, behavior: "smooth" });
    } finally {
      $("busy").hidden = true;
    }
  }
  async function openFile(f) {
    if (!f) return;
    analyse(await f.arrayBuffer());
  }

  // ---------- events ----------
  $("file").addEventListener("change", (e) => { openFile(e.target.files[0]); e.target.value = ""; });
  const drop = $("drop");
  ["dragenter", "dragover"].forEach((ev) => document.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => document.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  document.addEventListener("drop", (e) => openFile(e.dataTransfer && e.dataTransfer.files[0]));

  $("lang").addEventListener("click", () => {
    state.lang = state.lang === "zh" ? "en" : "zh";
    try { localStorage.setItem("tc-lang", state.lang); } catch (e) {}
    const url = new URL(location.href);
    url.searchParams.set("lang", state.lang);
    history.replaceState(null, "", url);
    tcTrack("lang_switch", { to: state.lang, page: "app" });
    drawChrome();
    if (state.ready) rerun(true);
  });
  $("theme").addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("tc-theme", dark ? "light" : "dark"); } catch (e) {}
    themeIcon();
    drawCharts(true);
  });
  function themeIcon() {
    const th = document.documentElement.dataset.theme;
    const dark = th ? th === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    $("theme").textContent = dark ? "☀️" : "🌙";
  }
  $("settings-btn").addEventListener("click", () => {
    const open = $("settings").hidden;
    $("settings").hidden = !open;
    $("settings-btn").setAttribute("aria-expanded", open);
  });
  $("settings").addEventListener("change", (e) => {
    const w = e.target.dataset.w;
    if (w === "method") state.method = e.target.value;
    if (w === "source") state.source = e.target.value;
    tcTrack("setting", { which: w, value: e.target.value });
    call("reanalyse", { method: state.method, source: state.source }).then((info) => {
      if (!info.ok) return;
      state.info = info;
      state.source = info.source;
      rerun(true);
    });
  });
  $("tabs").addEventListener("click", (e) => {
    const k = e.target.closest("[data-tab]");
    if (!k || k.dataset.tab === state.tab) return;
    state.tab = k.dataset.tab;
    history.replaceState(null, "", "#" + state.tab);
    document.querySelectorAll("#tabs button").forEach((x) => x.classList.toggle("on", x === k));
    const top = $("tabbar").getBoundingClientRect().top + scrollY - 64;
    if (scrollY > top) scrollTo({ top });
    tcTrack("app_tab", { tab: state.tab }, true);
    rerun(false);
  });
  document.addEventListener("click", (e) => {
    if (e.target.id === "to-sample") return analyse(null);
    const t = e.target.closest("button, a");
    if (!t) { if (!e.target.closest("#settings, #settings-btn")) $("settings").hidden = true; return; }
    const d = t.dataset;
    if (d.seg) { state.p[d.seg] = d.v; calcUsed(d.seg); return rerun(false); }
    if (d.multi) {
      const cur = state.p[d.multi] || [];
      state.p[d.multi] = cur.includes(d.v) ? cur.filter((x) => x !== d.v) : [...cur, d.v];
      return rerun(false);
    }
    if (d.gridAdd) { gridRows(d.gridAdd).push([0, 0, 0]); return rerun(false); }
    if (d.gridDel) { gridRows(d.gridDel).splice(+d.r, 1); return rerun(false); }
    if (d.dl) {
      const x = downloads[+d.dl];
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob(["﻿" + x.text], { type: "text/csv;charset=utf-8" }));
      a.download = x.filename;
      a.click();
      return setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    }
    if (d.founder) {
      state.ui["founder_" + d.founder] = d.plan;
      tcTrack("founder_click", { where: d.founder, plan: d.plan, base: state.info && state.info.base, demo: !state.info || state.info.demo });
      return redraw();
    }
    if (d.offer) {
      const price = state.page && blocksFind("offer");
      state.ui["offer_" + d.offer] = state.ui["offer_" + d.offer] || "open";
      tcTrack("paid_report_click", { where: d.offer, base: state.info && state.info.base, demo: !state.info || state.info.demo, price: price && price.price });
      return redraw();
    }
    if (d.offerSend) {
      const email = ($(`offer_${d.offerSend}-email`) || {}).value || "";
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) { state.ui["offer_" + d.offerSend] = "bad"; return redraw(); }
      tcTrack("waitlist_signup", { product: "report", where: d.offerSend, base: state.info && state.info.base, email: email.trim() });
      state.ui["offer_" + d.offerSend] = "sent";
      return redraw();
    }
    if (d.feedback) {
      const text = $(`feedback_${d.feedback}-text`), email = $(`feedback_${d.feedback}-email`);
      if (!text.value.trim()) return;
      tcTrack("feedback", { text: text.value.trim(), email: email.value.trim(), where: d.feedback, lang: state.lang });
      text.value = ""; email.value = "";
      state.ui["feedback_" + d.feedback] = true;
      return redraw();
    }
    if (t.hasAttribute("data-survey")) {
      const f = $("survey");
      const val = (n) => { const x = f.querySelector(`[name="sv-${n}"]:checked`); return x ? x.value : null; };
      tcTrack("survey", {
        pay: val("pay"), price_aud: +val("price_aud"), report: val("report"),
        ai: [...f.querySelectorAll('[name="sv-ai"]:checked')].map((x) => x.value),
        ai_text: $("sv-ai_text").value.trim(), other: $("sv-other").value.trim(), email: $("sv-email").value.trim(),
        base: f.dataset.base, demo: f.dataset.demo === "true", lang: state.lang,
      });
      state.ui.survey_done = true;
      return redraw();
    }
  });
  function blocksFind(kind) {
    let found = null;
    const walk = (list) => (list || []).forEach((x) => { if (x.k === kind) found = found || x; walk(x.blocks); (x.cols || []).forEach(walk); });
    walk(state.blocks);
    return found;
  }
  function gridRows(id) {
    if (!Array.isArray(state.p[id])) {
      const g = (function find(list) { for (const x of list || []) { if (x.k === "grid" && x.id === id) return x; const y = find(x.blocks) || (x.cols || []).map(find).find(Boolean); if (y) return y; } return null; })(state.blocks);
      state.p[id] = g ? g.rows.map((r) => [...r]) : [];
    }
    return state.p[id];
  }
  function redraw() { drawContent(); if (state.page) drawChrome(); }
  function calcUsed(id) { if (/^tcr?_/.test(id) && state.tab === "calc") tcTrack("app_calc", { mode: state.p.tc_mode || "plan" }, true); }

  const content = $("content");
  content.addEventListener("change", (e) => {
    const w = e.target.dataset.w;
    if (w) { state.p[w] = e.target.value; rerun(false); }
  });
  content.addEventListener("input", (e) => {
    const el = e.target, d = el.dataset;
    const num = (s) => { s = s.replace(/[,\s]/g, ""); return s === "" ? null : isNaN(+s) ? undefined : +s; };
    if (d.num) {
      const v = num(el.value);
      if (v === undefined) return;
      state.p[d.num] = v;
      calcUsed(d.num);
      return rerunSoon();
    }
    if (d.range) {
      state.p[d.range] = +el.value;
      el.closest(".field").querySelector(".range-val").textContent = (+el.value).toFixed(2);
      calcUsed(d.range);
      return rerun(false);
    }
    if (d.grid) {
      const v = num(el.value);
      if (v === undefined) return;
      gridRows(d.grid)[+d.r][+d.c] = v === null ? 0 : v;
      calcUsed(d.grid);
      return rerunSoon();
    }
  });
  // ---------- start ----------
  themeIcon();
  drawChrome();
  call("load_file", { path: null, method: state.method, source: state.source })
    .then((info) => {
      state.info = info;
      state.ready = true;
      $("boot").hidden = true;
      tcTrack("app_open", { lang: state.lang, demo: true, src: qs.get("src") || qs.get("utm_source") || "" }, true);
      rerun(true);
    })
    .catch((e) => { console.error(e); bootFailed(); });
})();
