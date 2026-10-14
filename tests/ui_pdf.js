// Browser test of the "Relevant Technical Data from the PDF" section.  Needs Playwright (Chromium):
//   NODE_PATH=$(npm root -g) node tests/ui_pdf.js
const { chromium } = require("playwright");
const path = require("path");
const PAGE = "file://" + path.join(__dirname, "..", "index.html");
const CASES = [
  { name: "methane accumulation (coal)", q: "An underground coal mine development heading experiences an auxiliary ventilation fan failure, allowing methane to accumulate near the working face and creating a potential firedamp explosion hazard.", place: "Below Ground", mt: "Coal",
    has: ["M01", "M02", "M08"], not: ["D02", "B01"], calcs: ["methanePosition", "gasEmissionIndex", "layeringIndex"] },
  { name: "coal dust (coal)", q: "Dry coal dust accumulates along underground coal mine roadways and is dispersed into the air during coal transport, creating conditions for a potential coal-dust explosion.", place: "Below Ground", mt: "Coal",
    has: ["D01", "D02", "D03"], not: ["M11", "B01"], calcs: [] },
  { name: "metal-ore processing dust", q: "Fine combustible dust accumulates around equipment in a metal-ore processing plant where an ignition source may be present, creating a potential dust-fire or explosion hazard.", place: "", mt: "Metal ore",
    has: ["D01"], not: ["D02", "M01", "M11", "B01"], calcs: [] },
  { name: "stone-dust barrier", q: "Stone dust barrier shelves in a coal mine roadway were found with little dust before a coal dust explosion risk inspection", place: "Below Ground", mt: "Coal",
    has: ["B01", "B04", "B06", "B09", "B11"], not: [], calcs: null },
  { name: "granite quarry misfire", q: "Drilling holes on a bench near an old blasted area in an opencast granite quarry where a misfire may remain", place: "Opencast", mt: "",
    section: false },
  { name: "stated methane reading", q: "Gas test showed 2.5% methane accumulating at the face of a coal mine heading after the fan stopped", place: "Below Ground", mt: "Coal",
    has: ["M01"], calcs: ["methanePosition", "gasEmissionIndex", "layeringIndex"], prefill: "2.5" }
];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 1400 } });
  const errs = []; p.on("pageerror", e => errs.push(e.message));
  await p.goto(PAGE); await p.waitForTimeout(300);
  let fail = 0; const ok = (c, m) => { if (!c) { fail++; console.log("  FAIL", m); } };
  for (const c of CASES) {
    await p.click("#brandBtn");
    await p.fill("#q", c.q); await p.selectOption("#place", c.place); await p.selectOption("#mt", c.mt);
    await p.click("#go"); await p.waitForSelector("#out .xpanel", { timeout: 5000 });
    const r = await p.evaluate(() => ({ sec: !!document.getElementById("pdt"), h: document.querySelector("#pdt h2")?.textContent,
      ids: [...document.querySelectorAll("#pdt .pdi")].map(e => e.dataset.pid), calcs: [...document.querySelectorAll("#pdt .pcalc")].map(e => e.dataset.calc),
      states: [...document.querySelectorAll("#pdt .pcalc")].map(e => e.dataset.state), pages: [...document.querySelectorAll("#pdt .pdi .pp")].every(e => /^PDF p\.\d+ \(printed \d+\/17/.test(e.textContent)),
      tags: [...document.querySelectorAll("#pdt .pdi .ptag")].map(e => e.textContent), out: [...document.querySelectorAll("#pdt .pc-out")].map(e => e.textContent) }));
    console.log(`${c.name}: section=${r.sec} items=${r.ids.join(",")} calcs=${r.calcs.join(",")} states=${r.states.join(",")}`);
    if (c.section === false) { ok(!r.sec, "section should be absent"); continue; }
    ok(r.sec && r.h === "Relevant Technical Data from the PDF", "section title");
    ok(r.pages, "every item cites a PDF page");
    ok(r.tags.every(t => /Reference value|Design specification|Calculation|Flagged for review/.test(t)), "type labels");
    for (const id of c.has || []) ok(r.ids.includes(id), "has " + id);
    for (const id of c.not || []) ok(!r.ids.includes(id), "not " + id);
    if (c.calcs) ok(JSON.stringify(r.calcs) === JSON.stringify(c.calcs), "calculators " + r.calcs);
    if (!c.prefill) ok(r.states.every(s => s === "missing"), "no calculation without inputs");
    if (c.prefill) {
      ok(r.states[0] === "ok" && /2\.5 % CH₄/.test(r.out[0]) && /not a prediction/.test(r.out[0]), "stated reading computed with caveat");
      ok(await p.$eval('#pdt .pcalc[data-calc="methanePosition"] .partial', e => /measured reading/.test(e.textContent)), "stated-value warning");
    }
  }
  // live calculators on the methane case
  await p.click("#brandBtn"); await p.fill("#q", CASES[0].q); await p.selectOption("#place", "Below Ground"); await p.selectOption("#mt", "Coal");
  await p.click("#go"); await p.waitForSelector("#pdt");
  const fill = async (calc, vals) => { const box = `#pdt .pcalc[data-calc="${calc}"]`; await p.evaluate(s => { document.querySelector(s).open = true; }, box);
    for (const [k, v] of Object.entries(vals)) await p.fill(`${box} input[data-k="${k}"]`, String(v));
    return p.$eval(box, e => ({ state: e.dataset.state, text: e.querySelector(".pc-out").textContent })); };
  let r = await fill("gasEmissionIndex", { c: 0.5, Q: 2000, O: 1000 }); ok(r.state === "missing" && /K \(–\)/.test(r.text), "GEI waits for K: " + r.text);
  r = await fill("gasEmissionIndex", { K: 2 }); ok(r.state === "ok" && /q = 7\.2 m³ CH₄\/t → Degree II/.test(r.text), "GEI result: " + r.text);
  r = await fill("gasEmissionIndex", { K: "0.5" }); ok(r.state === "invalid" && /cannot be below 1/.test(r.text), "GEI invalid K");
  r = await fill("layeringIndex", { v: 1, c: 3, F: 1 }); ok(r.state === "ok" && /S = 2\b/.test(r.text) && /not classified/.test(r.text), "layering = 2: " + r.text);
  r = await fill("layeringIndex", { v: 0.3, c: 2, F: 9 }); ok(/probable danger/.test(r.text), "layering < 2");
  r = await fill("methanePosition", { c: "abc" }); ok(r.state === "invalid", "invalid methane");
  r = await fill("methanePosition", { c: 9.5 }); ok(/stoichiometric 9\.5 %/.test(r.text), "9.5 %");
  // mobile width: no horizontal overflow
  await p.setViewportSize({ width: 320, height: 900 }); await p.waitForTimeout(200);
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= 320), "no overflow at 320 px");
  ok(errs.length === 0, "page errors: " + errs.join("; "));
  console.log(fail ? `${fail} UI checks failed` : "UI checks passed");
  await b.close(); process.exit(fail ? 1 : 0);
})();
