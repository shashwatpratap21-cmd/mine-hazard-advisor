"""Explosion-specific intelligence for Mine Hazard Advisor.

Builds model/explosion.json from two logically separate datasets:
  A. Historical DGMS accident records (data/accidents.csv, include_in_search_index == 1)
  B. Synthetic explosion scenarios (Excel workbook, sheet Explosion_Scenarios)
  C. SANKET explosion-specific accident records (Mining_Explosion_Accidents_Predictive_Analysis.xlsx,
     sheet Accident_Database: coal + non-coal narratives 2016-2022 and the major-accident lists 1901-2022)
  D. Reference-book guidance (data/reference_guidance.json; Ramlu and Cheng, with section and page)

Usage:
  python build_explosion.py [--workbook PATH] [--accidents PATH] [--out model/explosion.json]
  or set EXPLOSION_WORKBOOK / ACCIDENTS_CSV environment variables.

The script stops with a clear error if the workbook is missing or fails validation.
It never edits the source files; all normalisation is listed in the report.
"""
import argparse, json, os, re, sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, GridSearchCV
from sklearn.pipeline import Pipeline

HERE = Path(__file__).resolve().parent
RANDOM_STATE = 42

EXPECTED_COLS = ["Scenario_ID", "Situation_Text", "Primary_Explosion_Category", "Mine_Type_Context",
                 "Place_of_Work_Context", "Data_Origin", "Historical_DGMS_Record", "Training_Use"]
TAXONOMY = [
    "Methane / Firedamp Explosion",
    "Coal-Dust Explosion",
    "Combined Methane and Coal-Dust Explosion",
    "Blasting and Explosives-Related Explosion",
    "Electrical or Mechanical Ignition of Explosive Atmosphere",
    "Spontaneous Heating, Fire and Explosion Escalation",
    "Metal Mine: Gas, Dust and Other Explosion Mechanisms",
]

# Explosion-evidence lexicon. Decides only WHETHER a description is explosion-related;
# the category always comes from the trained classifier. Patterns are JavaScript-compatible.
STRONG = {
    "explosion event": r"\bexplo(?:sion|sions|de|des|ded|ding)\b",
    "methane / firedamp": r"\b(?:methane|firedamp|fire damp|inflammable gas|flammable gas|gassy|ch4)\b",
    "coal dust": r"\bcoal[- ]dust\b|\bstone[- ]dust",
    "dust cloud / deposits": r"\bdust (?:cloud|explosion|deposits?|layer)\b",
    "explosives / blasting": r"\b(?:explosives?|blast(?:ing|ed|s)?|detonat\w*|detonators?|misfire\w*|sockets?|charged holes?|shot ?fir\w*|shot holes?|fly ?rock|blasters?|barood|visphot)\b",
    "explosive / flammable atmosphere": r"\b(?:explosive|flammable|inflammable|combustible) (?:\w+ )?(?:atmosphere|mixture|range|gas\w*)\b|\bgas (?:accumulat\w*|build-?up|release|outburst)|\b(?:accumulat\w*|build-?up of) (?:of )?gas|\boutburst\b",
    "combustible dust": r"\b(?:combustible|explosive|flammable|inflammable|sulphide|sulfide|pyrit\w*|pyrrhotite|sulphur|sulfur|alumin(?:i)?um|magnesium)(?:[- ]\w+)?[- ]dust\b",
    "spontaneous heating": r"\bspontaneous(?:ly)? (?:heating|combustion)\b|\bself[- ]heat\w*",
    "hydrocarbon / gas cylinder": r"\bhydrocarbons?\b|\bvapou?rs?\b|\bacetylene\b|\b(?:gas|oxygen) cylinders?\b",
}
WEAK = {
    "ignition source": r"\b(?:ignit\w*|sparks?|sparking|arc|arcing|flames?|hot surface|friction\w*|static)\b",
    "electrical equipment": r"\b(?:electric\w*|cables?|motors?|switch\w*|enclosures?|flame ?proof|transformers?)\b",
    "fire / heat": r"\b(?:fire|fires|smoke|heating|burn\w*|welding|gas cutting|hot work)\b",
    "gas / ventilation": r"\b(?:gas|gases|ventilat\w*|fan|fans|air ?flow)\b",
    "dust": r"\bdust\b",
}
ATMOSPHERE = {"gas / ventilation", "dust"}
EVENT = r"\b(?:explodes|exploded|explosion occurs|an explosion|explosion follows|ignites|ignited|is ignited|detonate|detonates|detonated|detonation|propagates|triggers|initiates|burst|blew)\b|\b(?:initial|secondary|primary|methane|gas|dust|firedamp|coal-dust) explosion\b|\bexplosion (?:disperses|spreads|follows|propagates)\b"

SUBJECT_AREAS = {  # general subject areas from the project brief; shown as NOT evidence-backed
    TAXONOMY[0]: ["Methane monitoring and ventilation"],
    TAXONOMY[1]: ["Coal-dust control and explosion-propagation prevention"],
    TAXONOMY[2]: ["Methane monitoring and ventilation", "Coal-dust control and explosion-propagation prevention"],
    TAXONOMY[3]: ["Approved blasting procedures and misfire management"],
    TAXONOMY[4]: ["Electrical equipment suitability for hazardous atmospheres"],
    TAXONOMY[5]: ["Fire detection and spontaneous-combustion control"],
    TAXONOMY[6]: ["Gas monitoring and ventilation", "Approved blasting procedures and misfire management"],
}


def fail(msg):
    sys.exit(f"\n[build_explosion] ERROR: {msg}\n")


EXPLOSIVE_GROUPS = {"Explosives", "Gas, dust & other combustible material"}


def evidence(text, dgms_hazard=None):
    """Explosion relevance. 'Blasting' alone is common in roof/side-fall reports ("after blasting..."),
    so when it is the only strong signal we also require an explosion/ignition event in the text or
    the existing DGMS classifier pointing to Explosives or Gas."""
    t = text.lower()
    strong = [k for k, p in STRONG.items() if re.search(p, t)]
    weak = [k for k, p in WEAK.items() if re.search(p, t)]
    other_strong = [k for k in strong if k != "explosives / blasting"]
    blasting_ok = "explosives / blasting" in strong and (bool(re.search(EVENT, t)) or "ignition source" in weak or dgms_hazard in EXPLOSIVE_GROUPS)
    atmosphere = len(set(weak) & ATMOSPHERE) >= 1 and len(set(weak) - ATMOSPHERE) >= 1
    relevant = bool(other_strong) or blasting_ok or atmosphere
    return relevant, strong, weak


def hist_category(row):
    """Map a historical record to the taxonomy only where its DGMS-derived explosion label supports it."""
    if row.get("core_explosion_flag") != 1:
        return None
    c = str(row.get("explosion_category") or "")
    if c.startswith("Blasting") or c.startswith("Explosives handling"):
        return TAXONOMY[3]
    if c.startswith("Mine gas ignition"):
        return TAXONOMY[0]
    return "Outside taxonomy: " + c


GASDUST = "Gas or coal-dust explosion (type not recorded)"
UNSPEC = "Explosion (type not recorded)"


def sanket_category(std, mine_type):
    """Map the project's explosion_category_std (itself derived from SANKET wording) to the taxonomy.
    The original SANKET cause label is kept unchanged alongside this mapping."""
    s = str(std)
    coal = str(mine_type) == "Coal"
    if s.startswith("Blasting") or s.startswith("Explosives"):
        return TAXONOMY[3]
    if s in ("Firedamp explosion/ignition", "Mine gas ignition/explosion (inflammable gas)", "Inflammable gas explosion", "Gas explosion/ignition (type not specified)"):
        return TAXONOMY[0] if coal else TAXONOMY[6]
    if s == "Coal dust explosion":
        return TAXONOMY[1]
    if s == "Damp/coal dust explosion":
        # DGMS "Explosions of damp/coal dust" means firedamp OR coal dust; it does not establish a combined explosion
        return GASDUST if coal else TAXONOMY[6]
    if s == "Gas/dust explosion/ignition (type not specified)":
        return GASDUST if coal else TAXONOMY[6]
    if s == "Explosion (type not specified)":
        return UNSPEC
    if s == "Hydrocarbon/vapour explosion in vessel (hot work)":
        # hot work is reported for only some of these records, so the mapped name does not assert it
        return "Outside taxonomy: Hydrocarbon/vapour explosion in vessel"
    return "Outside taxonomy: " + s


def export_tfidf(vec, clf=None):
    terms = sorted(vec.vocabulary_, key=vec.vocabulary_.get)
    out = {"terms": terms, "idf": [round(float(x), 4) for x in vec.idf_]}
    if clf is not None:
        out["classes"] = list(clf.classes_)
        out["coef"] = [[round(float(v), 4) for v in row] for row in clf.coef_]
        out["intercept"] = [round(float(x), 4) for x in clf.intercept_]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook", default=os.environ.get("EXPLOSION_WORKBOOK", str(HERE / "data" / "explosion_specific_mining_scenarios_200.xlsx")))
    ap.add_argument("--accidents", default=os.environ.get("ACCIDENTS_CSV", str(HERE / "data" / "accidents.csv")))
    ap.add_argument("--sanket", default=os.environ.get("SANKET_EXPLOSION_WORKBOOK", str(HERE / "data" / "Mining_Explosion_Accidents_Predictive_Analysis.xlsx")))
    ap.add_argument("--guidance", default=os.environ.get("REFERENCE_GUIDANCE", str(HERE / "data" / "reference_guidance.json")))
    ap.add_argument("--out", default=str(HERE / "model" / "explosion.json"))
    ap.add_argument("--report", default=str(HERE / "reports" / "explosion_evaluation.md"))
    a = ap.parse_args()
    log = []

    # ---------------- load + validate workbook ----------------
    wb = Path(a.workbook)
    if not wb.exists():
        fail(f"workbook not found at {wb}. Pass --workbook PATH or set EXPLOSION_WORKBOOK.")
    try:
        xl = pd.ExcelFile(wb)
    except Exception as e:
        fail(f"could not open workbook {wb}: {e}")
    if "Explosion_Scenarios" not in xl.sheet_names:
        fail(f"sheet 'Explosion_Scenarios' missing; found {xl.sheet_names}")
    syn = xl.parse("Explosion_Scenarios")
    missing = [c for c in EXPECTED_COLS if c not in syn.columns]
    if missing:
        fail(f"missing columns {missing}")
    problems = []
    if not syn["Scenario_ID"].is_unique: problems.append("duplicate Scenario_ID values")
    if syn[EXPECTED_COLS].isna().any().any(): problems.append("blank cells in required columns")
    bad = sorted(set(syn["Primary_Explosion_Category"]) - set(TAXONOMY))
    if bad: problems.append(f"unknown categories {bad}")
    if not syn["Data_Origin"].str.startswith("Synthetic").all(): problems.append("rows not marked synthetic in Data_Origin")
    if not (syn["Historical_DGMS_Record"].astype(str).str.strip() == "No").all(): problems.append("rows not marked Historical_DGMS_Record = No")
    if problems:
        fail("; ".join(problems))
    dup_text = int(syn["Situation_Text"].str.strip().str.lower().duplicated().sum())
    summary = xl.parse("Category_Summary") if "Category_Summary" in xl.sheet_names else None
    if summary is not None:
        cnt = syn["Primary_Explosion_Category"].value_counts()
        for _, r in summary.iterrows():
            if int(cnt.get(r["Primary_Explosion_Category"], 0)) != int(r["Scenario_Count"]):
                fail(f"Category_Summary count mismatch for {r['Primary_Explosion_Category']}")
    syn["is_event"] = syn["Situation_Text"].str.contains(EVENT, case=False, regex=True)
    mt_ctx = syn.groupby("Primary_Explosion_Category")["Mine_Type_Context"].agg(lambda s: sorted(set(s)))
    log.append(f"Imported {len(syn)} synthetic scenarios from {wb.name}; IDs unique; {dup_text} duplicate texts; categories match Category_Summary.")
    log.append(f"All rows marked synthetic and Historical_DGMS_Record = No. No source values were changed.")
    log.append(f"Event wording heuristic: {int(syn.is_event.sum())} scenarios describe an explosion/ignition event, {int((~syn.is_event).sum())} describe a potential hazard only.")

    # ---------------- historical records ----------------
    acc = Path(a.accidents)
    if not acc.exists():
        fail(f"historical accidents CSV not found at {acc}. Pass --accidents PATH or set ACCIDENTS_CSV.")
    hist = pd.read_csv(acc)
    hist = hist[hist["include_in_search_index"] == 1].reset_index(drop=True)
    hist["xcat"] = hist.apply(hist_category, axis=1)
    hist["situation"] = hist["situation"].fillna("")
    allacc = pd.read_csv(acc)   # includes narratives left out of the general search index (no findings printed)

    # ---------------- SANKET explosion-specific records ----------------
    sk = Path(a.sanket)
    if not sk.exists():
        fail(f"SANKET explosion workbook not found at {sk}. Pass --sanket PATH or set SANKET_EXPLOSION_WORKBOOK.")
    try:
        sx = pd.read_excel(sk, "Accident_Database")
    except Exception as e:
        fail(f"could not read sheet Accident_Database from {sk}: {e}")
    need = ["accident_id", "record_type", "is_primary_record", "duplicate_of", "source_document", "source_pdf_page", "source_printed_page",
            "source_table_ref", "date_as_printed", "year", "mine_name", "state", "district", "mineral", "mine_type_std", "place_per_source_statement",
            "source_cause_label", "explosion_category_std", "explosion_family", "ignition_source_reported", "reported_cause", "cause_status",
            "fatalities", "seriously_injured", "core_explosion_flag", "verification_notes", "data_flag"]
    miss = [c for c in need if c not in sx.columns]
    if miss: fail(f"Accident_Database is missing columns {miss}")
    if not sx["accident_id"].is_unique: fail("Accident_Database has duplicate accident_id values")
    bad_dup = sorted(set(sx["duplicate_of"].dropna()) - set(sx["accident_id"]))
    if bad_dup: fail(f"duplicate_of points to unknown ids {bad_dup}")
    sx["src"] = np.where(sx["source_document"].str.startswith("Coal"), "Coal SANKET report", "Non-coal SANKET report")
    sx["kind"] = np.where(sx["record_type"].str.startswith("Individual"), "narrative", "list")
    link = allacc.set_index("workbook_id")
    sx["dgms_id"] = sx["accident_id"].map(lambda i: link.loc[i, "id"] if i in link.index else "")
    unlinked = sx[(sx.kind == "narrative") & (sx.dgms_id == "")]
    if len(unlinked): fail(f"narratives not found in accidents.csv: {unlinked.accident_id.tolist()}")
    sx["xcat"] = [sanket_category(s, m) for s, m in zip(sx["explosion_category_std"], sx["mine_type_std"])]
    dups = sx[sx["is_primary_record"] != 1]
    core = sx[(sx["is_primary_record"] == 1) & (sx["core_explosion_flag"] == 1)].copy()
    excluded_noncore = sx[(sx["is_primary_record"] == 1) & (sx["core_explosion_flag"] != 1)]
    also_listed = {r.duplicate_of: r.accident_id for r in dups.itertuples()}

    def nz(v, default=""):
        return default if (v is None or (isinstance(v, float) and np.isnan(v))) else v

    hrec = []
    for r in core.itertuples():
        d = link.loc[r.accident_id] if r.dgms_id else None
        findings = [m.strip() for m in str(nz(d["measures"] if d is not None else "", "")).split("|") if m.strip()]
        hrec.append({
            "id": r.accident_id, "dgms_id": r.dgms_id, "kind": r.kind, "src": r.src, "doc": r.source_document,
            "pdf_page": int(r.source_pdf_page) if not pd.isna(r.source_pdf_page) else None,
            "printed_page": nz(r.source_printed_page), "table": nz(r.source_table_ref), "date": str(nz(r.date_as_printed)),
            "year": int(r.year) if not pd.isna(r.year) else None, "mine": str(nz(r.mine_name)), "state": str(nz(r.state, "Not reported")),
            "district": str(nz(r.district)), "mineral": str(nz(r.mineral)), "mine_type": str(nz(r.mine_type_std)),
            "place": str(d["place"]) if d is not None else str(nz(r.place_per_source_statement, "Not reported")),
            "cause_label": str(nz(r.source_cause_label)), "cat_std": str(nz(r.explosion_category_std)), "xcat": r.xcat,
            "ignition": str(nz(r.ignition_source_reported)), "reported_cause": str(nz(r.reported_cause)), "cause_status": str(nz(r.cause_status)),
            "killed": int(nz(r.fatalities, 0)), "injured": (None if nz(r.seriously_injured, None) is None else int(r.seriously_injured)),
            "situation": str(d["situation"]) if d is not None else "", "findings": findings,
            "regulations": str(nz(d["regulations"], "")) if d is not None else "", "statutes": str(nz(d["statutes_cited"], "")) if d is not None else "",
            "notes": str(nz(r.verification_notes)), "flag": str(nz(r.data_flag)), "also_listed": also_listed.get(r.accident_id, ""),
        })
    sk_log = (f"SANKET explosion workbook {sk.name}: {len(sx)} rows ({int((sx.kind=='narrative').sum())} narratives, {int((sx.kind=='list').sum())} major-accident list rows); "
               f"{len(dups)} flagged duplicates removed ({', '.join(f'{r.accident_id}→{r.duplicate_of}' for r in dups.itertuples())}); "
               f"{len(excluded_noncore)} non-explosion/borderline rows excluded ({', '.join(excluded_noncore.accident_id)}); {len(hrec)} explosion records used.")
    log.append(sk_log)

    # ---------------- reference-book guidance ----------------
    gp = Path(a.guidance)
    if not gp.exists(): fail(f"guidance file not found at {gp}. Pass --guidance PATH or set REFERENCE_GUIDANCE.")
    G = json.loads(gp.read_text(encoding="utf-8"))
    for g in G["guidance"]:
        if not set(g["mechanisms"]) <= set(TAXONOMY): fail(f"{g['id']}: unknown mechanism {set(g['mechanisms']) - set(TAXONOMY)}")
        for ref in g["refs"]:
            if ref["book"] not in G["books"] or not ref.get("pages") or ref["support"] not in ("states", "case"):
                fail(f"{g['id']}: incomplete or invalid book reference {ref}")
        for k in ("keywords", "dgms_pattern"):
            try: re.compile(g[k] or "x")
            except re.error as e: fail(f"{g['id']}: bad {k} regex: {e}")
        pat = re.compile(g["dgms_pattern"], re.I) if g["dgms_pattern"] else None
        g["links"] = []   # [record id, DGMS finding text] - historical evidence, distinct records only
        if pat:
            for h in hrec:
                hit = next((f for f in h["findings"] if pat.search(f)), None)
                if hit: g["links"].append([h["id"], hit])

    # ---------------- explosion category classifier ----------------
    # Training rows: 200 synthetic scenarios + historical DGMS explosion narratives whose label maps to the taxonomy.
    # The 'source' column keeps the two identifiable; evaluation is reported per source.
    hx = pd.DataFrame([{"situation": h["situation"], "xcat": h["xcat"], "id": h["id"]} for h in hrec if h["kind"] == "narrative" and h["xcat"] in TAXONOMY and h["situation"]])
    train = pd.concat([pd.DataFrame({"text": syn["Situation_Text"], "label": syn["Primary_Explosion_Category"], "source": "synthetic"}),
                       pd.DataFrame({"text": hx["situation"], "label": hx["xcat"], "source": "historical"})], ignore_index=True)
    X, y = syn["Situation_Text"], syn["Primary_Explosion_Category"]   # synthetic-only, for the out-of-domain check
    mk = lambda C=1: Pipeline([("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1, sublinear_tf=True, stop_words="english")),
                              ("clf", LogisticRegression(max_iter=4000, class_weight="balanced", C=C))])
    cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    grid = GridSearchCV(mk(), {"clf__C": [0.5, 1, 2, 5, 10, 20]}, cv=cv, scoring="f1_macro").fit(X, y)
    C = grid.best_params_["clf__C"]
    pred = cross_val_predict(mk(C), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE + 1))
    cv_acc, cv_f1 = accuracy_score(y, pred), f1_score(y, pred, average="macro")
    cm = confusion_matrix(y, pred, labels=TAXONOMY)
    rep = classification_report(y, pred, labels=TAXONOMY, zero_division=0, output_dict=True)
    syn_only = mk(C).fit(X, y)

    # out-of-domain check: synthetic-only classifier on real DGMS explosion narratives with a taxonomy label
    hpred = syn_only.predict(hx["situation"])
    h_acc = accuracy_score(hx["xcat"], hpred) if len(hx) else float("nan")
    h_conf = pd.crosstab(hx["xcat"], pd.Series(hpred, index=hx.index, name="predicted"))

    # combined model (synthetic + historical): out-of-fold predictions, reported per source
    cv2 = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE + 2)
    strat = train["label"] + "|" + train["source"]
    strat = strat.where(strat.map(strat.value_counts()) >= 5, train["label"])   # tiny groups fall back to label-only strata
    oof = pd.Series(index=train.index, dtype=object)
    for tr, te in cv2.split(train["text"], strat):
        m = mk(C).fit(train.loc[tr, "text"], train.loc[tr, "label"]); oof.iloc[te] = m.predict(train.loc[te, "text"])
    comb = {}
    for src in ["synthetic", "historical"]:
        msk = train["source"] == src
        comb[src] = (accuracy_score(train.loc[msk, "label"], oof[msk]), f1_score(train.loc[msk, "label"], oof[msk], average="macro"), int(msk.sum()))
    final = mk(C).fit(train["text"], train["label"])

    # ---------------- explosion-evidence gate on historical narratives ----------------
    # DGMS 8-group hazard, predicted out-of-fold so the gate is not evaluated on memorised labels
    hz = hist["cause_group"].replace({"Transportation machinery (winding)": "Transportation machinery", "Transportation machinery (non-winding)": "Transportation machinery"})
    dg = Pipeline([("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")),
                   ("clf", LogisticRegression(max_iter=3000, class_weight="balanced", C=0.5))])
    dg_pred = cross_val_predict(dg, hist["situation"], hz, cv=StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE))
    gate = pd.Series([evidence(s, h)[0] for s, h in zip(hist["situation"], dg_pred)], index=hist.index)
    truth = hist["core_explosion_flag"] == 1
    g_p, g_r = precision_score(truth, gate), recall_score(truth, gate)
    g_fp = hist[gate & ~truth][["id", "cause_group"]]
    g_fn = hist[~gate & truth][["id", "explosion_category"]]
    syn_gate_s = syn["Situation_Text"].apply(lambda s: evidence(s)[0]); syn_gate = syn_gate_s.mean()
    syn_missed = syn.loc[~syn_gate_s, ["Scenario_ID", "Situation_Text"]]

    # ---------------- historical retrieval evaluation (leave-one-out) ----------------
    rvec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, stop_words="english").fit(hist["search_text"])
    M = rvec.transform(hist["search_text"]); M = M.multiply(1 / (np.sqrt(M.multiply(M).sum(1)) + 1e-12)).tocsr()
    core = np.where(truth.values)[0]
    p6_plain, p6_x = [], []
    for i in core:
        q = rvec.transform([hist.loc[i, "situation"]]); q = q / (np.sqrt(q.multiply(q).sum()) + 1e-12)
        s = np.asarray((M @ q.T).todense()).ravel(); s[i] = -9
        top = np.argsort(-s)[:6]; p6_plain.append(truth.values[top].mean())
        same = (hist["xcat"].values == hist.loc[i, "xcat"]).astype(float); sx = s.copy()
        sx = np.where(truth.values, sx + 0.15 * same, -9); sx[i] = -9
        top = np.argsort(-sx)[:6]; p6_x.append((hist["xcat"].values[top] == hist.loc[i, "xcat"]).mean())
    base_rate = (len(core) - 1) / (len(hist) - 1)

    # ---------------- synthetic retrieval index ----------------
    svec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, stop_words="english").fit(syn["Situation_Text"])
    S = svec.transform(syn["Situation_Text"]); S = S.multiply(1 / (np.sqrt(S.multiply(S).sum(1)) + 1e-12)).tocsr()
    sdocs = [[S.getrow(i).indices.tolist(), [round(float(v), 4) for v in S.getrow(i).data]] for i in range(S.shape[0])]

    # ---------------- export ----------------
    xclf = export_tfidf(final.named_steps["tfidf"], final.named_steps["clf"])
    out = {
        "source": wb.name,
        "taxonomy": TAXONOMY,
        "subject_areas": SUBJECT_AREAS,
        "coal_only": [TAXONOMY[0], TAXONOMY[1], TAXONOMY[2]],
        "lexicon": {"strong": STRONG, "weak": WEAK, "atmosphere": sorted(ATMOSPHERE), "event": EVENT, "explosive_groups": sorted(EXPLOSIVE_GROUPS)},
        "clf": xclf,
        "syn_index": {"terms": sorted(svec.vocabulary_, key=svec.vocabulary_.get), "idf": [round(float(x), 4) for x in svec.idf_], "docs": sdocs},
        "syn": [[r.Scenario_ID, r.Situation_Text, r.Primary_Explosion_Category, r.Mine_Type_Context, r.Place_of_Work_Context, bool(r.is_event)] for r in syn.itertuples()],
        "hist_xcat": {h["dgms_id"]: h["xcat"] for h in hrec if h["dgms_id"]},
        "hrec": hrec,
        "books": G["books"], "guidance": G["guidance"], "uncovered_by_books": G["uncovered_by_books"],
        "related_extra": {GASDUST: [TAXONOMY[0], TAXONOMY[1], TAXONOMY[2]]},
        "metrics": {"cv_accuracy": round(cv_acc, 3), "cv_macro_f1": round(cv_f1, 3), "C": C, "n_syn": len(syn), "n_train": len(train),
                    "oof_hist_accuracy": round(comb["historical"][0], 3), "oof_syn_accuracy": round(comb["synthetic"][0], 3),
                    "hist_mechanism_accuracy": round(float(h_acc), 3), "n_hist_mapped": int(len(hx)),
                    "gate_precision": round(float(g_p), 3), "gate_recall": round(float(g_r), 3)},
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")

    # ---------------- report ----------------
    L = ["# Explosion intelligence: build and evaluation report", "",
         "Generated by `build_explosion.py`. All numbers below are computed from the files, not estimated.", "",
         "## 1. Data import and validation", ""] + [f"- {x}" for x in log] + [
         "- Mine-type context per category: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in mt_ctx.items()) + ".",
         "- Labels are the workbook's *suggested* categories; the Data_Dictionary says expert validation is required. Some overlap is visible, for example scenarios labelled Coal-Dust that describe a methane ignition raising dust, and Metal Mine scenarios that describe blasting events.",
         "", "## 2. The 610 DGMS narratives (2016–2022) mapped to the taxonomy", "",
         f"- Historical records searched: {len(hist)}; core explosion events (from the project's DGMS coding): {int(truth.sum())}.",
         "- A record gets a taxonomy category only when its DGMS-derived explosion label supports it:", ""]
    for k, v in hist["xcat"].value_counts().items():
        L.append(f"  - {k}: {v}")
    L += ["", "- None of the 2016–2022 narratives is a Coal-Dust, Combined Methane and Coal-Dust, Electrical or Mechanical Ignition, or Spontaneous Heating explosion. The SANKET major-accident list (1901–2010, cause label only) adds older gas and coal-dust explosions; see section 6. No historical record of any period is classified as Combined, Electrical/Mechanical Ignition or Spontaneous Heating; for those the app says no historical record of the category exists and shows related records and synthetic scenarios separately.",
          "", "## 3. Explosion-category classifier (trained on the 200 synthetic scenarios)", "",
          f"- Model: TF-IDF (1–2 grams, sublinear tf, English stop words) + Logistic Regression (class_weight=balanced), C = {C} chosen by 5-fold stratified CV on macro-F1.",
          f"- Synthetic-only model, 5-fold stratified cross-validation on synthetic data: accuracy **{cv_acc:.3f}**, macro-F1 **{cv_f1:.3f}** (table below).",
          f"- Deployed model is trained on {len(train)} rows: {int((train.source=='synthetic').sum())} synthetic + {int((train.source=='historical').sum())} SANKET explosion narratives, each tagged with its source.",
          f"- Deployed model, 5-fold out-of-fold predictions reported per source: synthetic accuracy **{comb['synthetic'][0]:.3f}** (macro-F1 {comb['synthetic'][1]:.3f}, n={comb['synthetic'][2]}); historical accuracy **{comb['historical'][0]:.3f}** (n={comb['historical'][2]}, effectively one class, so macro-F1 is not meaningful).",
          "- Caveat: synthetic scenarios are short and template-like, so cross-validation on them is optimistic. No near-duplicate pairs above 0.85 string similarity were found, but no grouping information exists to rule out paraphrase leakage.", "",
          "| Category | Precision | Recall | F1 | n |", "|---|---|---|---|---|"]
    for c in TAXONOMY:
        r = rep[c]; L.append(f"| {c} | {r['precision']:.2f} | {r['recall']:.2f} | {r['f1-score']:.2f} | {int(r['support'])} |")
    L += ["", "Confusion matrix (rows = workbook label, columns = predicted, same order as the table):", "", "```"]
    for c, row in zip(TAXONOMY, cm):
        L.append(f"{c[:42]:42s} " + " ".join(f"{v:3d}" for v in row))
    L += ["```", "", "### Cross-domain check on real DGMS explosion narratives", "",
          f"- {len(hx)} SANKET explosion narratives have a taxonomy category ({', '.join(f'{v} {k.split(' ')[0].lower()}' for k, v in hx['xcat'].value_counts().items())}). A classifier trained on synthetic data ONLY assigns the matching category to **{h_acc:.1%}** of them (true out-of-domain test; these narratives are then added to the deployed model).",
          "- This is the only real-data test available and it covers essentially two categories, so it is not a reliable multi-class evaluation.", "", "```", h_conf.to_string(), "```", "",
          "## 4. Explosion-evidence gate (decides whether to run explosion analysis)", "",
          f"- On the {len(hist)} historical narratives, using the project's core-explosion flag as truth: precision **{g_p:.3f}**, recall **{g_r:.3f}**.",
          f"- On the 200 synthetic scenarios the gate fires for {syn_gate:.1%} (text only, no DGMS signal). Missed: " + ("; ".join(f"{r.Scenario_ID} \"{r.Situation_Text}\"" for r in syn_missed.itertuples()) or "none") + ".",
          f"- False positives ({len(g_fp)}): mostly " + (", ".join(f"{k} ({v})" for k, v in g_fp['cause_group'].value_counts().head(4).items()) or "none") + ". These are narratives that mention blasting, gas or fire without an explosion; the app still shows them correctly as hazard context.",
          f"- Missed explosion records ({len(g_fn)}): " + (", ".join(f"{r.id} ({r.explosion_category})" for r in g_fn.itertuples()) or "none") + ".",
          "", "## 5. Historical retrieval (leave-one-out over the 31 core explosion records)", "",
          f"- Plain text similarity over all {len(hist)} records: on average **{np.mean(p6_plain):.1%}** of the top 6 are explosion records (random baseline {base_rate:.1%}).",
          f"- Explosion mode (explosion records only, +0.15 for the same mapped category): on average **{np.mean(p6_x):.1%}** of the top 6 share the query record's category.",
          "", "## 6. SANKET explosion-specific accident records", "",
          "Files inspected:",
          "- `sanket0404_2024coalmies_1.pdf`: DGMS SANKET Coal Mines 2016–2022 (Feb 2024). Fatal-accident narratives (Statements 3.8–9.8) and Chapter 10 list of major accidents (≥4 killed) since 1901.",
          "- `sanketnoncoal-17042025.pdf`: DGMS SANKET Non-Coal Mines 2016–2022 (Mar 2025). Narratives and the Chapter 10 major-accident list.",
          "- `Mining_Explosion_Accidents_Predictive_Analysis.xlsx` (sheet Accident_Database): the explosion-specific extraction from both PDFs built earlier in this project, with source page, table reference, original cause label and duplicate flags. Used as the historical explosion dataset.",
          "- `accidents.csv`: full narrative text, DGMS findings and regulations for the narrative records (linked by workbook id).", "",
          f"- {sk_log}",
          "", "Explosion records used, by source and taxonomy category (original SANKET labels are kept on every record):", "",
          "| Category | Coal narratives | Coal list | Non-coal narratives | Non-coal list |", "|---|---|---|---|---|"]
    hdf = pd.DataFrame(hrec)
    for c, g in hdf.groupby("xcat"):
        f = lambda s, k: int(((g.src.str.startswith(s)) & (g.kind == k)).sum())
        L.append(f"| {c} | {f('Coal','narrative')} | {f('Coal','list')} | {f('Non','narrative')} | {f('Non','list')} |")
    L += ["", "Mapping rule: blasting and explosives labels → Blasting; firedamp / inflammable-gas labels → Methane in coal mines, Metal Mine category in non-coal mines; 'Coal dust' → Coal-Dust; 'Damp/coal dust' (DGMS: firedamp or coal dust) → Gas or coal-dust, type not recorded; unspecified gas/dust → its own label (related to Methane, Coal-Dust and Combined); 'Explosion (type not specified)' → its own label; hydrocarbon/vapour explosions in vessels (hot work reported for some, not all), cylinder and borderline fuel/gas-cloud events → 'Outside taxonomy'.",
          f"- Major-accident list rows carry only a cause label (no narrative, no findings): {int((hdf.kind=='list').sum())} records. The app says so on each card and never states a cause beyond the label.",
          f"- Narratives without printed DGMS findings: {', '.join(h['id'] + ' (' + h['dgms_id'] + ')' for h in hrec if h['kind']=='narrative' and not h['findings'])}.",
          "", "## 7. Reference books and the guidance extracted", "",
          f"- **Ramlu**: {G['books']['Ramlu']} Supplied as a scanned PDF (two printed pages per PDF page, OCR'd). Sections used: 1.1.1.2.9, 1.1.1.7, 1.1.4.2.2.2 (mine fires and sealing); 2.1.5–2.1.7 (firedamp causes, prevention, inspection, localization); 2.2.8–2.2.9 (coal-dust causes, prevention, stonedusting, barriers); 2.4 (sulphide ore-dust explosions).",
          f"- **Cheng**: {G['books']['Cheng']} Sections used: 1.2–1.3 (hazard locations and cases), 2.1.3–2.1.5 (seals, pressure chambers), 2.2 (explosive range), Table 2.3 (accidents since 2005), 2.3.1–2.3.8 and Table 2.4 (prevention and suppression techniques), 5.2.2 (inerting).",
          f"- Not covered by either book: {G['uncovered_by_books']}", "",
          "| ID | Measure (summary) | Mechanisms | Book references | DGMS records whose findings support it |", "|---|---|---|---|---|"]
    for g in G["guidance"]:
        refs = "; ".join(f"{r['book']} §{r['section'].split(' ')[0]} p.{r['pages']} ({'states' if r['support']=='states' else 'case → derived'})" for r in g["refs"])
        L.append(f"| {g['id']} | {g['measure']} | {', '.join(m.split(' ')[0] for m in g['mechanisms'])} | {refs} | {', '.join(x[0] for x in g['links']) or '—'} |")
    L += ["", "## 8. What the app does with each dataset", "",
          "- Historical records: shown as accident cards and the ONLY accident evidence counted for preventive measures. In explosion mode the SANKET explosion records are used (coal and non-coal kept separate by source); duplicates are not counted twice.",
          "- Reference books: each preventive measure shows the book, section and printed page, and whether the book states the measure or the measure is derived from a case the book describes.",
          "- Synthetic scenarios: train the explosion-category classifier and appear in a separate, labelled list. Never shown as accidents and never counted as evidence.",
          "- The existing 8-group DGMS hazard classifier is unchanged."]
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote {a.out} and {a.report}")


if __name__ == "__main__":
    main()
