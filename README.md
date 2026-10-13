# Mine Hazard Advisor

Type the job you are about to do in a mine (a sentence, or just a word like "truck", "blasting", "methane", "chhat") and the site shows:

- **Most likely hazard**: one of 8 DGMS cause groups (TF-IDF + Logistic Regression)
- **Explosion analysis** (only when the description contains explosion evidence): the predicted explosion mechanism, the words behind it, mine context, and whether the text describes a potential hazard or an explosion event
- **Preventive measures**: grouped from the DGMS "the accident could have been averted had…" findings of the closest **historical** accidents
- **Historical records**: DGMS SANKET accidents, six at a time
- **Synthetic training scenarios**: a separate, clearly labelled list (never shown as accidents, never counted as evidence)

Everything runs in the browser. There is no server and nothing you type leaves the page (except the optional Claude button inside claude.ai).

## Data

| Dataset | File | Role |
|---|---|---|
| A. Historical DGMS accidents | `data/accidents.csv` | 610 searchable fatal-accident narratives (DGMS SANKET coal and non-coal reports, 2016–2022), used for general hazards |
| B. SANKET explosion records | `data/Mining_Explosion_Accidents_Predictive_Analysis.xlsx` (Accident_Database) | 87 explosion accidents from both SANKET reports after removing 2 duplicates and 4 non-explosion rows: 34 narratives with DGMS findings and 53 major-accident list rows (1901–2022, cause label only). Coal and non-coal are kept separate; original cause labels are kept |
| C. Synthetic explosion scenarios | `data/explosion_specific_mining_scenarios_200.xlsx` | 200 generated scenarios; training and a separate labelled list only, never evidence |
| D. Reference-book guidance | `data/reference_guidance.json` | 23 preventive measures from Ramlu, *Mine Disasters and Mine Rescue*, and Cheng, *Explosions in Underground Coal Mines* (2018), each with section, printed page and whether the book states it or it is derived from a case |

Historical records carry the label **Historical — DGMS source** (traceable to the PDF page shown, not individually re-verified). Synthetic rows carry **Synthetic — training scenario**, plus **Potential hazard — not a confirmed explosion** when the text describes a condition rather than an event.

## Preventive measures in explosion mode

Each measure shows its evidence status, the book section and page, and the DGMS findings that support it, which open under "Evidence and references". Measures come from three places, kept apart:

- **Reference-book guidance**: "Stated in Ramlu / Cheng / both books", or "Derived from a case in the book".
- **Historical evidence**: DGMS "the accident could have been averted had…" findings of SANKET explosion accidents, counted once per accident.
- **DGMS findings only**: measures that neither book covers. Neither book discusses blasting misfires, lightning, flyrock or blasting shelters, which cause most 2016–2022 explosion accidents.

The list is ordered by how many of the matched accidents support each measure, and it changes with the predicted mechanism, the mine type and the description.

## Explosion taxonomy

Methane / Firedamp · Coal-Dust · Combined Methane and Coal-Dust · Blasting and Explosives-Related · Electrical or Mechanical Ignition of Explosive Atmosphere · Spontaneous Heating, Fire and Explosion Escalation · Metal Mine: Gas, Dust and Other Mechanisms.

Historical DGMS records cover only two of these (27 blasting, 1 methane). For the others the site shows related mechanisms or synthetic scenarios and says so.

## Models and evaluation

See [`reports/explosion_evaluation.md`](reports/explosion_evaluation.md) for every number and the full source/guidance tables, and [`reports/explosion_validation.md`](reports/explosion_validation.md) for the 10-case validation run.

- DGMS hazard classifier: 70.5% accuracy / 0.62 macro-F1 on unseen 2021–22 accidents (23% majority baseline).
- Explosion-category classifier: trained on 200 synthetic + 28 historical narratives; synthetic-only 5-fold CV macro-F1 0.66; synthetic-only model on real DGMS explosion narratives 85.7% (out-of-domain, mostly one class).
- Explosion-evidence gate on 610 historical narratives: precision 0.79, recall 0.87.

## Build

```bash
pip install pandas scikit-learn openpyxl
python build_model.py                              # DGMS hazard classifier + search index -> model/model.json
python build_explosion.py   # --workbook / --sanket / --guidance PATHS (or EXPLOSION_WORKBOOK, SANKET_EXPLOSION_WORKBOOK, REFERENCE_GUIDANCE); validates, trains, evaluates -> model/explosion.json + reports
python build_site.py                               # template.html + both model files -> index.html
```

`build_explosion.py` stops with a clear error if the workbook is missing, a column or sheet is absent, IDs repeat, cells are blank, categories are unknown, or any row is not marked synthetic. If the page is ever built without the explosion data, it shows a diagnostic banner and keeps general hazard analysis working.

## Disclaimer

Decision support only. This does not replace the mine's Safety Management Plan, SOPs, statutory permissions or the judgement of a competent person. Synthetic scenarios are examples, not evidence.
