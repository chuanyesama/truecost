// Round-trip (做 T) calculator shared by index.html and calculator.html.
// Each page defines T, lang and fill(), merges CT into T, and calls initReview() before its first render.
const CT = {
  en: {
    c_try: "Start with an example:", c_p_good: "Sold high, bought back low", c_p_bad: "Got it backwards",
    c_p_zero: "Down to zero cost",
    c_s1: "Your first purchase", c_s1_hint: "How many shares you bought, and what you paid for each (any currency).",
    c_s2: "Each round trip", c_s2_hint: "You sold some shares, then later bought the same number back. Remove the rounds you didn't do.",
    c_s3: "Today's price", c_s3_hint: "Used to work out how far up or down you are.",
    c_round: "Round {n}",
    c_shares: "Shares", c_price: "Price per share",
    c_qty: "Shares sold", c_sell: "Sold at", c_buy: "Bought back at", c_add: "+ Add a round",
    c_now: "Price now", c_result: "Your result",
    c_ibkr: "Cost IBKR shows", c_real: "Your real cost",
    c_fine: "IBKR's cost assumes first-in, first-out lots; the real cost is the money still in the position ÷ shares held. Fees ignored. Your own statement gives the exact figures.",
    c_zero: "Zero cost", c_cta: "See it for your whole account →", mini_see: "Details ↓", mini_real: "real",
    say_zero: "Your round trips have already paid back the whole position, plus {extra}. The shares you hold now cost you nothing — but IBKR still shows {ibkr}.",
    say_lower: "Your round trips lowered your real cost by {diff} a share ({pct}). At {now}, IBKR shows {ibkrPct} — you're actually {realPct}.",
    say_higher: "These round trips raised your real cost by {diff} a share: you sold lower than you bought back. IBKR shows {ibkrPct}; you're actually {realPct}.",
    say_same: "No round trips yet — both costs are the same.",
  },
  zh: {
    c_try: "先点一个例子看看：", c_p_good: "高抛低吸成功", c_p_bad: "做 T 做反了", c_p_zero: "做到零成本",
    c_s1: "最初买入", c_s1_hint: "你第一次买了多少股、每股多少钱（任何币种都行）。",
    c_s2: "每一轮做 T", c_s2_hint: "先卖出一部分，之后再买回同样的股数。没做过的轮次点 × 删掉。",
    c_s3: "现在的股价", c_s3_hint: "用来算你现在赚了还是亏了多少。",
    c_round: "第 {n} 轮",
    c_shares: "股数", c_price: "每股价格",
    c_qty: "卖出股数", c_sell: "卖出价", c_buy: "买回价", c_add: "+ 再加一轮",
    c_now: "现价", c_result: "结果",
    c_ibkr: "IBKR 显示成本", c_real: "你的真实成本",
    c_fine: "IBKR 成本按先进先出计算；真实成本 = 仍投在这只股票里的钱 ÷ 持有股数。未计佣金。上传你的对账单可以看到精确数字。",
    c_zero: "零成本持股", c_cta: "看看你整个账户 →", mini_see: "看详情 ↓", mini_real: "真实",
    say_zero: "做 T 已经把本金全部赚回，还多赚 {extra}。你现在手里的股票等于零成本——IBKR 却仍显示成本 {ibkr}。",
    say_lower: "做 T 让你每股真实成本降低了 {diff}（{pct}）。按现价 {now}，IBKR 显示 {ibkrPct}，你实际是 {realPct}。",
    say_higher: "这几轮做 T 让每股真实成本升高了 {diff}：卖得比买回的还低。IBKR 显示 {ibkrPct}，你实际是 {realPct}。",
    say_same: "还没有做 T，两个成本一样。",
  },
};

let roundsEl;
function addRound(q, s, b) {
  const d = T[lang];
  const row = document.createElement("div");
  row.className = "round";
  row.innerHTML = `<div class="round-top"><span class="round-n"></span>
      <button class="x" type="button" aria-label="remove">×</button></div>
    <div class="round-grid">
      <div><label data-t="c_qty">${d.c_qty}</label><input type="number" min="0" step="1" value="${q}"></div>
      <div><label data-t="c_sell">${d.c_sell}</label><input type="number" min="0" step="0.01" value="${s}"></div>
      <div><label data-t="c_buy">${d.c_buy}</label><input type="number" min="0" step="0.01" value="${b}"></div>
    </div>`;
  row.querySelector(".x").addEventListener("click", () => { row.remove(); edited(); });
  row.querySelectorAll("input").forEach(i => i.addEventListener("input", edited));
  roundsEl.appendChild(row);
}

// examples a newcomer can click before typing anything
const PRESETS = {
  good: { n0: 100, p0: 100, now: 110, rounds: [[50, 120, 105], [50, 118, 102]] },
  bad:  { n0: 100, p0: 100, now: 100, rounds: [[50, 95, 104], [50, 98, 106]] },
  zero: { n0: 100, p0: 100, now: 120, rounds: [[100, 150, 110], [100, 140, 100], [100, 130, 95]] },
};
function usePreset(key) {
  const p = PRESETS[key];
  document.getElementById("n0").value = p.n0;
  document.getElementById("p0").value = p.p0;
  document.getElementById("now").value = p.now;
  roundsEl.innerHTML = "";
  p.rounds.forEach(r => addRound(...r));
  document.querySelectorAll("[data-preset]").forEach(c => c.classList.toggle("on", c.dataset.preset === key));
  calc();
  if (window.tcTrack) tcTrack("calc_preset", { mode: "review", preset: key });
}
// typing anything un-highlights the example, recalculates, and counts as using the calculator (once)
function edited() {
  document.querySelectorAll("[data-preset]").forEach(c => c.classList.remove("on"));
  calc();
  if (window.tcTrack) tcTrack("calc_use", { mode: "review" }, true);
}

function initReview() {
  roundsEl = document.getElementById("rounds");
  document.querySelectorAll("[data-preset]").forEach(c => c.addEventListener("click", () => usePreset(c.dataset.preset)));
  PRESETS.good.rounds.forEach(r => addRound(...r));
  document.getElementById("add").addEventListener("click", () => { addRound(50, 115, 104); edited(); });
  ["n0", "p0", "now"].forEach(id => document.getElementById(id).addEventListener("input", edited));

  // phones: show the mini result bar while the inputs are on screen and the full result isn't
  if (!("IntersectionObserver" in window)) return;
  const mini = document.getElementById("mini");
  const seen = { inputs: false, result: false };
  const update = () => mini.classList.toggle("show", seen.inputs && !seen.result);
  new IntersectionObserver(es => es.forEach(e => { seen.inputs = e.isIntersecting; update(); }),
    { threshold: 0.05 }).observe(roundsEl.closest(".panel"));
  new IntersectionObserver(es => es.forEach(e => { seen.result = e.intersectionRatio > 0.4; update(); }),
    { threshold: [0, 0.4, 1] }).observe(document.getElementById("calc-result"));
}

const num = v => { const x = parseFloat(v); return isFinite(x) ? x : 0; };
const fmt = v => v.toLocaleString(lang === "zh" ? "zh-CN" : "en-AU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const pct = v => (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + "%";

function calc() {
  const d = T[lang];
  const n0 = Math.max(0, num(document.getElementById("n0").value));
  const p0 = Math.max(0, num(document.getElementById("p0").value));
  const now = Math.max(0, num(document.getElementById("now").value));
  let lots = n0 > 0 ? [{ q: n0, p: p0 }] : [];
  let cash = n0 * p0;              // money still in the position
  let rounds = 0;
  roundsEl.querySelectorAll(".round-n").forEach((el, i) => el.textContent = fill(d.c_round, { n: i + 1 }));
  roundsEl.querySelectorAll(".round").forEach(row => {
    const [q, s, b] = [...row.querySelectorAll("input")].map(i => Math.max(0, num(i.value)));
    const held = lots.reduce((t, l) => t + l.q, 0);
    const sell = Math.min(q, held);
    if (sell <= 0) return;
    let left = sell;                 // first in, first out
    while (left > 1e-9 && lots.length) {
      const take = Math.min(left, lots[0].q);
      lots[0].q -= take; left -= take;
      if (lots[0].q <= 1e-9) lots.shift();
    }
    lots.push({ q: sell, p: b });
    cash += sell * (b - s);
    rounds++;
  });
  const shares = lots.reduce((t, l) => t + l.q, 0);
  const ibkr = shares ? lots.reduce((t, l) => t + l.q * l.p, 0) / shares : 0;
  const real = shares ? cash / shares : 0;

  document.getElementById("r_ibkr").textContent = fmt(ibkr);
  const rr = document.getElementById("r_real");
  rr.textContent = real <= 0 ? d.c_zero : fmt(real);
  rr.style.fontSize = real <= 0 ? "1.3rem" : "";
  document.getElementById("mini_ibkr").textContent = fmt(ibkr);
  document.getElementById("mini_real").textContent = real <= 0 ? d.c_zero : fmt(real);
  const ibkrPct = ibkr > 0 ? pct(now / ibkr - 1) : "—";
  const realPct = real > 0 ? pct(now / real - 1) : "—";
  document.getElementById("r_ibkr_pct").textContent = ibkr > 0 ? `${ibkrPct} @ ${fmt(now)}` : "";
  document.getElementById("r_real_pct").textContent = real > 0 ? `${realPct} @ ${fmt(now)}` : "";
  const top = Math.max(ibkr, real, 1e-9);
  document.getElementById("b_ibkr").style.width = `${Math.max(0, ibkr / top) * 100}%`;
  document.getElementById("b_real").style.width = `${Math.max(0, real / top) * 100}%`;

  let say;
  if (!rounds || Math.abs(real - ibkr) < 0.005) say = d.say_same;
  else if (real <= 0) say = fill(d.say_zero, { extra: fmt(-cash), ibkr: fmt(ibkr) });
  else if (real < ibkr) say = fill(d.say_lower, { diff: fmt(p0 - real), pct: pct(real / p0 - 1), now: fmt(now), ibkrPct, realPct });
  else say = fill(d.say_higher, { diff: fmt(real - p0), ibkrPct, realPct });
  document.getElementById("r_say").textContent = say;
}

