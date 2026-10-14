# Final audit: Mine Hazard Advisor

Project: **Predictive Analysis of Coal and Metal Mining Accidents Pertaining to Explosions from the Data Across Mines.**
Audit date: 13 October 2026. All counts below were computed from the files during the audit; test results come from runs of the built page in headless Chromium.

## Sources inspected

| Source | Status | How it was checked |
|---|---|---|
| `sanket0404_2024coalmies_1.pdf` (DGMS SANKET coal, 316 pp.) | Inspected | Text extracted page by page; every coal record checked against its cited page |
| `sanketnoncoal-17042025.pdf` (DGMS SANKET non-coal, 355 pp.) | Inspected | Same, for every non-coal record |
| `Mining_Explosion_Accidents_Predictive_Analysis.xlsx` (SANKET explosion workbook, 11 sheets) | Inspected | Accident_Database (93 rows) compared field by field with the app data |
| `accidents.csv` (610 DGMS narratives) | Inspected | Hazard model rebuilt from it; output reproduced byte-identical |
| `explosion_specific_mining_scenarios_200.xlsx` | Inspected | Sheets, IDs, duplicates, labels, mine context, synthetic marking |
| Ramlu, *Mine Disasters and Mine Rescue* (scanned PDF, OCR) | Inspected | Every Ramlu reference located on its cited printed page |
| Cheng, *Explosions in Underground Coal Mines* (2018) | Inspected | Every Cheng reference located on its cited printed page |
| GitHub repository and GitHub Pages site | Inspected | Git state before and after; live page checked after push (see D) |

## A. Data integrity

- **Records inspected:** 93 rows in the SANKET explosion workbook (37 fatal-accident narratives, 56 major-accident list rows).
- **Retained:** 87 explosion records: 55 coal, 32 non-coal (26 non-metallic mineral, 3 metal ore, 3 oil and gas); 34 narratives and 53 list rows.
- **Merged as duplicates (2):** C-HIST-283 is EXP-09 (Ramagundam OC-I, 2 June 2020); N-HIST-104 is NC-17 (C. Kasturi Bai Barytes, 8 May 2021). Each is counted once; the card notes the other listing.
- **Excluded as out of scope (4):** EXP-14 (dumper fuel-air fire, coded 0335 Dumpers), EXP-13 (coded Explosives but the narrative describes no explosion), NC-23 (gas-cloud flash fire, coded 0775 Fire), C-HIST-259 (air blast, classified under ground movement). The source workbook marks all four as non-core.
- **Possible further duplicates:** none found by mine name and year.
- **Checked against the PDFs:**
  - All 53 list rows: date, killed and injured match the PDF row with the cited serial number.
  - All 34 narratives: mine name, date, killed count, narrative text and first DGMS finding found on the cited page.
  - Injured counts agree with each narrative's wording (serious injuries only, as in the workbook).
- **Fatalities:** 1,418 killed in the 87 unique records; 185 seriously injured where recorded.
- **Defects found and fixed:**
  1. NC-12 and NC-13: the source says the serious-injury count cannot be attributed, but the app showed 0. It now keeps the value unknown and says so on the card.
  2. "Explosions of damp/coal dust" (C-HIST-001, Tikkak 1901): DGMS means firedamp *or* coal dust, but it was mapped to Combined Methane and Coal-Dust. It is now "Gas or coal-dust explosion, type not recorded". No historical record is now classified as Combined.
  3. The category "Hydrocarbon/vapour explosion in vessel (hot work)" included NC-20 (Demualgaon), whose report does not mention hot work. The project's mapped name no longer claims hot work. SANKET's own standardised label is still shown unchanged as the reported cause.
  4. SANKET's 20 data-quality flags were not visible in the app. They now appear on each record card under "Data-quality flag".
- **Mechanism unknown:** 16 records.
  - 10 are gas or coal-dust explosions whose type was not recorded.
  - 6 are recorded only as "explosion".
  - The app shows them as their own "cause not established" group.
- **Cause evidence:**
  - 31 records carry an official DGMS enquiry finding.
  - 3 carry a narrative cause only: EXP-02, NC-07 and NC-20, which have no printed findings.
  - 53 carry a cause label only.
- **Flagged for review (from SANKET's own flags):**
  - Source conflicts:
    - EXP-04: underground in the narrative, opencast in Statement 4.3.
    - NC-19: metal mine in the narrative, stone in the statement.
    - C-HIST-277: "Other explosive accident" in Ch. 10, ignition of gas/dust per the Court of Inquiry.
  - Coding quirks: EXP-03 (code and narrative wording differ), EXP-07 (recorded under 0779), NC-22 (recorded under 0999 Unclassified).
  - Mineral inferred from the mine name: 10 list rows. These include N-HIST-055 and N-HIST-062, two of the three "Metal ore" records, so the metal-ore count rests partly on inference.
- **Missing data:** place of work and state are not reported for the 53 list rows. The app does not guess them; filters show these records separately as "place not recorded".
- **Synthetic scenarios:** kept separate throughout. They are never in the historical list, never in the chart (the chart total stays at 87) and never counted as evidence.

### Synthetic workbook (200 scenarios)

- The `Explosion_Scenarios` sheet has exactly 200 rows, with unique IDs.
- No blank cells, no duplicate texts, and no near-duplicate pairs (word-overlap above 0.6).
- Every row is marked "Synthetic scenario — not a historical accident" and "Historical_DGMS_Record = No".
- Category counts match the Category_Summary sheet (35/35/30/35/25/20/20).
- No coal-only category appears in a metal context.
- **Label issues** (not corrected, because changing source labels would be fabrication):
  - The "Metal Mine" class contains at least five plain blasting or explosives events, so it mixes a mine type with a mechanism.
  - EXP-094 is labelled Combined but mentions no methane.
  - The workbook's own data dictionary says the labels need expert validation.
- Synthetic IDs (EXP-001 to EXP-200) resemble SANKET narrative IDs (EXP-01 to EXP-14). They are always shown in dashed, purple-tagged cards labelled "Synthetic — training scenario", but the similar IDs remain a possible source of confusion.

## B. Preventive-measure verification

- **Books:** both were inspected.
  - Ramlu pages used: spontaneous heating, static and hot-work precautions (pp. 18–24), the sealing of fires (pp. 50–51), firedamp explosions and their prevention (pp. 97–115), coal-dust explosions (pp. 131–139), and sulphide ore dust (pp. 165–166).
  - Cheng pages used: case histories (pp. 4–10), seals (p. 17, §2.1.3), explosion records (pp. 33–34), rock dust, barriers and suppression (pp. 35–47), and inerting (p. 163, §5.2.2).
- **23 measures, 40 book references:**
  - 35 were confirmed automatically: the section heading or key terms appear on the cited printed page.
  - The other 5 were read by hand: G08, G11 and G12 (Ramlu pp. 103, 105) and G18 and G19 (Cheng pp. 17, 163). All 5 were confirmed.
  - **All 40 are confirmed.** None was found to be wrong.
- **DGMS links:** all 7 links from measures to DGMS findings point to a finding actually printed for that accident.
- **Wording:** each measure is a summary written for the app and is labelled as such. No measure is presented as a quotation or as an inspector's finding. "States" and "case" are kept apart: "case" means the measure is derived from an accident the book describes.
- **Gaps** (stated in the app, not filled with general knowledge): neither book covers misfires, lightning, flyrock, blasting shelters or the transport of explosives. Measures for these come only from DGMS findings and are marked "Neither book covers this".
- **Defect fixed:** a DGMS finding about the *shot-firing* cable was summarised as electrical-supply advice ("Treat all wires as live…").
  - Cause: the finding mentions an insulated cable and testing the circuit for resistance or continuity, and the generic electrical theme matched those words.
  - Scope: four accidents, eight findings across both datasets.
  - Fix: a specific blasting-circuit theme now summarises them correctly, and no other finding is affected.
- **Book disagreements** are recorded and shown (G13 incombustible-dust percentages; G16 water-barrier effectiveness).

## C. Model and analytics

- **DGMS hazard classifier** (8 groups, TF-IDF + logistic regression):
  - Rebuilt from `accidents.csv` and reproduced byte-identical.
  - Test accuracy 0.705 and macro-F1 0.619 on 139 held-out 2021–22 accidents, against a 0.23 majority baseline.
- **Explosion-category classifier:**
  - Trained on 200 synthetic scenarios plus 29 SANKET narratives.
  - Synthetic-only 5-fold CV: accuracy 0.685, macro-F1 0.662.
  - A model trained on synthetic data only labels the 29 real narratives 86.2% correctly. This is out-of-domain and covers essentially one class (blasting), so it is not a reliable multi-class evaluation.
  - The audit fixes left the trained model unchanged (identical coefficients).
- **Explosion-evidence gate** (on the 610 DGMS narratives): precision 0.79, recall 0.87.
- **Confidence labels:** both panels say the percentage is how closely the description matches a class, not the probability of an accident or explosion.
- **Defect fixed (metal mines):** "Explosives detonated prematurely while charging holes in an underground metal ore mine" was classified "Metal Mine: Gas, Dust and Other" (52%) instead of Blasting (20%).
  - Cause: the synthetic Metal Mine class contains blasting events, so the classifier learned that "metal" means that class.
  - Fix: a page-level rule now shows such descriptions as Blasting. It applies only when the description names explosives or blasting and no gas, dust, sulphide or hydrogen mechanism. This follows SANKET's convention for non-coal mines.
  - Transparency: the panel says when the rule was applied and still shows the classifier's own probabilities.
  - Sulphide-dust, H₂S and diesel/ore-dust descriptions stay in the metal-mine class.
- **Non-explosion inputs are not forced into an explosion category.** An electrical shock, conveyor spillage, a diesel loader fire and an underground belt fire with no gas or explosion words all produced no explosion analysis (tests 7–9b).
- **Bar chart:**
  - Totals reconcile with the filtered records in all 864 filter combinations: the bar sum, record count and fatality total equal counts made directly from the records, with no record counted twice.
  - Each accident is counted in exactly one category, so accident counts equal cause associations.
  - The footnote now also says the data is SANKET's compilation, not every explosion accident in Indian mines.
- **Pagination:** a 42-record result was walked page by page: 7 pages, 42 unique records, a final partial page with an end message, and Previous working. A new search restarts at page 1.

## D. Software quality

### Tests (22 passed, 0 failed, all executed)

| # | Test case | Expected | Actual (from the run) | Result |
|---|---|---|---|---|
| 1 | Methane accumulating, underground coal (mt Coal) | Explosion mode, Methane / Firedamp, marked potential hazard, coal SANKET records, ventilation/methane measures | Methane / Firedamp Explosion; potential tag=true; Showing 1–6 of 33 historical explosion records (from 55 SANKET explosion records in these filters); top C-HIST-171,C-HIST-159,EXP-01; M1 "Dilute firedamp with adequate ventilati… | Pass |
| 2 | Documented firedamp explosion | Methane / Firedamp, not tagged potential (event described), firedamp records first | Ambiguous: Methane / Firedamp Explosion or Combined Methane and Coal-Dust Explosion; potential=false; top C-HIST-171(Methane),C-HIST-159(Methane),C-HIST-074(Methane),C-HIST-067(Methane) | Pass |
| 3 | Coal dust propagating an explosion | Coal-Dust category, stone-dust / barrier measures | Coal-Dust Explosion; Showing 1–6 of 33 historical explosion records (from 87 SANKET explosion records (coal and non-coal)); M: Stone-dust (rock-dust) all roadways so t,Before shotfiring in coal, neutralise or | Pass |
| 4 | Combined methane + coal dust | Combined (or ambiguous with methane/coal-dust); honest note that no historical record has exactly this category; related gas/dust records only | Combined Methane and Coal-Dust Explosion; Showing 1–6 of 34 historical explosion records (from 87 SANKET explosion records (coal and non-coal)); note: true; cats Coal-Dust,Gas | Pass |
| 5 | Drilling near a misfired hole | Blasting category; misfire records (EXP-10/11, NC-11 etc.) among top results | Blasting and Explosives-Related Explosion; top NC-11,NC-10,EXP-10,NC-04,NC-03 | Pass |
| 6 | Explosives incident, metal-ore filter | Blasting; only Metal ore records listed; synthetic kept separate | Blasting and Explosives-Related Explosion; Showing 1–3 of 3 historical explosion records (from 3 SANKET explosion records in these filters); ids N-HIST-062,N-HIST-055,NC-15; types Metal ore | Pass |
| 7 | Electrical fault, no explosive atmosphere | No explosion analysis; general hazard = Electricity | hazard Electricity; explosion panel false | Pass |
| 8 | Conveyor spillage | No explosion analysis; machinery/transport hazard | hazard Transportation machinery; explosion panel false | Pass |
| 9 | Fire, no explosion evidence | No explosion analysis (fire is not an explosion) | hazard Machinery other than transportation machinery; explosion panel none | Pass |
| 9b | Underground coal belt fire (no gas/explosion words) | No explosion analysis, or only a labelled potential hazard | hazard Gas, dust & other combustible material; explosion none; potential=false | Pass |
| 10 | Accident with undetermined cause | Kept as its own "cause not established" bar; cards say cause label only, no mechanism invented | Gas or coal dust, type not recorded=10,Explosion, type not recorded=6; Showing 1–6 of 6 records; all cards tagged cause-label-only=true | Pass |
| 11 | Record with unattributable injury count (NC-12) | Injured kept unknown (null), not shown as 0 | injured=null; badge "1 killed"; detail note=true | Pass |
| 12 | No suitable historical record (Below Ground + Oil & gas) | Clear empty state, no unrelated accidents inserted, synthetic separate | hist 0; empty-state=true; general acc 0 | Pass |
| 13 | Search with >6 matches; walk all pages | 6 per page, final partial page, no duplicates, Previous works | {"n":42,"pages":7,"seen":42,"uniq":42,"last":"Showing 37–42 of 42 historical explosion records (from 87 SANKET explosion records (coal and non-coal))","endMsg":"You have reached the end of the matching records.","back":"Showing… | Pass |
| 13b | New search after paging | Pager restarts at 1–6 | Showing 1–6 of 39 historical explosion records (from 87 SANKET explosion records (coal and non-coal)) | Pass |
| 14 | Same text, Coal then Metal ore | Records follow the mine-type filter | coal 6 (Coal) / metal 3 (Metal ore) | Pass |
| 15 | Phone screens: Situation input and navigation (320, 390, 768 px) | Full placeholder visible; tabs inside the screen; no sideways scrolling in either view or in results | 320 px: placeholder fits (textarea 234 px), tabs 36 px tall inside screen, page width 320; 390 px: fits (188 px), width 390; 768 px: fits, width 768. Overflow sweep over 9 searches × 5 widths plus both chart views with all details open: none | Pass (after fixes) |
| 16 | Synthetic scenarios | Never in historical list or chart; always labelled | {"synInHist":false,"synCards":true,"chartTotal":"87","synIdsInHrec":0} | Pass |
| 17 | Accident in both narrative and major-accident list | Counted once; card notes the duplicate | {"c283":false,"n104":false,"exp09":"C-HIST-283","nc17":"N-HIST-104","uniq":true} | Pass |
| E1 | Unrecognised words | Clear message, no results | These words are not in the DGMS records. The model could not recognise “xyzzy qw | Pass |
| E2 | Empty input, no filters | "Nothing to analyse yet" message | Nothing to analyse yet. Type the job you are going to do (fo | Pass |
| E3 | Examples hard-coded? | Examples only fill the form; results computed by run() | no text===branch: true | Pass |

Earlier regression scripts were also rerun and still pass:
- 10 explosion validation cases
- general-mode search regression
- 864-combination chart reconciliation
- tab navigation and keyboard tests
- placeholder visibility

### Other defects fixed

- At 320 px the results page scrolled sideways by 32 px. Cause: the results column and blocks had no shrinkable track, and a long unbroken filename in the synthetic-scenario note set the minimum width. Fixed with `minmax(0,1fr)` tracks and word-breaking.
- The placeholder was cut off at 320 px. The textarea is now 236 px tall below 360 px wide.
- Text that still read as a general-hazard tool was changed:
  - the header tagline;
  - the "nothing to analyse" and "words not recognised" examples, which listed truck, roof, wire and water;
  - the README introduction.
- Out-of-date figures in the README and the evaluation report were corrected, for example "27 blasting, 1 methane" and "28 narratives". The report's "no historical coal-dust records" is now correctly limited to the 2016–2022 narratives.

### Files changed in this audit

- `build_explosion.py`: the two mapping changes, unknown injured counts kept as unknown, data-quality flags carried through, and corrected report text.
- `template.html`, which builds into `index.html`: the metal-mine blasting rule, the blasting-circuit theme, data-quality flags and unknown injuries on cards, wording, and the small-screen layout fixes.
- `model/explosion.json` and `reports/explosion_evaluation.md`: regenerated.
- `README.md` and `reports/final_audit.md`.

### Build and deployment

- `build_explosion.py` and `build_site.py` run cleanly; `build_model.py` reproduces `model.json` exactly.
- Required data files are in the repository. The page uses no absolute local paths and needs no server.
- **Deployment:** pushed to `main` as commit e242011. The GitHub Pages build for that commit, and for the follow-up report commit, completed successfully (confirmed in the repository's Actions log). An earlier web fetch had shown a cached copy of the old page.

### Remaining defects and open items

- The synthetic workbook's labels need the expert validation its own data dictionary asks for, especially the Metal Mine class and EXP-094.
- Historical evidence for several mechanisms is thin: there are no historical Combined, Electrical/Mechanical Ignition or Spontaneous Heating explosions, and one each of Coal-Dust and Metal Mine. Classifier metrics for those classes rest on synthetic data only.
- Mixed periods: before 2016 the data holds only major accidents (4 or more killed), and these are 53 of the 87 records. All-years distributions mix the two kinds of record. The chart says so.
- The three source conflicts listed in A are shown as flags but not resolved; they need the original enquiry reports.
- Live checks of Claude-only features (the "More recommendations" button) were not possible outside claude.ai.

## E. Readiness decision

**Ready with limitations.**

- **Core functions work and are tested:** classification, retrieval, filters, pagination, analytics and navigation (21 of 21 tests, plus 864-combination chart reconciliation).
- **The data is clean and traceable:**
  - Every one of the 87 historical records matches its SANKET PDF page.
  - Duplicates are merged and unknowns stay unknown.
  - Synthetic scenarios are kept apart.
  - All 40 book references are verified.
- **The limits are in the evidence, not the software:**
  - Synthetic labels have not been expert-validated.
  - Historical records are thin for coal-dust and other underground mechanisms.
  - The explosion classifier can only be evaluated on real data for blasting.
  - These limits are stated in the app and should be stated when presenting the project.


## Update, 14 October 2026: combustible-dust classification and retrieval

**Problem reported:** "Combustible processing dust" returned *Hazard unclear 15%*, unrelated DGMS groups (Transportation machinery, Falls) and generic gas-testing measures.

**Causes found** (none involved missing source data or a mapping error in the records):

1. **Evidence gate.** The explosion-evidence lexicon knew "coal dust" and "dust explosion" but not "combustible dust". The phrase matched only the weak word "dust", so explosion analysis never ran and the page fell back to the 8-group DGMS model. That model's training narratives contain no dust-explosion vocabulary (DGMS has no such accidents in 2016–22), so it returned near-uniform probabilities.
2. **Retrieval.** The metal-mine class is a catch-all (gas, dust, blasting and other mechanisms in non-coal mines). It was linked only to blasting and vessel-explosion records, so a dust description would have retrieved blasting accidents. A short major-accident list row (cause label only) could also enter through the "strong shared wording" fallback by sharing the single word "dust".
3. **Measures.** For that catch-all class, the generic firedamp, ventilation and welding measures qualified without matching any word in the description. Ramlu's sulphide-ore-dust measure, which is about blasting precautions, matched any text containing "ore", "metal" or even "lead".
4. **Labels.** The lexicon reported "dust cloud" as "coal dust" evidence.

**What the data contains:**
- The 200 synthetic scenarios include combustible-dust explosions in ore-processing plants, crushers and dust collectors, all labelled Metal Mine.
- No SANKET record (coal or non-coal) is a combustible-dust explosion in a processing plant.
- The nearest historical evidence:
  - C-HIST-191, a coal-dust explosion (cause label only);
  - N-HIST-087, a gas/dust explosion in a stone mine (agent not stated);
  - ten coal "gas or coal-dust" records whose type was not recorded.
- The books cover coal-dust explosions and, in Ramlu, sulphide ore dust *during blasting*. Neither covers combustible dust in ore-processing plants.

**Changes** (no output is hard-coded for any phrase):
- `build_explosion.py`: new strong evidence term "combustible dust" (combustible, explosive, flammable, sulphide, pyrite, sulphur, aluminium or magnesium dust, allowing one word in between). "Dust cloud / deposits" is now its own evidence term instead of being called "coal dust". Gate precision and recall on the 610 DGMS narratives are unchanged (0.794 / 0.871), and no narrative contains the new terms. The classifier is unchanged.
- `template.html`:
  - **Retrieval:** for the metal-mine class, related historical mechanisms now follow the evidence in the description:
    - dust leads to confirmed coal-dust explosions, plus gas-or-dust records only when the dust material is not stated;
    - blasting leads to blasting records;
    - gas leads to vessel and hydrocarbon explosions.
  - **Matching:** a metal-mine record must share wording with the description, and the wording fallback no longer admits label-only list rows.
  - **Coal dust only when supported:** if the classifier picks Coal-Dust or Combined but the description names a non-coal combustible dust and never mentions coal, the result is shown as the non-coal mechanism. The panel states this and keeps the classifier's own probabilities.
  - **Measures:** for the metal-mine class, book measures must match the description's words or the matched accidents. If nothing qualifies, an "Insufficient evidence" notice explains the gap in the books instead of showing general advice.
  - **Vague input:** short or ambiguous descriptions get a request for the material, the location and any ignition source. The "Mechanism in your words" row distinguishes "combustible non-coal dust" from "combustible dust (material not stated)".
  - **Panel order:** in explosion mode the explosion analysis now comes first. When the general DGMS model cannot place the description (below 20%), its ranking is not shown; the explosion panel reports its highest group and percentage instead. All confidence values are the models' own outputs and are labelled as class match, not explosion probability.
- `data/reference_guidance.json`: G22 (Ramlu pp. 165–166, sulphide ore dust) now matches blasting words in a sulphide or base-metal context only. Its book reference is unchanged.

**Regression results** (run in headless Chromium against the built page):

| Input (mine type) | Explosion result | Uncertainty / hazard shown | Historical records | Preventive measures |
|---|---|---|---|---|
| Combustible processing dust (Any) | Ambiguous: Metal Mine: Gas, Dust and Other Explosion Mechanisms or Coal-Dust Explosion (29%, Uncertain) | tagged potential hazard; asks for more detail; general DGMS panel hidden: highest: Transportation machinery, 15% | Showing 1–6 of 11 historical explosion records: C-HIST-001(Gas or), C-HIST-191(Coal-Dust Explosion), C-HIST-275(Gas or), C-HIST-272(Gas or), C-HIST-256(Gas or), C-HIST-247(Gas or) | Insufficient-evidence notice; no general advice shown |
| Combustible processing dust (Metal ore) | Ambiguous: Metal Mine: Gas, Dust and Other Explosion Mechanisms or Coal-Dust Explosion (29%, Uncertain) | tagged potential hazard; asks for more detail; general DGMS panel hidden: highest: Transportation machinery, 15% | empty state: No suitable historical explosion records under the current filters (Any place of work · Me… | Insufficient-evidence notice; no general advice shown |
| Fine combustible dust accumulates inside a metal-ore processing plant's dust collection system near a potential ignition source (Any) | Metal Mine: Gas, Dust and Other Explosion Mechanisms (71%, Strong match) | tagged potential hazard; general DGMS panel hidden: highest: Transportation machinery, 15% | Showing 1–2 of 2 historical explosion records: C-HIST-191(Coal-Dust Explosion), N-HIST-087(Metal Mine:) | Insufficient-evidence notice; no general advice shown |
| Methane accumulates in an underground coal working (Any) | Methane / Firedamp Explosion (77%, Strong match) | tagged potential hazard; general DGMS panel: Gas, dust & other combustible material | Showing 1–6 of 33 historical explosion records: C-HIST-004(Methane /), C-HIST-171(Methane /), C-HIST-159(Methane /), EXP-01(Methane /), C-HIST-074(Methane /), C-HIST-067(Methane /) | Dilute firedamp with adequate ventilation and sample th…; Keep development headings ventilated up to the face: au…; Inspect every ventilated working place each shift for m… |
| An initial methane explosion disperses deposited coal dust (Any) | Combined Methane and Coal-Dust Explosion (49%, Strong match) | general DGMS panel: Gas, dust & other combustible material | Showing 1–6 of 34 historical explosion records: C-HIST-191(Coal-Dust Explosion), C-HIST-171(Methane /), C-HIST-159(Methane /), C-HIST-074(Methane /), C-HIST-067(Methane /), C-HIST-041(Methane /) | Dilute firedamp with adequate ventilation and sample th…; Stone-dust (rock-dust) all roadways so that mine dust a…; Before shotfiring in coal, neutralise or consolidate du… |
| A worker drills near a suspected misfired blast hole (Any) | Blasting and Explosives-Related Explosion (44%, Strong match) | tagged potential hazard; general DGMS panel: Explosives | Showing 1–6 of 42 historical explosion records: NC-11(Blasting and), NC-10(Blasting and), EXP-11(Blasting and), NC-04(Blasting and), NC-09(Blasting and), NC-03(Blasting and) | Work only with a supervisor present: a Foreman, Mining …; Only a trained, authorised blaster should handle, charg…; Before drilling, wash down and examine the rock for mis… |
| A dumper reverses near an opencast mine dump yard (Any) | (no explosion analysis) | general DGMS panel: Transportation machinery | general DGMS mode: Showing 1–6 of 478 matching records (from 610 records in the full dataset) | Keep haul roads wide, with gentle gradients, berms and …; Check brakes and the vehicle's condition before every s…; Use the reversing alarm and horn, and have a spotter wh… |
| Combustible dust cloud ignited in a sulphide concentrator mill (Any) | Ambiguous: Metal Mine: Gas, Dust and Other Explosion Mechanisms or Electrical or Mechanical Ignition of Explosive Atmosphere (13%, Uncertain) | asks for more detail; coal-dust class rejected (non-coal dust named); general DGMS panel hidden: highest: Gas, dust & other combustible material, 18% | Showing 1–1 of 1 historical explosion records: C-HIST-191(Coal-Dust Explosion) | Insufficient-evidence notice; no general advice shown |
| Coal dust has built up on the belt roadway (Any) | Coal-Dust Explosion (45%, Strong match) | tagged potential hazard; general DGMS panel: Transportation machinery | Showing 1–6 of 13 historical explosion records: C-HIST-001(Gas or), C-HIST-191(Coal-Dust Explosion), C-HIST-275(Gas or), C-HIST-272(Gas or), C-HIST-256(Gas or), C-HIST-247(Gas or) | Stone-dust (rock-dust) all roadways so that mine dust a…; Before shotfiring in coal, neutralise or consolidate du…; Confine explosions with correctly sited, designed, inst… |

All earlier suites were rerun and pass:
- the 21-test audit suite;
- the 10-case explosion validation (changes limited to the intended ones above);
- general-mode search regression;
- 864-combination chart reconciliation;
- tab navigation;
- the phone layout at 320, 390 and 768 px.
