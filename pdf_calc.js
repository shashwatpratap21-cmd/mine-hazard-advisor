// Calculations and retrieval for the technical data extracted from the "Mine Explosions" PDF (data/pdf_technical_data.json).
// Pure functions: no DOM. Inlined into the page by build_site.py and loaded directly by tests/test_pdf_calc.js.
// Rules: a calculation runs only when every input is supplied as a number in the stated unit; nothing is assumed or inferred.
const PDFCALC = (() => {
  // "" / null / undefined -> missing; anything that is not a plain finite number -> invalid
  function num(v) {
    if (v === null || v === undefined) return { missing: true };
    if (typeof v === "number") return Number.isFinite(v) ? { v } : { invalid: true };
    const s = String(v).trim();
    if (s === "") return { missing: true };
    if (!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(s)) return { invalid: true };
    const x = Number(s);
    return Number.isFinite(x) ? { v: x } : { invalid: true };
  }
  // read named inputs; spec: {k:[label, unit, check(x) -> error text | ""]}
  function readInputs(raw, spec) {
    const vals = {}, missing = [], errors = [];
    for (const [k, [label, unit, check]] of Object.entries(spec)) {
      const r = num(raw ? raw[k] : undefined);
      if (r.missing) { missing.push(`${label} (${unit})`); continue; }
      if (r.invalid) { errors.push(`${label}: not a number`); continue; }
      const e = check ? check(r.v) : "";
      if (e) { errors.push(`${label}: ${e}`); continue; }
      vals[k] = r.v;
    }
    return { vals, missing, errors };
  }
  const notCalc = (missing, errors) => ({ ok: false, missing, errors });
  const pos = x => (x > 0 ? "" : "must be greater than 0");
  const pct = x => (x < 0 || x > 100 ? "must be between 0 and 100 %" : "");
  const pctPos = x => (x <= 0 || x > 100 ? "must be greater than 0 and at most 100 %" : "");
  const fmt = (x, d = 3) => { if (!Number.isFinite(x)) return String(x); const a = Math.abs(x); return (a !== 0 && (a < 0.001 || a >= 1e6)) ? x.toExponential(2) : String(+x.toFixed(d)); };

  // Position of a measured methane concentration against the PDF's approximate flammable range (M01) and 9.5 % (M02).
  // Reference comparison, not a prediction: the PDF's limits are approximate and the LFL falls with airborne coal dust (M05).
  function methanePosition(raw, ref = { lo: 5, hi: 15, st: 9.5 }) {
    const { vals, missing, errors } = readInputs(raw, { c: ["Measured methane", "% CH₄", pct] });
    if (missing.length || errors.length) return notCalc(missing, errors);
    const c = vals.c;
    let zone, text;
    if (c < ref.lo) { zone = "below"; text = `Below the PDF's approximate lower flammable limit (≈${ref.lo} %).`; }
    else if (c === ref.lo) { zone = "at-lower"; text = `At the PDF's approximate lower flammable limit (≈${ref.lo} %).`; }
    else if (c < ref.hi) { zone = "within"; text = `Inside the PDF's approximate flammable range (≈${ref.lo}–${ref.hi} %).`; }
    else if (c === ref.hi) { zone = "at-upper"; text = `At the PDF's approximate upper flammable limit (≈${ref.hi} %).`; }
    else { zone = "above"; text = `Above the PDF's approximate upper flammable limit (≈${ref.hi} %).`; }
    let stoich = null;
    if (zone === "within" || zone.startsWith("at")) {
      stoich = c === ref.st ? `Equal to the stoichiometric ${ref.st} %, where the PDF says explosions are most violent.`
        : c < ref.st ? `Below ${ref.st} % (oxygen in excess).` : `Above ${ref.st} % (oxygen not sufficient for complete combustion).`;
    }
    const notes = [];
    if (zone === "below") notes.push("Not by itself safe: the PDF states the lower limit falls towards zero as airborne coal dust increases, and it gives no statutory action limit.");
    if (zone === "above") notes.push("Can become flammable again when diluted with air (Coward diagram, PDF p.11).");
    notes.push("Comparison with a reference range, not a prediction of an explosion: an ignition source and the other conditions also matter.");
    return { ok: true, value: c, unit: "% CH₄", zone, text, stoich, notes, inputs: { c }, formula: `compare c with ≈${ref.lo}–${ref.hi} % and ${ref.st} %` };
  }

  // Gas-emission index (M11): q = c × 60 × 24 × Q_air / (100 × O × K) = c × 14.4 × Q_air / (O × K), m³ CH₄/t; degree from M13.
  function gassinessDegree(q) {
    if (!Number.isFinite(q) || q < 0) return null;
    return q < 1 ? "I" : q <= 10 ? "II" : "III";   // printed table: < 1, 1 - 10, > 10
  }
  function gasEmissionIndex(raw) {
    const { vals, missing, errors } = readInputs(raw, {
      c: ["Methane in return air", "% CH₄", pct],
      Q: ["Return air quantity", "m³/min", pos],
      O: ["Output", "t/d", pos],
      K: ["K", "–", x => (x < 1 ? "is the weekly maximum ÷ the weekly average, so it cannot be below 1" : "")]
    });
    if (missing.length || errors.length) return notCalc(missing, errors);
    const { c, Q, O, K } = vals;
    const q = (c * 60 * 24 * Q) / (100 * O * K);
    const notes = [];
    if (K > 2) notes.push(`K = ${fmt(K)} is outside the 1–2 range the PDF gives.`);
    notes.push("Degree as printed in the PDF's Indian classification; not checked against current regulations.");
    const daily = (c / 100) * Q * 1440;
    return { ok: true, value: q, unit: "m³ CH₄/t", degree: gassinessDegree(q), inputs: { c, Q, O, K },
      formula: "q = c × 60 × 24 × Q_air / (100 × O × K)", working: `${fmt(c)} × 14.4 × ${fmt(Q)} / (${fmt(O)} × ${fmt(K)})`,
      daily, notes };
  }

  // Middendorf layering index (V01), as printed on PDF p.8: S = cube root of ( 24 v² / (c √F) ).
  // S < 2 probable danger of layering; S > 2 no danger; S = 2 is not classified by the stated rule.
  function layeringIndex(raw) {
    const { vals, missing, errors } = readInputs(raw, {
      v: ["Mean air velocity", "m/s", pos],
      c: ["Mean methane", "% CH₄", pctPos],
      F: ["Airway cross-section", "m²", pos]
    });
    if (missing.length || errors.length) return notCalc(missing, errors);
    const { v, c, F } = vals;
    const S = Math.cbrt((24 * v * v) / (c * Math.sqrt(F)));
    const EPS = 1e-9;
    const cls = Math.abs(S - 2) <= EPS ? "undefined" : S < 2 ? "danger" : "no-danger";
    const text = cls === "undefined" ? "S = 2: not classified by the rule stated in the PDF (it defines only S < 2 and S > 2)."
      : cls === "danger" ? "S < 2: the PDF states there is probable danger of methane layering."
      : "S > 2: the PDF states there is no danger of methane layering.";
    return { ok: true, value: S, unit: "–", cls, text, inputs: { v, c, F }, formula: "S = ∛( 24 v² / (c √F) )",
      working: `∛( 24 × ${fmt(v)}² / (${fmt(c)} × √${fmt(F)}) )`,
      notes: ["The PDF requires a correction factor for a rising airway or a changing cross-section but does not give it; it is not applied, so the result holds only for a level airway of constant section."] };
  }

  // Le Chatelier (M04): 100 / L = Σ p_i / l_i, with Σ p_i = 100.
  function leChatelier(rows) {
    const missing = [], errors = [], comp = [];
    (rows || []).forEach((r, i) => {
      const name = (r && r.name && String(r.name).trim()) || `Gas ${i + 1}`;
      const p = num(r && r.p), l = num(r && r.l);
      if (p.missing && l.missing) return;                       // empty row
      if (p.missing) missing.push(`${name}: share (%)`); else if (p.invalid) errors.push(`${name}: share is not a number`);
      else if (p.v < 0 || p.v > 100) errors.push(`${name}: share must be between 0 and 100 %`);
      if (l.missing) missing.push(`${name}: lower limit (%)`); else if (l.invalid) errors.push(`${name}: lower limit is not a number`);
      else if (l.v <= 0 || l.v > 100) errors.push(`${name}: lower limit must be greater than 0 and at most 100 %`);
      if (!p.missing && !p.invalid && !l.missing && !l.invalid) comp.push({ name, p: p.v, l: l.v });
    });
    if (!comp.length && !missing.length && !errors.length) missing.push("at least one gas: share (%) and lower limit (%)");
    if (missing.length || errors.length) return notCalc(missing, errors);
    const sumP = comp.reduce((a, c) => a + c.p, 0);
    if (Math.abs(sumP - 100) > 0.01) return notCalc([], [`The shares add up to ${fmt(sumP)} %; the PDF defines them as summing to 100 %.`]);
    const L = 100 / comp.reduce((a, c) => a + (c.p / c.l), 0);
    return { ok: true, value: L, unit: "%", inputs: comp, formula: "100 / L = p₁/l₁ + p₂/l₂ + …",
      working: `100 / (${comp.map(c => `${fmt(c.p)}/${fmt(c.l)}`).join(" + ")})`,
      notes: ["Lower limits other than methane's (≈5 %) are not given in the PDF; they come from your input."] };
  }

  // ----- retrieval: which entries and calculators fit the analysed situation -----
  const RX = {
    gas: /\b(?:methane|firedamp|fire-damp|ch4|gas|gassy|gases)\b/i,
    gasNamed: /\b(?:methane|firedamp|fire-damp|ch4)\b/i,
    dust: /\b(?:dust|dusty)\b/i,
    coal: /\b(?:coal|colliery|collieries|firedamp|seam|longwall|bord and pillar|goaf|goaves)\b/i,
    plant: /\b(?:processing plant|beneficiation|concentrator|smelter|mill(?:ing)?|plant)\b/i,
    hydrocarbon: /\b(?:cylinders?|lpg|acetylene|propane|butane|diesel|petrol|fuel|vapou?rs?|oxy-?\w*)\b/i,
    blasting: /\b(?:blast\w*|shot\s?fir\w*|explosives|detonat\w*|charged\s+(?:blast\s+)?holes?|charging)\b/i,   // not the adjective "explosive"
    barrier: /\b(?:stone[- ]?dust\w*|rock[- ]?dust\w*|barriers?|shelf|shelves|water barrier\w*|explosion[- ]proof stopping\w*)\b/i,
    stated: /(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:methane|ch4|ch₄|firedamp)\b|\b(?:methane|ch4|ch₄|firedamp)\b[^.%\d]{0,30}?(\d+(?:\.\d+)?)\s*%/i
  };
  const CAT_KEYS = [
    [/^Methane/, ["methane"]],
    [/^Coal-Dust/, ["coal_dust"]],
    [/^Combined/, ["methane", "coal_dust", "combined"]],
    [/^Blasting/, ["blasting_coal"]],
    [/^Electrical/, ["electrical"]],
    [/^Spontaneous/, ["sealed"]],
    [/^Metal Mine/, []]
  ];
  // context: "coal", "noncoal" or "unknown" (mine type not given and nothing in the text decides)
  function context(text, mt) {
    if (mt === "Coal") return "coal";
    if (mt) return "noncoal";
    const coal = RX.coal.test(text);
    const non = /\b(?:metal|ore|iron|copper|zinc|lead|manganese|bauxite|gold|uranium|limestone|granite|stone quarry|quarry|sulph\w*|sulf\w*|pyrit\w*)\b/i.test(text) || RX.plant.test(text);
    if (coal && !/\b(?:metal|ore)\b/i.test(text)) return "coal";
    if (non && !coal) return "noncoal";
    return coal ? "coal" : "unknown";
  }
  function keysFor(cats, text, ctx) {
    const keys = new Set();
    for (const cat of cats.filter(Boolean)) for (const [rx, ks] of CAT_KEYS) if (rx.test(cat)) ks.forEach(k => keys.add(k));
    // "gas" means firedamp only when the description names methane, or says gas in a coal context without a fuel gas
    const gasNamed = RX.gasNamed.test(text), gas = gasNamed || (RX.gas.test(text) && !RX.hydrocarbon.test(text)), dust = RX.dust.test(text);
    const coalOk = ctx !== "noncoal";
    if (keys.has("blasting_coal") && !coalOk) keys.delete("blasting_coal");
    if (keys.has("sealed") && !coalOk) keys.delete("sealed");
    if ((keys.has("electrical") || keys.has("blasting_coal") || keys.has("sealed")) && (gasNamed || (gas && coalOk))) keys.add("methane");
    if (cats.some(c => /^Metal Mine/.test(c || ""))) {
      if (dust) keys.add("dust_any");
      if (gasNamed) keys.add("methane");
    }
    if (!coalOk) { keys.delete("coal_dust"); keys.delete("combined"); if (!gasNamed) keys.delete("methane"); }
    if (coalOk && ((keys.has("methane") && /\bcoal[- ]dust\b|\bdust\b/i.test(text)) || (keys.has("coal_dust") && gas))) keys.add("combined");
    if (coalOk && keys.has("combined")) { keys.add("methane"); keys.add("coal_dust"); }
    if (coalOk && RX.barrier.test(text)) keys.add("barrier");
    if (ctx === "coal" && RX.blasting.test(text) && (keys.has("methane") || keys.has("coal_dust"))) keys.add("blasting_coal");
    if (keys.has("dust_any") || keys.has("coal_dust")) keys.add("dust_any");
    return keys;
  }
  // entries: data.entries; returns {ctx, keys, items:[{e, why, matched}], calcs:[{name, open, prefill}], stated}
  function select(data, { cats, text, mt }) {
    const t = String(text || ""), ctx = context(t, mt), keys = keysFor(cats || [], t, ctx);
    const gasNamed = RX.gasNamed.test(t);
    const items = [];
    for (const e of data.entries) {
      if (e.sector === "coal" && ctx === "noncoal") continue;
      if (e.sector === "gas" && ctx === "noncoal" && !gasNamed) continue;
      const base = (e.base || []).some(k => keys.has(k));
      let matched = null;
      if (!base && e.triggers && e.mechanism.some(k => keys.has(k))) { const m = t.match(new RegExp(e.triggers, "i")); if (m) matched = m[0]; }
      if (base || matched) items.push({ e, why: base ? "mechanism" : "words", matched });
    }
    const ids = new Set(items.map(i => i.e.id));
    if (ids.has("M11") && !ids.has("M12")) { const k = data.entries.find(x => x.id === "M12"); if (k) items.push({ e: k, why: "with", matched: null }); }
    if (ids.has("M11") && !ids.has("M13")) { const k = data.entries.find(x => x.id === "M13"); if (k) items.push({ e: k, why: "with", matched: null }); }
    // a barrier named in the description comes first; then values for the mechanism; then values matched by words
    const rank = i => (keys.has("barrier") && RX.barrier.test(t) && (i.e.base || []).includes("barrier") ? 0 : i.why === "mechanism" ? 1 : 2);
    items.sort((a, b) => rank(a) - rank(b));
    // stated methane reading in the description: offered as an input to confirm, never used for anything else
    const sm = t.match(RX.stated);
    const stated = sm ? Number(sm[1] || sm[2]) : null;
    const calcs = [];
    const has = id => items.some(i => i.e.id === id);
    if (keys.has("methane")) calcs.push({ name: "methanePosition", open: stated !== null, prefill: stated !== null ? { c: String(stated) } : null });
    if (keys.has("methane") && ctx !== "noncoal") {
      calcs.push({ name: "gasEmissionIndex", open: has("M11") });
      calcs.push({ name: "layeringIndex", open: has("V01") });
    }
    if (has("M04")) calcs.push({ name: "leChatelier", open: items.some(i => i.e.id === "M04" && i.why === "words") });
    return { ctx, keys: [...keys], items, calcs, stated };
  }

  return { num, methanePosition, gassinessDegree, gasEmissionIndex, layeringIndex, leChatelier, select, context, fmt };
})();
if (typeof module !== "undefined" && module.exports) module.exports = PDFCALC;
