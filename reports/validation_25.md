# 25-situation validation: Mine Hazard Advisor

Run on 14 October 2026 against the built page (`index.html`) in headless Chromium. Each situation was typed into the Situation box exactly as written, with Place of work and Mine type left at **Any**, and submitted with **Find precedents**. Everything below comes from what the page displayed; nothing was filled in by hand.

**Full results:** [`validation_25.csv`](validation_25.csv) has one row per test with all 13 required columns: Test_ID, Input_Situation, Expected_Behaviour, Actual_Prediction, Actual_Confidence, Top_Hazard_Groups, Historical_Records, Record_Relevance, Preventive_Measures, Evidence_References, False_Positive, Test_Status and Findings.

## Summary

| | Baseline (before fixes) | Final (after fixes) |
|---|---|---|
| Pass | 13 | **21** |
| Partial | 11 | **4** (TEST-15, 16, 17, 19) |
| Fail | 1 (TEST-12) | **0** |
| Not tested | 0 | 0 |
| False-positive explosion results | 0 | **0** |

All five non-explosion situations (TEST-21 to TEST-25) produced no explosion analysis, both before and after the fixes. All 20 explosion situations were tagged as **potential hazard, not a confirmed explosion** after the fixes. None of the 20 reports a completed explosion.

| Test | Input (abridged) | Actual prediction | Confidence | Top historical records | False positive | Baseline | Final |
|---|---|---|---|---|---|---|---|
| TEST-01 | Methane accumulates near the roof of an underground coal mine working… | Methane / Firedamp Explosion — potential hazard, not a confirmed explosion | 66% explosion-category match (Strong match) | EXP-01, C-HIST-171, C-HIST-159, C-HIST-153, C-HIST-117, C-HIST-091 | No | Partial | **Pass** |
| TEST-02 | An auxiliary ventilation fan stops working in an underground coal hea… | Methane / Firedamp Explosion — potential hazard, not a confirmed explosion | 66% explosion-category match (Strong match) | C-HIST-171, C-HIST-159, EXP-01, C-HIST-004, C-HIST-074, C-HIST-067 | No | Pass | **Pass** |
| TEST-03 | Dry coal dust accumulates along underground roadways and is dispersed… | Coal-Dust Explosion — potential hazard, not a confirmed explosion | 42% explosion-category match (Strong match) | C-HIST-191, EXP-01, C-HIST-171, C-HIST-159, C-HIST-153, C-HIST-117 | No | Pass | **Pass** |
| TEST-04 | A methane ignition in an underground coal mine disperses deposited co… | Combined Methane and Coal-Dust Explosion — potential hazard, not a confirmed ex… | 55% explosion-category match (Strong match) | EXP-01, C-HIST-191, C-HIST-171, C-HIST-159, C-HIST-153, C-HIST-117 | No | Pass | **Pass** |
| TEST-05 | Electrical equipment produces a spark in an underground coal working … | Ambiguous: Electrical or Mechanical Ignition of Explosive Atmosphere or Methane… | 35% explosion-category match (Uncertain) | C-HIST-171, C-HIST-159, EXP-01, C-HIST-004, EXP-02 | No | Partial | **Pass** |
| TEST-06 | A worker begins drilling near a previously charged blast hole in an u… | Blasting and Explosives-Related Explosion — potential hazard, not a confirmed e… | 37% explosion-category match (Strong match) | NC-11, NC-10, EXP-11, NC-03, NC-04, NC-05 | No | Pass | **Pass** |
| TEST-07 | Blasting is planned at an underground coal face, but the required gas… | Methane / Firedamp Explosion — potential hazard, not a confirmed explosion | 43% explosion-category match (Strong match) | EXP-01, C-HIST-171, C-HIST-159, C-HIST-004, C-HIST-074, C-HIST-067 | No | Pass | **Pass** |
| TEST-08 | A methane drainage system becomes ineffective in a gassy underground … | Methane / Firedamp Explosion — potential hazard, not a confirmed explosion | 35% explosion-category match (Strong match) | EXP-01, C-HIST-171, C-HIST-159, C-HIST-004, C-HIST-074, C-HIST-067 | No | Partial | **Pass** |
| TEST-09 | After blasting in an underground coal working, ventilation and gas co… | Methane / Firedamp Explosion — potential hazard, not a confirmed explosion | 53% explosion-category match (Strong match) | EXP-01, C-HIST-171, C-HIST-159, C-HIST-004, C-HIST-074, C-HIST-067 | No | Pass | **Pass** |
| TEST-10 | Coal in an abandoned underground working shows signs of spontaneous h… | Spontaneous Heating, Fire and Explosion Escalation — potential hazard, not a co… | 69% explosion-category match (Strong match) | C-HIST-004, NC-21, EXP-02, EXP-01, C-HIST-001 | No | Partial | **Pass** |
| TEST-11 | A drilling crew approaches a blasted face in an underground metal min… | Blasting and Explosives-Related Explosion — potential hazard, not a confirmed e… | 27% explosion-category match (Moderate match) | NC-11, NC-10, EXP-11, NC-04, NC-05, NC-07 | No | Partial | **Pass** |
| TEST-12 | Explosives are being handled at an underground metal-mine blasting si… | Blasting and Explosives-Related Explosion — potential hazard, not a confirmed e… | 25% explosion-category match (Moderate match) | NC-18, NC-03, NC-04, EXP-05, NC-05, NC-09 | No | Fail | **Pass** |
| TEST-13 | Electrical equipment develops an arc in a metal-mine working where a … | Ambiguous: Metal Mine: Gas, Dust and Other Explosion Mechanisms or Electrical o… | 33% explosion-category match (Uncertain) | N-HIST-087, EXP-02, NC-22, NC-21 | No | Partial | **Pass** |
| TEST-14 | Fine combustible dust accumulates inside a metal-ore processing facil… | Metal Mine: Gas, Dust and Other Explosion Mechanisms — potential hazard, not a … | 66% explosion-category match (Strong match) | N-HIST-087, C-HIST-191 | No | Pass | **Pass** |
| TEST-15 | Diesel fuel vapours accumulate in a poorly ventilated underground met… | Metal Mine: Gas, Dust and Other Explosion Mechanisms — potential hazard, not a … | 48% explosion-category match (Strong match) | N-HIST-087, NC-21, NC-20 | No | Partial | **Partial** |
| TEST-16 | A blasting crew prepares a shot near old underground metal-mine worki… | Ambiguous: Blasting and Explosives-Related Explosion or Metal Mine: Gas, Dust a… | 32% explosion-category match (Uncertain) | NC-03, NC-04, NC-09, EXP-05, NC-07, NC-05 | No | Partial | **Partial** |
| TEST-17 | Following blasting in an underground metal mine, workers encounter an… | Metal Mine: Gas, Dust and Other Explosion Mechanisms — potential hazard, not a … | 65% explosion-category match (Strong match) | NC-03, NC-04, EXP-05, NC-05, NC-09, NC-07 | No | Partial | **Partial** |
| TEST-18 | Combustible dust accumulates in a metal-processing plant's dust colle… | Metal Mine: Gas, Dust and Other Explosion Mechanisms — potential hazard, not a … | 50% explosion-category match (Strong match) | N-HIST-087, C-HIST-191 | No | Partial | **Pass** |
| TEST-19 | A fire develops near stored combustible materials in an underground m… | Metal Mine: Gas, Dust and Other Explosion Mechanisms — potential hazard, not a … | 38% explosion-category match (Strong match) | N-HIST-087, NC-21, EXP-02, NC-20, NC-22 | No | Partial | **Partial** |
| TEST-20 | A damaged gas cylinder or gas supply line leaks in a mine workshop ne… | Ambiguous: Metal Mine: Gas, Dust and Other Explosion Mechanisms or Electrical o… | 30% explosion-category match (Uncertain) | EXP-02, NC-21, NC-20, N-HIST-087, NC-22 | No | Pass | **Pass** |
| TEST-21 | A dumper reverses near the edge of an opencast mine dump yard. | No explosion analysis; general hazard: Transportation machinery | 54% DGMS hazard-group match (Strong match) | Not applicable (general DGMS mode: Showing 1–6 of 478 matching record… | No | Pass | **Pass** |
| TEST-22 | A worker cleans spilled coal from a stopped conveyor belt. | No explosion analysis; general hazard: Transportation machinery | 23% DGMS hazard-group match (Moderate match) | Not applicable (general DGMS mode: Showing 1–6 of 413 matching record… | No | Pass | **Pass** |
| TEST-23 | Loose rock falls from the roof of an underground metal mine. | No explosion analysis; general hazard: Ground movement | 36% DGMS hazard-group match (Strong match) | Not applicable (general DGMS mode: Showing 1–6 of 377 matching record… | No | Pass | **Pass** |
| TEST-24 | An electrician repairs an isolated cable after verifying that no haza… | No explosion analysis; general hazard: Electricity | 57% DGMS hazard-group match (Strong match) | Not applicable (general DGMS mode: Showing 1–6 of 369 matching record… | No | Pass | **Pass** |
| TEST-25 | Water accumulates in a mine roadway following heavy rainfall. | No explosion analysis; general hazard: Other causes | 35% DGMS hazard-group match (Moderate match) | Not applicable (general DGMS mode: Showing 1–6 of 117 matching record… | No | Pass | **Pass** |

## Root causes of the baseline failures and partial results

| # | Root cause | Tests affected | Fix |
|---|---|---|---|
| 1 | The event detector counted "explosion" words even when hedged. "A potential firedamp explosion hazard" was read as an explosion that happened, so the potential-hazard tag was missing. | 01 | New `is_event()` rule in `build_explosion.py`, mirrored in the page: an event word preceded by hedging ("potential", "risk of", "conditions for", "could", "may" and similar) or followed by "hazard" or "risk" is not an event. |
| 2 | The explosives pattern matched the adjective in "explosive gas", adding false explosives evidence and pulling in blasting records. | 08 | The pattern now excludes "explosive" when followed by gas, atmosphere, mixture, range, limit, dust, concentration, conditions or methane. "Explosive gas" is still caught as a flammable-atmosphere term. |
| 3 | Measure ordering. Within the list, measures were ranked only by how many matched accidents supported them, so generic machine-isolation and supervision findings outranked the mechanism's own book measures. | 05, 10, 13 (and 06) | Measures are now grouped first by mechanism, then ranked by match to the description. Group 0 holds book measures for the predicted mechanism that match the description or the matched accidents, plus DGMS findings from accidents of the same mechanism. Within a group, ranking is by words of the description matched, then accident support (capped at 2), then whether the measure belongs to the top class. |
| 4 | When the classifier was undecided between two mechanisms, guidance came only from the top class. The electrical-ignition measures never appeared for a metal-mine arc. | 13 | When the result is uncertain, guidance for the runner-up class is also considered. A coal-dust class is never added unless the description or mine type says coal. |
| 5 | G11 ("where firedamp may be present…") applied to any "underground" text, and its keyword `fir` matched "fire". So metal-mine blasting without gas, fires and gas leaks all received a firedamp-blasting measure. G15 had the same `fir` fragment. | 11, 12, 16, 19, 20 | G11 now applies only where coal, gas, gassy, methane, firedamp or seam is mentioned. Keyword `fir` became `firing` in G11 and G15. |
| 6 | G01 (dilute flammable gas by ventilation) missed phrasing like "accumulation of … flammable gas". | 17 | G01 keywords extended to "flammable / inflammable / explosive / combustible gas" and "accumulation of … gas". |
| 7 | Label-only major-accident rows have one-label vectors, so a single shared word ("Explosives") gave them a cosine of 0.25. They outranked narratives that carry DGMS findings, leaving no findings to draw measures from. | 12 | For ranking, a label-only row's similarity is capped at 0.10. Confirmed mechanisms rank slightly ahead of "type not recorded" rows. |
| 8 | Any narrative sharing generic words (sim ≥ 0.15) was admitted, which brought an oil-tank vapour explosion into a dust-collector search. | 18 | The wording-only threshold was raised to 0.25 (narratives only). |
| 9 | Equivalent misfire wording ("unexploded charge", "previous blast holes", "old holes") was not recognised. | 11 (16 partly) | Added to the plain-words dictionary used for retrieval and to the misfire theme. Lightning findings that mention "charged holes" are deliberately not regrouped (0 findings newly grouped). |
| 10 | Situation-specific inspector-finding themes (lightning, mobile phone) appeared when the description did not mention them. | 16, 17 | These themes are now shown only when the description mentions a storm, lightning, rain, phone or radio. |
| 11 | The uncertainty message said "not enough detail" for long, detailed descriptions whose uncertainty came from overlapping classes. | 05, 13, 16, 20 | Three messages now: short input asks for more detail; a near tie (top two within 10 points) says two mechanisms fit about equally; a top class below 35% says the match is weak. It mentions measures for both classes only when they are actually used. |
| 12 | Found while checking the 10-case regression: the machine-isolation theme's finding pattern contains "stopped". A description saying the auxiliary fan "stopped" therefore lifted "Stop the machine and isolate the power" to 3rd for a ventilation failure. | 10-case validation, case 1 | Theme matching against the description uses a stricter pattern where needed (isolation: isolate, lock-out, permit to work, de-energise). The 25 test results were unchanged by this fix. |

No answer is hard-coded for any of the 25 inputs. Each fix changes a general rule, and the 10-case validation, the 21-test audit suite and the 9 dust regressions were rerun after every change.

## Why four tests remain Partial

These are limits of the evidence, not software defects:

- **TEST-15 (diesel vapour):** neither book covers flammable vapour in a mine workshop. The displayed measures (ventilation dilution, written for firedamp; hot-work precautions, linked through vessel-explosion records) apply only indirectly.
- **TEST-16 (blasting near old workings):** the description best matches charging-in-progress accidents. The misfire accidents rank 8th and later, so the inspector-finding measures stay generic. Forcing misfire records to the top would mean inventing a misfire the text does not report.
- **TEST-17 (gas found after blasting, metal mine):** no historical record of this kind exists. The records shown are blasting accidents, offered as context.
- **TEST-19 (fire escalation, metal mine):** neither book covers fire escalation in metal mines, and no SANKET record of it exists.

## Source validation of the retrieved records

- **Records retrieved:** 80 distinct historical records across the 25 tests (33 narratives, 47 major-accident list rows). All are among the 87 SANKET records checked against the PDFs on 13 October; the same checks were rerun today:
  - all 53 list rows: date, killed and injured match the PDF row;
  - all 34 narratives: mine, date, killed, narrative and first finding match the cited page.
- **What each record documents:**
  - 32 narratives describe an explosion, detonation or blast.
  - One, EXP-04 (Nawapara), is a blasting-projectile accident: shots fired and flying coal fragments.
  - 33 list rows carry an explosion or ignition label.
  - 14 list rows carry only "Explosives" or "Other explosive accident". The source does not describe an explosion for these, and the app tags them "Cause label only".
- **Duplicates:** neither of the merged duplicates (C-HIST-283, N-HIST-104) was retrieved, and no result list repeated an ID.
- **Synthetic scenarios:** no synthetic scenario appeared in any historical list. The 200 scenarios stay in their own labelled list.
- **Unknown values stay unknown.** For example, the serious-injury counts for NC-12 and NC-13 are shown as not recorded.

## Preventive-measure references

- **References displayed:** every book measure shown in the 25 runs comes from `data/reference_guidance.json`. Its 40 page references were each located on the cited printed page of the books on 13 October.
- **What changed today:** only matching keywords and contexts (G01, G11, G15, G22). Every measure text and every book reference is byte-identical to the audited version.
- **Labelling:** measures marked "DGMS findings only" come from inspector findings of the matched accidents (IDs are in the CSV), and their cards say "Neither book covers this".
- **Measures needing further verification:**
  - G06 (flameproof apparatus) when shown for a metal mine: Ramlu states it for coal mines.
  - G01 when shown for a non-firedamp gas or vapour (TEST-15, TEST-17): the ventilation-dilution principle is applied beyond the book's firedamp context.

## Confidence and ranking

- **Explosion panel:** the figure is the explosion classifier's softmax probability for the displayed class (logistic regression over TF-IDF), labelled "explosion-category confidence … not the chance of an explosion".
- **General-hazard panel:** labelled "not the probability of an accident". No score was changed.
- **Uncertainty:** any class below 35%, or within 10 points of the runner-up, is shown as uncertain. The metal-mine blasting rule and the non-coal dust rule both state when they override the top class.
- **Ranking:** in explosion mode the explosion analysis is shown first. When the general model cannot place the description (below 20%), its ranking is hidden and the highest group is reported in one line.
- **Short vs full descriptions:** "Combustible processing dust" gets a request for more detail. TEST-14 and TEST-18 (full descriptions) get a confident non-coal dust classification (66%, 50%).
- **Equivalent terms:** these are recognised through the plain-words dictionary and the evidence lexicon, not exact phrases only. Examples: "unexploded charge" = misfire; "flammable gas accumulation" triggers the ventilation measure.

## Regression results after all fixes

| Suite | Result |
|---|---|
| 25 situations (this report) | 21 Pass, 4 Partial, 0 Fail, 0 false positives |
| Audit suite (17 scenarios + extras, incl. 6-per-page pagination with no duplicates, coal/metal filter, empty state, synthetic separation, duplicate merge) | 21 / 21 |
| 10-case explosion validation | runs clean. Changes are the intended ones: ventilation measures lead the fan-stoppage case; the lightning measure rises where a thunderstorm is described; the sulphide-ore case now leads with Ramlu's sulphide-dust measure and no longer shows the firedamp-blasting measure; the confirmed coal-dust record leads the coal-dust case |
| Combustible-dust regression (9 inputs from the 14 October fix) | unchanged: dust inputs give insufficient-evidence notices, no coal measures |
| Explosion Causes chart reconciliation | 864 / 864 filter combinations reconcile; synthetic and duplicate records excluded |
| General-mode search, examples, browse, navigation | all pass, no page errors |
| Phone layout (320, 390, 768 px) | placeholder fully visible, tabs inside screen, no sideways scrolling |
| Gate metrics on 610 DGMS narratives | precision 0.794, recall 0.871 (unchanged); classifier metrics unchanged |

## Files changed

- `build_explosion.py`: `is_event()` with hedging; explosives pattern excludes the adjective "explosive"; hedge patterns exported to the page.
- `template.html` (built into `index.html`):
  - event hedging;
  - measure grouping and ranking;
  - guidance from both classes when uncertain (no coal-dust class without a coal context);
  - list-row similarity cap and stricter wording fallback;
  - misfire synonyms;
  - situation-specific theme triggers;
  - the three uncertainty messages.
- `data/reference_guidance.json`: G01 keywords; G11 context and keywords; G15 keywords. Book references untouched.
- `model/explosion.json` and `reports/explosion_evaluation.md`: regenerated.
- New: `reports/validation_25.md` and `reports/validation_25.csv`.

## Readiness

**Ready for presentation, with stated limitations.** All 25 situations were executed. The explosion-related ones are classified as potential hazards of a supported mechanism, and the unrelated hazards are never forced into an explosion category. Retrieved records are traceable to the SANKET PDFs, and the measures shown are book- or DGMS-backed. The four Partial results reflect evidence that does not exist, either in the SANKET records or in the two books (diesel vapour, gas after blasting in metal mines, metal-mine fire escalation). Present them as known gaps. The synthetic scenario labels still need the expert validation their own data dictionary requires.
