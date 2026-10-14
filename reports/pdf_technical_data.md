# Technical data from the *Mine Explosions* PDF

Source: **Mine Explosions (Mine Ventilation and Environmental Hazards), AMIE Study Circle** (5_explosion.pdf, 19 pages, SHA-256 `afb3b7308fa15d4a…`). The PDF is not stored in the repository.

Every value below was read from the rendered page image, not only from extracted text. Page numbers are given two ways: **PDF page** (position in the file) and **printed page** (the footer, n/17). PDF page = printed page + 1. The request quoted printed pages: its “p.7” (Middendorf) is PDF p.8; “pp.11–13” (coal dust) are PDF pp.12–13; “pp.14–16” (barriers) are PDF pp.15–17.

## Where it lives

| File | Content |
|---|---|
| `data/pdf_technical_data.json` | The knowledge base: 40 entries, each with parameter, value and unit as printed, conditions, inputs, mechanism, sector, PDF and printed page, section, applicability, limitations, verification status and the retrieval keys. Text is paraphrased; values and units are as printed. |
| `pdf_calc.js` | The app's calculations and retrieval rules (pure functions, no page code). |
| `template.html` | Section **Relevant Technical Data from the PDF** in the explosion results (`pdfBlock`), live calculators (`pdCompute`). |
| `build_site.py` | Embeds both files and stops the build if an entry lacks a required field, has an unknown group/status/sector, a page outside the PDF, a flagged entry without its flag text, or a bad trigger pattern. |
| `tests/test_pdf_calc.js`, `tests/ui_pdf.js` | Automated tests (below). |

## Three kinds of content, kept apart

1. **PDF content** – the `value`, `unit`, `pdf_page` and `section` fields. Nothing was substituted from another source. Wording that looks wrong is kept as printed and flagged.
2. **App calculations** – `pdf_calc.js`. Each result names the PDF equation or values it uses and says it was calculated by the app from the user's inputs. A calculation runs only when every input is typed in as a number; missing or invalid inputs give “Not calculated” with the list of what is needed. No input is ever taken from a default or inferred from the text.
3. **App notes (not in the PDF)** – limited to: the dimension check of the gas-emission formula; K ≥ 1 (follows from K being a maximum ÷ an average); the 35 cm overlap of the light and heavy shelf definitions; the observation that the shelf spacings read sensibly in metres (0.91 m ≈ 3 ft, 1.22 m ≈ 4 ft) and that the loadings are round imperial figures (29.8 kg/m ≈ 20 lb/ft, 107.4 kg/m² ≈ 22 lb/ft²). These are noted in the limitations, never used to change a value.

## Corrections to the request

- **Middendorf layering index.** The request gave S = 24v²/(cF³). The PDF (p.8, printed 7/17) prints **S = ∛( 24 v² / (c √F) )**, a cube root over 24v² divided by c times the square root of F. The app uses the PDF version. The PDF's correction factor for a rising airway and a changing cross-section is not given, so it is not applied and the result is labelled as valid for a level airway of constant section. The transcription is verified; the empirical index itself has not been checked against Middendorf's original publication.
- The 600–900 °C coal-dust ignition range is on PDF p.12, the barrier values on PDF pp.15–17.

## Items flagged for review (kept as printed)

| ID | Parameter | Issue |
|---|---|---|
| V03 | Workings that must not be ventilated by diffusion alone | Symbol “+” before 3 m is ambiguous (probably “>”). Printed as “+ 3 m in length”; probably means more than 3 m. Kept as printed. |
| B07 | Intermediate barrier dust loading | Not stated whether 195.3 kg/m² is a minimum or an exact value. Printed without “at least” (unlike the light and heavy barriers) and with “roadway cross-section” instead of “average roadway cross-section”. |
| B08 | Heavy barrier dust loading | Shelf composition probably should read “heavy type”; not corrected. The composition wording looks inconsistent: a heavy barrier would be expected to need at least one-third heavy shelves. Kept as printed. |
| B09 | Distance between adjacent shelves | Unit printed as “in”; probably metres. The PDF prints “in”. Inches are implausible for shelves 35–50 cm wide in a 25–40 m barrier; metres (0.91 m ≈ 3 ft, 1.22 m ≈ 4 ft) fit. Not corrected. |
| B11 | When stone-dust barriers fail | Placement wording “or far” is incomplete. “less than 40 to 60 m or far from a face” is ambiguous (probably “or too far”). |

Also noted, not flagged: “0. 1 s” read as 0.1 s (B10); a missing bracket after “0.4 m3 volume” (D05); the flame-velocity heading on printed p.3 has no value; the Polish-shelf statement (B03) is presented as a statement from the PDF, not as current regulation.

## Knowledge base

| ID | Group | Parameter | Value (as printed) | Unit | PDF p. (printed) | Status |
|---|---|---|---|---|---|---|
| M01 | reference | Flammable range of methane in air | ≈5 (33 g/m³) to ≈15 (100 g/m³) | % CH₄ by volume | 2 (1/17) | verified |
| M02 | reference | Stoichiometric methane concentration | 9.5 | % CH₄ by volume | 2 (1/17) | verified |
| M03 | reference | Air needed to burn methane completely | 1 volume CH₄ : 2 volumes O₂, or 10 volumes of air | volume ratio | 2 (1/17) | verified |
| M04 | calculation | Le Chatelier relation: lower flammable limit of a gas mixture | 100 / L = p₁/l₁ + p₂/l₂ + p₃/l₃ + … | % | 3 (2/17) | verified |
| M05 | reference | Effect of oxygen and airborne coal dust on the methane LFL | Independent of O₂ above 20 %; falls linearly from 5 % to zero as airborne coal-dust concentration rises | % CH₄ / % O₂ | 3 (2/17) | verified |
| M06 | reference | Inert-gas damping | CO₂ is more effective than N₂ |  | 3 (2/17) | verified |
| M07 | reference | Ignition temperature of pure methane in oxygen | 550 | °C | 3 (2/17) | verified |
| M08 | reference | Ignition temperature of flammable firedamp-air mixtures | 650 to 750 | °C | 3 (2/17) | verified |
| M09 | reference | Maximum explosion pressure of a methane-air mixture | 7.2 | bar | 3 (2/17) | verified |
| M10 | reference | Flame length of an ignited gas zone | Increases up to ≈12 % CH₄, then decreases; ≈4.5 at 9.5 %, ≈5 at 12 % | × gas-zone length (total flame length) | 3 (2/17 to 3/17) | verified |
| M11 | calculation | Gas-emission index | q = c × 60 × 24 × Q_air / (100 × O × K) = c × 14.4 × Q_air / (O × K) | m³ CH₄/t | 4 (3/17 to 4/17) | verified |
| M12 | reference | Factor K in the gas-emission index | 1 to 2; 1.5 to 2 for mechanised faces | – | 5 (4/17) | verified |
| M13 | reference | Indian classification of coal-mine gassiness | Degree I < 1; Degree II 1–10; Degree III > 10 | m³ CH₄/t output | 5 (4/17) | verified |
| M14 | reference | Coward triangle: oxygen below which no mixture is explosive by itself | ≈12.1 (normal air 20.93 % O₂) | % O₂ | 11 (10/17) | verified |
| V01 | calculation | Middendorf layering index | S = ∛( 24 v² / (c √F) ) | index (no unit given) | 8 (7/17) | verified |
| V02 | design | Mine equivalent orifice | > 2 (as large as possible) | m² | 7 (6/17) | verified |
| V03 | design | Workings that must not be ventilated by diffusion alone | + 3 (as printed) | m length | 7 (6/17) | flagged |
| E01 | design | Flameproof and intrinsically safe apparatus voltage | Flameproof enclosure above 25; intrinsically safe up to 25 | V | 9 (8/17) | verified |
| D01 | reference | Conditions for a dust explosion | A dense dust cloud with a definite mixing ratio with oxygen, and an ignition source of sufficient intensity |  | 12 (11/17 to 12/17) | verified |
| D02 | reference | Ignition temperature of dry airborne coal dust | 600 to 900 | °C | 12 (11/17) | verified |
| D03 | reference | Ignition delay: coal dust vs firedamp | Coal dust ≥ 100 ms even with the strongest source; firedamp 1 to 2 ms | ms | 12 (11/17) | verified |
| D04 | reference | Coal-dust properties that change flammability | Fineness, volatile matter, ash, moisture |  | 12 (11/17) | verified |
| D05 | reference | Firedamp explosion raising deposited dust (secondary explosion) | A gas explosion of ≈0.4 m³ of flammable firedamp mixture can start a much bigger coal-dust explosion | m³ | 13 (12/17) | verified |
| D06 | reference | Coal-dust explosion severity compared with firedamp | Some reach higher maximum pressures; longer duration; faster propagation; CO always in the afterdamp |  | 12 (11/17) | verified |
| D07 | design | Air velocity in mine airways to limit dust pick-up | < 3 (if possible) | m/s | 14 (13/17) | verified |
| D08 | design | Calcium chloride stemming cartridges for shotfiring in coal | 82 to 85 % CaCl₂ with 15 to 18 % water of crystallisation | % by mass (as printed: per cent) | 14 (13/17) | verified |
| D09 | design | Dust neutralisation before shotfiring | Within a radius of 10 to 20 of the working coal face | m | 15 (14/17) | verified |
| B01 | design | Length of roadway occupied by a shelf barrier | 25 to 40 | m | 15 (14/17) | verified |
| B02 | design | Polish-shelf plank size | 10 to 15 wide, 35 to 50 long | cm | 15 (14/17) | verified |
| B03 | design | Approved shelf type in India | Only the Polish Shelf (statement in the PDF) |  | 16 (15/17) | verified |
| B04 | design | Light Polish shelf | Width ≤ 35 cm; dust loading ≤ 29.8 kg/m of shelf length | cm; kg/m | 16 (15/17) | verified |
| B05 | design | Heavy Polish shelf | Width ≥ 35 and ≤ 50 cm; dust loading ≤ 59.6 kg/m of shelf length | cm; kg/m | 16 (15/17) | verified |
| B06 | design | Light barrier dust loading | ≥ 107.4 kg per m² of average roadway cross-section; all shelves light | kg/m² | 16 (15/17) | verified |
| B07 | design | Intermediate barrier dust loading | 195.3 kg per m² of roadway cross-section; not more than one-third of the shelves heavy | kg/m² | 16 (15/17) | flagged |
| B08 | design | Heavy barrier dust loading | ≥ 390.6 kg per m² of average roadway cross-section; “not less than one-third of the shelves of the light type” (as printed) | kg/m² | 16 (15/17) | flagged |
| B09 | design | Distance between adjacent shelves | Light shelves: min 0.91, max 2.10. Heavy–heavy or heavy–light: min 1.22, max 2.59 | “in” as printed (probably m) | 16 (15/17) | flagged |
| B10 | design | Time from dust release to flame arrival | 0.1 to 0.2 | s | 17 (16/17) | verified |
| B11 | design | When stone-dust barriers fail | Barrier in a flammable firedamp mixture or under a roof layer; flame velocity above ≈500 m/s; barrier less than 40 to 60 m “or far” from a face so that dynamic pressure is below the minimum, normally 3 to 5 kN/m²; weak ignition giving too little pressure | m/s; m; kN/m² | 17 (16/17) | flagged |
| B12 | design | Water barriers compared with stone dust | Heat capacity of water ≈5 × that of dust | ratio | 17 (16/17) | verified |
| B13 | design | Steel doors in explosion-proof stoppings | ≈20 thick, single-wing, in a solid stopping | mm | 17 (16/17) | verified |

## Calculations

| Calculator | Formula (PDF) | Inputs | Result and rule |
|---|---|---|---|
| Methane position | compare with ≈5–15 % (M01) and 9.5 % (M02) | measured CH₄ % (0–100) | below / at lower limit / within / at upper limit / above; relation to 9.5 %. Below 5 % is reported as “not by itself safe” because the PDF says the LFL falls with airborne coal dust. Always marked “not a prediction”. |
| Gas-emission index (M11) | q = c × 60 × 24 × Q_air / (100 × O × K) | c % (0–100), Q_air m³/min (>0), O t/d (>0), K (≥1; warning above 2) | q in m³ CH₄/t; Degree I < 1, II 1–10 (1 and 10 included, as the table prints “1 - 10”), III > 10 (M13). |
| Middendorf layering index (V01) | S = ∛( 24 v² / (c √F) ) | v m/s (>0), c % (>0, ≤100), F m² (>0) | S < 2 probable danger of layering; S > 2 no danger (as stated); S = 2 (within 10⁻⁹) “not classified by the stated rule”. |
| Le Chatelier (M04) | 100 / L = Σ pᵢ / lᵢ | share pᵢ % (sum 100 ± 0.01) and lower limit lᵢ % of each gas | L in %. Only methane's limit (≈5 %) is in the PDF; others must be typed in. |

A methane percentage written in the description (for example “2.5% methane”) is placed in the methane-position box with the warning *“Use it only if it is a measured reading”*. It is not used for any other calculation and nothing else is read from the text.

## How values are chosen for a situation

Retrieval runs on the explosion analysis already produced for the description (category, runner-up when undecided, mine type and wording); it is not a fixed list.

- The explosion category gives mechanism keys: methane, coal dust, combined, blasting in coal, electrical ignition, sealed/fire area. An entry is shown when its own mechanism matches (core values) or when the description uses a word tied to it (for example *gassy / degree III* → gassiness classification; *heading* → diffusion rule; *sealed* → Coward oxygen limit and Le Chatelier). The reason is printed under each value.
- **Coal-only values** (gassiness, coal dust, barriers, layering, Coward analysis) are never shown when the mine type or the description is metal / non-coal or a processing plant. For those, the only entry that can appear is the PDF's general dust-cloud condition (D01), which the PDF states for “any industrial dust”, and methane properties only when methane or firedamp is named.
- “Gas” counts as firedamp only when methane/firedamp is named, or gas is mentioned in a coal context without a fuel gas (cylinder, LPG, acetylene, diesel …). The adjective “explosive” does not count as blasting.
- If the mine type is not given and nothing in the text decides, coal values may appear with the note that they are coal-mine values.
- At most five values are shown; the rest are under “more values from the PDF”. An equation that has a calculator is shown as the calculator, not repeated as a list item.

## The 25 validation situations

Section contents for the situations in `reports/validation_25.md` (no filters set, as in that run).

| Test | Explosion category | Values shown | Calculators |
|---|---|---|---|
| TEST-01 | Methane / Firedamp Explosion | M01, M02, M08, M10 | methanePosition, gasEmissionIndex, layeringIndex |
| TEST-02 | Methane / Firedamp Explosion | M01, M02, M08, M10, V03 | methanePosition, gasEmissionIndex, layeringIndex |
| TEST-03 | Coal-Dust Explosion | D01, D02, D03, D04, D07 | – |
| TEST-04 | Combined Methane and Coal-Dust Explosion | M01, M02, M05, M08, D01, D02, D03, D04, D05, D07 | methanePosition, gasEmissionIndex, layeringIndex |
| TEST-05 | Ambiguous: Electrical or Mechanical Ignition of Explosive Atmosphere or Methane / Firedamp Explosion | M01, M02, M08, E01 | methanePosition, gasEmissionIndex, layeringIndex |
| TEST-06 | Blasting and Explosives-Related Explosion | D08, D09 | – |
| TEST-07 | Methane / Firedamp Explosion | M01, M02, M08, D08, D09 | methanePosition, gasEmissionIndex, layeringIndex |
| TEST-08 | Methane / Firedamp Explosion | M01, M02, M08, M10, M13, M12 | methanePosition, gasEmissionIndex, layeringIndex |
| TEST-09 | Methane / Firedamp Explosion | M01, M02, M08, D08, D09 | methanePosition, gasEmissionIndex, layeringIndex |
| TEST-10 | Spontaneous Heating, Fire and Explosion Escalation | M01, M02, M08, M14, M10 | methanePosition, gasEmissionIndex, layeringIndex, leChatelier |
| TEST-11 | Blasting and Explosives-Related Explosion | section not shown | – |
| TEST-12 | Blasting and Explosives-Related Explosion | section not shown | – |
| TEST-13 | Ambiguous: Metal Mine: Gas, Dust and Other Explosion Mechanisms or Electrical or Mechanical Ignition of Explosive Atmosphere | section not shown | – |
| TEST-14 | Metal Mine: Gas, Dust and Other Explosion Mechanisms | D01 | – |
| TEST-15 | Metal Mine: Gas, Dust and Other Explosion Mechanisms | section not shown | – |
| TEST-16 | Ambiguous: Blasting and Explosives-Related Explosion or Metal Mine: Gas, Dust and Other Explosion Mechanisms | section not shown | – |
| TEST-17 | Metal Mine: Gas, Dust and Other Explosion Mechanisms | section not shown | – |
| TEST-18 | Metal Mine: Gas, Dust and Other Explosion Mechanisms | D01 | – |
| TEST-19 | Metal Mine: Gas, Dust and Other Explosion Mechanisms | section not shown | – |
| TEST-20 | Ambiguous: Metal Mine: Gas, Dust and Other Explosion Mechanisms or Electrical or Mechanical Ignition of Explosive Atmosphere | E01 | – |
| TEST-21 | (no explosion analysis) | section not shown | – |
| TEST-22 | (no explosion analysis) | section not shown | – |
| TEST-23 | (no explosion analysis) | section not shown | – |
| TEST-24 | (no explosion analysis) | section not shown | – |
| TEST-25 | (no explosion analysis) | section not shown | – |

Metal-mine, quarry and non-explosion situations show no coal values; the two metal-processing dust cases show only D01. TEST-20 (fuel-gas leak) shows only the flameproof/intrinsic-safety voltage, not methane values.

## Tests

- `node tests/test_pdf_calc.js` – 69 checks: every source value, unit and page (and PDF page = printed + 1); flagged items kept as printed; the Middendorf equation text; methane below / at / within / above the range and at 9.5 %; gas-emission index against both printed forms, its dimensions, Degree I / II / III and the boundaries 1 and 10; layering index below 2, above 2 and exactly 2; Le Chatelier; missing, non-numeric, negative, out-of-range and unit-suffixed inputs; retrieval for coal methane, coal dust, combined, barriers, blasting in a gassy seam, sealed fire area, electrical ignition, metal-ore processing dust, metal mine with methane, quarry misfire, fuel-gas leak, unknown mine type; a reference present while site data are absent (calculators start empty and return “Not calculated”).
- `NODE_PATH=$(npm root -g) node tests/ui_pdf.js` – runs the page in Chromium: section title, page citations and type labels on every item, expected and excluded values per situation, no calculation without inputs, the stated-reading warning, live results (Degree II at q = 7.2, invalid K, S = 2 unclassified, S < 2, invalid methane, 9.5 %), no horizontal overflow at 320 px, no page errors.
