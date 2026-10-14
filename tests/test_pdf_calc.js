// Tests for the PDF technical data and calculations.  Run: node tests/test_pdf_calc.js
// Checks source values and units against data/pdf_technical_data.json, the equations, the classification boundaries,
// missing and invalid inputs, and the retrieval rules (no coal values for metal mines; no calculation without inputs).
const assert = require("assert");
const path = require("path");
const fs = require("fs");
const C = require(path.join(__dirname, "..", "pdf_calc.js"));
const D = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "pdf_technical_data.json"), "utf8"));
const E = Object.fromEntries(D.entries.map(e => [e.id, e]));
let n = 0, fail = 0;
function t(name, fn) { n++; try { fn(); } catch (e) { fail++; console.log("FAIL", name, "\n   ", e.message); } }
const near = (a, b, tol = 1e-9) => assert.ok(Math.abs(a - b) <= tol, `${a} != ${b}`);

// ---------- source values, units and pages ----------
const SRC = [
  ["M01", { lo: 5, hi: 15 }, "% CH₄ by volume", 2],
  ["M02", { value: 9.5 }, "% CH₄ by volume", 2],
  ["M07", { value: 550 }, "°C", 3],
  ["M08", { lo: 650, hi: 750 }, "°C", 3],
  ["M09", { value: 7.2 }, "bar", 3],
  ["M10", { at9_5: 4.5, at12: 5, peak: 12 }, "× gas-zone length (total flame length)", 3],
  ["M11", { factor: 14.4 }, "m³ CH₄/t", 4],
  ["M12", { lo: 1, hi: 2, mech_lo: 1.5, mech_hi: 2 }, "–", 5],
  ["M13", { I_below: 1, III_above: 10 }, "m³ CH₄/t output", 5],
  ["M14", { value: 12.1, air: 20.93 }, "% O₂", 11],
  ["D02", { lo: 600, hi: 900 }, "°C", 12],
  ["D03", { dust_min: 100, gas_lo: 1, gas_hi: 2 }, "ms", 12],
  ["D05", { value: 0.4 }, "m³", 13],
  ["B01", { lo: 25, hi: 40 }, "m", 15],
  ["B02", { w_lo: 10, w_hi: 15, l_lo: 35, l_hi: 50 }, "cm", 15],
  ["B04", { w_max: 35, load_max: 29.8 }, "cm; kg/m", 16],
  ["B05", { w_min: 35, w_max: 50, load_max: 59.6 }, "cm; kg/m", 16],
  ["B06", { min: 107.4 }, "kg/m²", 16],
  ["B07", { value: 195.3 }, "kg/m²", 16],
  ["B08", { min: 390.6 }, "kg/m²", 16],
  ["B09", { light_min: 0.91, light_max: 2.10, heavy_min: 1.22, heavy_max: 2.59 }, "“in” as printed (probably m)", 16],
  ["B10", { lo: 0.1, hi: 0.2 }, "s", 17],
  ["B11", { v_flame: 500, d_lo: 40, d_hi: 60, p_lo: 3, p_hi: 5 }, "m/s; m; kN/m²", 17]
];
for (const [id, num, unit, page] of SRC) t(`source value ${id}`, () => {
  assert.deepStrictEqual(E[id].num, num); assert.strictEqual(E[id].unit, unit); assert.strictEqual(E[id].pdf_page, page);
  assert.strictEqual(String(E[id].pdf_page), String(Number(E[id].printed_page.split("/")[0]) + 1), "PDF page = footer + 1");
});
t("every entry has a group, page, status and paraphrased source fields", () => {
  for (const e of D.entries) {
    assert.ok(["calculation", "reference", "design"].includes(e.group), e.id);
    assert.ok(e.pdf_page >= 1 && e.pdf_page <= 19, e.id);
    assert.ok(["verified", "flagged"].includes(e.status), e.id);
    if (e.status === "flagged") assert.ok(e.flag, e.id);
    for (const f of ["parameter", "value", "conditions", "applicability", "limitations", "relevance", "section"]) assert.ok(String(e[f]).length > 0, e.id + " " + f);
  }
});
t("ambiguous items are flagged, not corrected", () => {
  for (const id of ["B07", "B08", "B09", "B11", "V03"]) assert.strictEqual(E[id].status, "flagged", id);
  assert.match(E.B09.unit, /in/); assert.match(E.B08.value, /light type/);
  assert.strictEqual(E.B03.value, "Only the Polish Shelf (statement in the PDF)");
  assert.match(E.B03.applicability, /not checked as current regulatory advice/);
});
t("Middendorf equation is the one printed in the PDF (cube root, √F)", () => {
  assert.strictEqual(E.V01.value, "S = ∛( 24 v² / (c √F) )"); assert.strictEqual(E.V01.pdf_page, 8); assert.strictEqual(E.V01.printed_page, "7/17");
});

// ---------- methane position ----------
t("methane below the range", () => { const r = C.methanePosition({ c: "1.2" }); assert.ok(r.ok); assert.strictEqual(r.zone, "below"); assert.strictEqual(r.unit, "% CH₄"); assert.match(r.notes.join(" "), /Not by itself safe/); });
t("methane within the range", () => { const r = C.methanePosition({ c: 7 }); assert.strictEqual(r.zone, "within"); assert.match(r.stoich, /Below 9.5 %/); });
t("methane at the stoichiometric 9.5 %", () => { const r = C.methanePosition({ c: "9.5" }); assert.strictEqual(r.zone, "within"); assert.match(r.stoich, /stoichiometric 9.5 %/); });
t("methane above 9.5 inside the range", () => { const r = C.methanePosition({ c: 12 }); assert.match(r.stoich, /not sufficient/); });
t("methane above the range", () => { const r = C.methanePosition({ c: 20 }); assert.strictEqual(r.zone, "above"); assert.strictEqual(r.stoich, null); });
t("methane at the limits", () => { assert.strictEqual(C.methanePosition({ c: 5 }).zone, "at-lower"); assert.strictEqual(C.methanePosition({ c: 15 }).zone, "at-upper"); });
t("methane result is never a prediction", () => { for (const c of [1, 9.5, 20]) assert.match(C.methanePosition({ c }).notes.join(" "), /not a prediction/); });
t("methane missing / invalid", () => {
  assert.deepStrictEqual(C.methanePosition({}).missing, ["Measured methane (% CH₄)"]);
  assert.ok(!C.methanePosition({ c: "abc" }).ok); assert.ok(!C.methanePosition({ c: "-1" }).ok); assert.ok(!C.methanePosition({ c: "101" }).ok);
  assert.ok(!C.methanePosition({ c: "5%" }).ok, "units typed into the box are rejected, not guessed");
  assert.ok(!C.methanePosition({ c: "Infinity" }).ok);
});

// ---------- gas-emission index ----------
const q = (c, Q, O, K) => c * 14.4 * Q / (O * K);
t("gas-emission equation: both printed forms agree", () => { const r = C.gasEmissionIndex({ c: 0.5, Q: 3000, O: 1500, K: 1.5 }); near(r.value, q(0.5, 3000, 1500, 1.5)); near(r.value, 0.5 * 60 * 24 * 3000 / (100 * 1500 * 1.5)); assert.strictEqual(r.unit, "m³ CH₄/t"); });
t("gas-emission dimensions: daily methane volume", () => { const r = C.gasEmissionIndex({ c: 1, Q: 1000, O: 100, K: 1 }); near(r.daily, 14400); near(r.value, 144); });
t("degree I below 1", () => { const r = C.gasEmissionIndex({ c: 0.1, Q: 1000, O: 2000, K: 1.2 }); assert.ok(r.value < 1); assert.strictEqual(r.degree, "I"); });
t("degree II within 1-10", () => { const r = C.gasEmissionIndex({ c: 0.5, Q: 2000, O: 1000, K: 2 }); near(r.value, 7.2); assert.strictEqual(r.degree, "II"); });
t("degree III above 10", () => { const r = C.gasEmissionIndex({ c: 0.8, Q: 3000, O: 1000, K: 1.5 }); assert.ok(r.value > 10); assert.strictEqual(r.degree, "III"); });
t("degree boundaries as printed (1 and 10 are degree II)", () => {
  assert.strictEqual(C.gassinessDegree(0.999), "I"); assert.strictEqual(C.gassinessDegree(1), "II");
  assert.strictEqual(C.gassinessDegree(10), "II"); assert.strictEqual(C.gassinessDegree(10.001), "III"); assert.strictEqual(C.gassinessDegree(-1), null);
});
t("gas-emission missing inputs are not invented", () => {
  const r = C.gasEmissionIndex({ c: 0.5, Q: 2000 }); assert.ok(!r.ok); assert.deepStrictEqual(r.missing, ["Output (t/d)", "K (–)"]); assert.strictEqual(r.value, undefined);
});
t("gas-emission invalid inputs", () => {
  assert.ok(!C.gasEmissionIndex({ c: 0.5, Q: 2000, O: 0, K: 1.5 }).ok);
  assert.ok(!C.gasEmissionIndex({ c: 0.5, Q: -5, O: 10, K: 1.5 }).ok);
  assert.match(C.gasEmissionIndex({ c: 0.5, Q: 20, O: 10, K: 0.8 }).errors[0], /cannot be below 1/);
  assert.match(C.gasEmissionIndex({ c: 0.5, Q: 20, O: 10, K: 3 }).notes[0], /outside the 1–2 range/);
});

// ---------- Middendorf layering index ----------
const S = (v, c, F) => Math.cbrt(24 * v * v / (c * Math.sqrt(F)));
t("layering below 2: probable danger", () => { const r = C.layeringIndex({ v: 0.3, c: 2, F: 9 }); near(r.value, S(0.3, 2, 9)); assert.ok(r.value < 2); assert.strictEqual(r.cls, "danger"); });
t("layering above 2: no danger (as stated)", () => { const r = C.layeringIndex({ v: 2, c: 0.5, F: 9 }); assert.ok(r.value > 2); assert.strictEqual(r.cls, "no-danger"); });
t("layering equal to 2: not classified", () => { const r = C.layeringIndex({ v: 1, c: 3, F: 1 }); near(r.value, 2); assert.strictEqual(r.cls, "undefined"); assert.match(r.text, /not classified/); });
t("layering correction factor is disclosed", () => { assert.match(C.layeringIndex({ v: 1, c: 1, F: 4 }).notes[0], /correction factor/); });
t("layering missing / invalid", () => {
  assert.deepStrictEqual(C.layeringIndex({ v: 1 }).missing, ["Mean methane (% CH₄)", "Airway cross-section (m²)"]);
  assert.ok(!C.layeringIndex({ v: 1, c: 0, F: 4 }).ok, "c = 0 would divide by zero");
  assert.ok(!C.layeringIndex({ v: 1, c: 1, F: -4 }).ok);
  assert.ok(!C.layeringIndex({ v: "fast", c: 1, F: 4 }).ok);
});

// ---------- Le Chatelier ----------
t("Le Chatelier single gas returns its own limit", () => { near(C.leChatelier([{ name: "methane", p: 100, l: 5 }]).value, 5); });
t("Le Chatelier mixture", () => { const r = C.leChatelier([{ name: "A", p: 80, l: 5 }, { name: "B", p: 20, l: 4 }]); near(r.value, 100 / (80 / 5 + 20 / 4)); assert.strictEqual(r.unit, "%"); });
t("Le Chatelier shares must sum to 100", () => { const r = C.leChatelier([{ p: 80, l: 5 }, { p: 10, l: 4 }]); assert.ok(!r.ok); assert.match(r.errors[0], /100/); });
t("Le Chatelier missing component limit", () => { const r = C.leChatelier([{ name: "CO", p: 100 }]); assert.ok(!r.ok); assert.deepStrictEqual(r.missing, ["CO: lower limit (%)"]); });
t("Le Chatelier empty", () => { assert.ok(!C.leChatelier([{}, {}]).ok); });

// ---------- retrieval ----------
const sel = (cats, text, mt = "") => C.select(D, { cats, text, mt });
const ids = s => s.items.map(i => i.e.id);
t("methane accumulation in a coal heading: methane references, no coal-dust or barrier values", () => {
  const s = sel(["Methane / Firedamp Explosion"], "Auxiliary fan failure lets methane accumulate near the face of a development heading", "Coal");
  for (const id of ["M01", "M02", "M08"]) assert.ok(ids(s).includes(id), id);
  for (const id of ["D02", "B01", "B04"]) assert.ok(!ids(s).includes(id), id);
  assert.ok(ids(s).includes("V03"), "heading triggers the diffusion rule");
  assert.deepStrictEqual(s.calcs.map(c => c.name), ["methanePosition", "gasEmissionIndex", "layeringIndex"]);
  assert.ok(s.calcs.every(c => !c.prefill), "no methane value is invented");
});
t("reference exists but site data are absent: calculators start empty and do not compute", () => {
  const s = sel(["Methane / Firedamp Explosion"], "methane accumulation in a coal mine", "Coal");
  assert.strictEqual(s.stated, null);
  for (const c of s.calcs) { const r = C[c.name](c.prefill || {}); assert.ok(!r.ok); assert.ok(r.missing.length > 0); }
});
t("a methane reading stated in the description is offered, not assumed", () => {
  const s = sel(["Methane / Firedamp Explosion"], "Gas test showed 2.5% methane at the face", "Coal");
  assert.strictEqual(s.stated, 2.5); assert.deepStrictEqual(s.calcs[0].prefill, { c: "2.5" }); assert.ok(s.calcs[0].open);
  assert.strictEqual(sel(["Methane / Firedamp Explosion"], "methane reading of 1.8 % in the return", "Coal").stated, 1.8);
});
t("coal dust: 600-900 °C with dust-cloud conditions", () => {
  const s = sel(["Coal-Dust Explosion"], "Dry coal dust dispersed into the air during transport", "Coal");
  for (const id of ["D01", "D02", "D03", "D04"]) assert.ok(ids(s).includes(id), id);
  assert.ok(ids(s).includes("D07"), "transport triggers the air-velocity guide");
  assert.ok(!ids(s).includes("M11")); assert.strictEqual(s.calcs.length, 0);
});
t("combined methane and coal dust: secondary-explosion data", () => {
  const s = sel(["Combined Methane and Coal-Dust Explosion"], "methane ignition raises coal dust", "Coal");
  for (const id of ["M05", "D05", "M01", "D02"]) assert.ok(ids(s).includes(id), id);
});
t("stone-dust barrier: design values and failure conditions", () => {
  const s = sel(["Coal-Dust Explosion"], "Checking the stone dust barrier shelves in a coal roadway", "Coal");
  for (const id of ["B01", "B04", "B05", "B06", "B07", "B08", "B09", "B10", "B11", "B02", "B03"]) assert.ok(ids(s).includes(id), id);
});
t("metal-ore processing plant dust: no coal values, only the general dust-cloud condition", () => {
  const s = sel(["Metal Mine: Gas, Dust and Other Explosion Mechanisms"], "Fine combustible dust accumulates in a metal-ore processing plant", "Metal ore");
  assert.strictEqual(s.ctx, "noncoal"); assert.deepStrictEqual(ids(s), ["D01"]); assert.strictEqual(s.calcs.length, 0);
});
t("metal mine with methane named: methane properties only, no gassiness index", () => {
  const s = sel(["Metal Mine: Gas, Dust and Other Explosion Mechanisms"], "methane detected in a metal mine raise", "Metal ore");
  assert.ok(ids(s).includes("M01")); assert.ok(!ids(s).some(i => /^[DB]|M11|M13|V01/.test(i)));
  assert.deepStrictEqual(s.calcs.map(c => c.name), ["methanePosition"]);
});
t("coal-dust class never shown for a metal mine even if the classifier says so", () => {
  const s = sel(["Coal-Dust Explosion"], "dust in an iron ore mine", "Metal ore"); assert.ok(!ids(s).some(i => /^D0[2-9]|^B/.test(i)));
});
t("misfire / blasting in a metal mine: nothing from the PDF", () => {
  const s = sel(["Blasting and Explosives-Related Explosion"], "drilling near a misfired hole in a granite quarry", "Non-metallic mineral (DGMS \"metalliferous\")");
  assert.strictEqual(s.items.length, 0); assert.strictEqual(s.calcs.length, 0);
});
t("blasting in a gassy coal seam: degree classification and shotfiring dust values", () => {
  const s = sel(["Blasting and Explosives-Related Explosion"], "Gas testing before blasting in a degree III gassy seam", "Coal");
  for (const id of ["D08", "D09", "M11", "M12", "M13", "M01"]) assert.ok(ids(s).includes(id), id);
  assert.ok(s.calcs.find(c => c.name === "gasEmissionIndex").open);
});
t("sealed fire area: Coward oxygen limit and Le Chatelier", () => {
  const s = sel(["Spontaneous Heating, Fire and Explosion Escalation"], "Welding near a sealed-off fire area where firedamp may be present", "Coal");
  for (const id of ["M14", "M04"]) assert.ok(ids(s).includes(id), id);
  assert.ok(s.calcs.some(c => c.name === "leChatelier"));
});
t("electrical ignition in a coal mine: 25 V and ignition temperature", () => {
  const s = sel(["Electrical or Mechanical Ignition of Explosive Atmosphere"], "damaged cable sparking in a coal mine return airway with gas", "Coal");
  for (const id of ["E01", "M08", "M01"]) assert.ok(ids(s).includes(id), id);
});
t("fuel-gas leak is not treated as firedamp", () => {
  const s = sel(["Metal Mine: Gas, Dust and Other Explosion Mechanisms", "Electrical or Mechanical Ignition of Explosive Atmosphere"], "A damaged gas cylinder or gas supply line leaks in a mine workshop near hot work");
  assert.ok(!s.keys.includes("methane")); assert.ok(!ids(s).some(i => /^M/.test(i))); assert.ok(!s.calcs.length);
});
t("gas checks before blasting in coal: shotfiring dust values join the methane data", () => {
  const s = sel(["Methane / Firedamp Explosion"], "Blasting is planned at an underground coal face, but the required gas checks have not been completed.", "Coal");
  for (const id of ["M01", "D08", "D09"]) assert.ok(ids(s).includes(id), id);
});
t("'explosive gas' is not blasting", () => {
  const s = sel(["Methane / Firedamp Explosion"], "A methane drainage system becomes ineffective in a gassy underground coal panel, increasing the risk of explosive gas accumulation.", "Coal");
  assert.ok(!ids(s).includes("D08")); assert.ok(ids(s).includes("M13"));
});
t("unknown mine type: coal values allowed, context reported", () => { assert.strictEqual(sel(["Methane / Firedamp Explosion"], "methane in a heading").ctx, "unknown"); });

console.log(`${n - fail}/${n} PDF data tests passed`);
process.exit(fail ? 1 : 0);
