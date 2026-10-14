# Mine / colliery search

A third view, **Mine search**, lets a user enter a mine, colliery, quarry or metal-mine name and see every explosion-related record, outcome, statistic, preventive measure and book reference available for that mine. Everything is generated from the source files by `build_mines.py` and `tools/build_book_mines.py`; no mine name, record or number is written into the page by hand.

## 1. Sources searched

| Source | Mine-level information | How it is used |
|---|---|---|
| SANKET explosion workbook `Mining_Explosion_Accidents_Predictive_Analysis.xlsx` (Accident_Database, 93 rows) | `mine_name`, state, district, mineral, mine type, duplicate flags, verification notes | 87 explosion records (after removing 2 duplicate listings and 4 borderline rows) are the explosion evidence. Duplicate listings become documented aliases. The 4 borderline rows are shown as "reviewed but not counted", with the workbook's reason. |
| DGMS SANKET narratives `accidents.csv` (622 rows, 2016–2022, all causes) | `mine_name`, state, district, mineral, mine type | Identifies the mine and its location. Rows linked to an explosion record are the same incident and are not counted twice. Other rows are reported only as a count of non-explosion accidents, never as explosion evidence. |
| Synthetic workbook (200 scenarios) | none: 0 scenarios name a mine | Not searchable; never counted. |
| Ramlu, *Mine Disasters and Mine Rescue* (scanned, OCR) and Cheng, *Explosions in Underground Coal Mines* (PDF) | mine and colliery names in the text | `tools/build_book_mines.py` indexes names with printed page, year printed next to the name, and topic words nearby. No book text is published. |

## 2. Mine-name fields and matching method

- **Fields used:**
  - `mine_name` from the workbook and `accidents.csv`;
  - names of documented duplicate listings, as aliases;
  - mine names detected in the books.
- **Normalisation** (identical in Python and in the page):
  - lower case, and "&" becomes "and";
  - "U/G" becomes "ug";
  - letters and digits are split ("No.5" becomes "no 5");
  - punctuation and extra spaces are removed;
  - abbreviations and Roman numerals are expanded (coll → colliery, collieries → colliery, mines → mine, I–X → 1–10).
- **Same mine:** identical normalised name and the same sector (coal or non-coal). Records with different known states would be split (none occur in the current data). A major-accident list row has no location; it is attached by exact name only, and the profile says so. Similar but different names are never merged.
- **Match types**, with exact matches first:
  - **Exact:** the normalised query equals a name or documented alias. A single exact match opens the profile directly.
  - **Partial:** every word of the query begins a word of the name.
  - **Possible spelling match:** each distinctive query word (4+ letters, not a generic word such as mine or stone) is within 1 edit of a name word, or 2 edits for words of 7+ letters.

  Partial and possible matches are listed with sector, location, mineral and record counts for the user to choose from, six per page with Next and Previous.
- **Book names:** a name is detected when a word printed only with a capital letter in that book is followed by Colliery, Mine, Pit or Quarry. Generic words, company names ("… Ltd") and scan errors one letter away from a common word (e.g. "Bassy" for "gassy") are rejected. For dataset mines, the distinctive words of the name must appear on the same book page in a passage about mines or mine accidents.

## 3. Index size

- **552 mines in total:**
  - **83 mines with explosion records**, covering all **87 unique SANKET explosion records** (each assigned to exactly one mine);
  - **41 mines named only in the books**;
  - the rest have only non-explosion DGMS accidents.
- **6 dataset mines are also named in a book:** Chasnalla, Chirimiri, Dhori, and Ramagundam OC-I, OC-II and OC-III.

## 4. Demonstration with real names

These runs were executed in headless Chromium against the built page.

| Case | Search | Result |
|---|---|---|
| Exact match | "Amman Granite Mine" | Opens the profile: NC-11 (2019, blasting, 1 killed, 1 seriously injured), the DGMS findings for NC-11, and general blasting guidance labelled as not about this mine. "Not found in either reference book" is stated. |
| Case, space and abbreviation variants | "  amman   GRANITE mine ", "RAMAGUNDAM OC 1", "ravindra khani no 5", "Kurasia Coll.", "Chhatarpur Mine No.1" | Each opens the right mine. |
| Partial match | "Ramagundam" | 3 candidates (OC-I, OC-II, OC-III), kept separate. |
| Multiple explosion records | "Dishergarh" | 3 firedamp explosions (1910, 1916, 1918), 35 killed, 8 seriously injured. The profile says they come from the major-accident list and are attached by name. "Dishergarh West" is offered separately. |
| One record | "Kurasia Colliery" | EXP-10 (2020, misfire): 1 record, with its findings. |
| Records in more than one source, with a duplicate | "Ramagundam" → OC-I | EXP-09 (narrative), its duplicate listing C-HIST-283 (alias, counted once: "1 duplicate listing merged"), 1 other non-explosion DGMS accident (stated, not counted), and a Ramlu page mentioning Ramagundam collieries (name match only). |
| Duplicate across files | "C. Kasturi Bai Barytes" | NC-17 counted once; the duplicate N-HIST-104 is merged. |
| Incomplete casualty data | "Dahra Pathar Khadan" | NC-12: Seriously injured "Not available in source (1 record without a figure)"; the table marks it "—*" and does not count it as zero. |
| Book only | "Darby" → Darby Mine | No historical record in the datasets; Cheng printed pp. 8, 9, 10, 13, 205, with year 2006 printed beside the name on pp. 9–13. "Darby No.1 Coal Mine" is offered separately. |
| Book and dataset cross-check | "Dhori" | C-HIST-191 (1965 coal-dust explosion, 268 killed). Ramlu names "Dhori Colliery", printed p. 88–89 (approximate); the year printed beside it, 1965, matches the record. |
| In the data, but no explosion record | "Chasnalla", "Bangwar U/G Project" | "No explosion-related record for this mine", with the count of other DGMS accidents by cause group; no unrelated accident is shown as evidence. Chasnalla is also mentioned in Ramlu (1975, printed p. 366–367, approximate). |
| Misspelled | "Kurasiya" | Possible spelling match: Kurasia Colliery. |
| Invalid | "xyzabc" | "No matching mine found in the available project sources", with the sources listed. |
| Pagination | "stone" | 72 matching mines across 12 pages of 6; all 72 seen, no repeats, end message on the last page. |
| Changing mine | "Dishergarh" then "Amlabad" | Summary, charts and table update (3 records / 3 years, then 2 / 2). |

## 5. Reconciliation

For **every one of the 83 mines with explosion records** the profile was opened and these checks were run:

- the record count, mechanism bars, year bars, outcome-table rows and pager items all equal the mine's records;
- killed in the summary and in the table equals the sum over the records;
- "explosion documented" plus "explosion not explicitly recorded" equals the record count.

**0 mismatches.** All 87 records are assigned to exactly one mine.

## 6. Pagination

Records and candidate mines both use the existing six-per-page pager with Next and Previous. Every item is reachable. No mine in the current data has more than 3 explosion records, so the record list never needs a second page; the same pager was tested with 72 candidates and, in the audit suite, with a 42-record explosion search.

## 7. Files changed and tests

**Files:**
- New: `build_mines.py` (mine index → `model/mines.json`).
- New: `tools/build_book_mines.py` (book name index → `data/book_mine_mentions.json`; needs the book files locally).
- `template.html` (built into `index.html`): third tab, search, candidates, profile, charts, measures, book references.
- `build_site.py`: embeds `mines.json`.
- `README.md`.

**Tests:**
- All cases above.
- Full reconciliation over the 83 mines.
- Phone layouts at 320 and 390 px: no sideways scrolling; three tabs fit.
- Earlier suites still pass:
  - audit suite 21/21;
  - Explosion Causes chart 864/864;
  - general search, examples, browse and navigation;
  - the 25-situation validation, with results unchanged.

## 8. Limitations

- **Sparse data per mine:** most mines have one explosion record. The richest are Dishergarh (3), Amlabad (2) and Parbelia (2). Totals describe the available SANKET records only, not a mine's complete history, and are not explosion rates.
- **Major-accident list rows (1901–2010):** these give no location, findings or narrative. They are attached to a mine by exact name, and their injury figures are as listed.
- **Book matches are by name.**
  - Ramagundam is named as a group of collieries, not a specific OC mine.
  - Chasnalla's 1975 mention concerns an inundation; topic tags are words in the surrounding text, not a classification.
  - Ramlu page numbers are read from scanned headers and are marked approximate where a page has no readable header.
  - OCR noise may hide some names in Ramlu.
- **Preventive measures:** mine-specific measures exist only where DGMS printed enquiry findings, which applies to the 2016–2022 narratives. For older mines the page shows general book guidance for the documented mechanism, clearly labelled as not about that mine. Where the mechanism is unrecorded, no measure is offered.
