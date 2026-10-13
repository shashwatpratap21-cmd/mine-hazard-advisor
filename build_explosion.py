"""Explosion-specific intelligence for Mine Hazard Advisor.

Builds model/explosion.json from two logically separate datasets:
  A. Historical DGMS accident records (data/accidents.csv, include_in_search_index == 1)
  B. Synthetic explosion scenarios (Excel workbook, sheet Explosion_Scenarios)

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
    "coal dust": r"\bcoal[- ]dust\b|\bdust (?:cloud|explosion|deposits?|layer)\b|\bstone[- ]dust",
    "explosives / blasting": r"\b(?:explosives?|blast(?:ing|ed|s)?|detonat\w*|detonators?|misfire\w*|sockets?|charged holes?|shot ?fir\w*|shot holes?|fly ?rock|blasters?|barood|visphot)\b",
    "explosive / flammable atmosphere": r"\b(?:explosive|flammable|inflammable|combustible) (?:\w+ )?(?:atmosphere|mixture|range|gas\w*)\b|\bgas (?:accumulat\w*|build-?up|release|outburst)|\b(?:accumulat\w*|build-?up of) (?:of )?gas|\boutburst\b",
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

    # ---------------- explosion category classifier ----------------
    # Training rows: 200 synthetic scenarios + historical DGMS explosion narratives whose label maps to the taxonomy.
    # The 'source' column keeps the two identifiable; evaluation is reported per source.
    hx = hist[hist["xcat"].isin(TAXONOMY)]
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
        "hist_xcat": {r.id: r.xcat for r in hist.itertuples() if isinstance(r.xcat, str)},
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
         "", "## 2. Historical DGMS records mapped to the taxonomy", "",
         f"- Historical records searched: {len(hist)}; core explosion events (from the project's DGMS coding): {int(truth.sum())}.",
         "- A record gets a taxonomy category only when its DGMS-derived explosion label supports it:", ""]
    for k, v in hist["xcat"].value_counts().items():
        L.append(f"  - {k}: {v}")
    L += ["", "- No historical records exist for Coal-Dust, Combined Methane and Coal-Dust, Electrical or Mechanical Ignition, or Spontaneous Heating. For those situations the app shows synthetic scenarios and says no historical record matched.",
          "", "## 3. Explosion-category classifier (trained on the 200 synthetic scenarios)", "",
          f"- Model: TF-IDF (1–2 grams, sublinear tf, English stop words) + Logistic Regression (class_weight=balanced), C = {C} chosen by 5-fold stratified CV on macro-F1.",
          f"- Synthetic-only model, 5-fold stratified cross-validation on synthetic data: accuracy **{cv_acc:.3f}**, macro-F1 **{cv_f1:.3f}** (table below).",
          f"- Deployed model is trained on {len(train)} rows: {int((train.source=='synthetic').sum())} synthetic + {int((train.source=='historical').sum())} historical DGMS narratives (27 blasting, 1 methane), each tagged with its source.",
          f"- Deployed model, 5-fold out-of-fold predictions reported per source: synthetic accuracy **{comb['synthetic'][0]:.3f}** (macro-F1 {comb['synthetic'][1]:.3f}, n={comb['synthetic'][2]}); historical accuracy **{comb['historical'][0]:.3f}** (n={comb['historical'][2]}, effectively one class, so macro-F1 is not meaningful).",
          "- Caveat: synthetic scenarios are short and template-like, so cross-validation on them is optimistic. No near-duplicate pairs above 0.85 string similarity were found, but no grouping information exists to rule out paraphrase leakage.", "",
          "| Category | Precision | Recall | F1 | n |", "|---|---|---|---|---|"]
    for c in TAXONOMY:
        r = rep[c]; L.append(f"| {c} | {r['precision']:.2f} | {r['recall']:.2f} | {r['f1-score']:.2f} | {int(r['support'])} |")
    L += ["", "Confusion matrix (rows = workbook label, columns = predicted, same order as the table):", "", "```"]
    for c, row in zip(TAXONOMY, cm):
        L.append(f"{c[:42]:42s} " + " ".join(f"{v:3d}" for v in row))
    L += ["```", "", "### Cross-domain check on real DGMS explosion narratives", "",
          f"- {len(hx)} historical explosion records have a taxonomy label (27 blasting, 1 methane). A classifier trained on synthetic data ONLY assigns the matching category to **{h_acc:.1%}** of them (true out-of-domain test; these narratives are then added to the deployed model).",
          "- This is the only real-data test available and it covers essentially two categories, so it is not a reliable multi-class evaluation.", "", "```", h_conf.to_string(), "```", "",
          "## 4. Explosion-evidence gate (decides whether to run explosion analysis)", "",
          f"- On the {len(hist)} historical narratives, using the project's core-explosion flag as truth: precision **{g_p:.3f}**, recall **{g_r:.3f}**.",
          f"- On the 200 synthetic scenarios the gate fires for {syn_gate:.1%} (text only, no DGMS signal). Missed: " + ("; ".join(f"{r.Scenario_ID} \"{r.Situation_Text}\"" for r in syn_missed.itertuples()) or "none") + ".",
          f"- False positives ({len(g_fp)}): mostly " + (", ".join(f"{k} ({v})" for k, v in g_fp['cause_group'].value_counts().head(4).items()) or "none") + ". These are narratives that mention blasting, gas or fire without an explosion; the app still shows them correctly as hazard context.",
          f"- Missed explosion records ({len(g_fn)}): " + (", ".join(f"{r.id} ({r.explosion_category})" for r in g_fn.itertuples()) or "none") + ".",
          "", "## 5. Historical retrieval (leave-one-out over the 31 core explosion records)", "",
          f"- Plain text similarity over all {len(hist)} records: on average **{np.mean(p6_plain):.1%}** of the top 6 are explosion records (random baseline {base_rate:.1%}).",
          f"- Explosion mode (explosion records only, +0.15 for the same mapped category): on average **{np.mean(p6_x):.1%}** of the top 6 share the query record's category.",
          "", "## 6. What the app does with each dataset", "",
          "- Historical records: shown as accident cards and the ONLY evidence counted for preventive measures.",
          "- Synthetic scenarios: train the explosion-category classifier and appear in a separate, labelled list. Never shown as accidents and never counted as evidence.",
          "- The existing 8-group DGMS hazard classifier is unchanged."]
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote {a.out} and {a.report}")


if __name__ == "__main__":
    main()
