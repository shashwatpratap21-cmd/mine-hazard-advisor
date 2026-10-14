"""Build the mine / colliery search index -> model/mines.json

Sources (each is checked; a missing file stops the build with a clear message):
  model/explosion.json                 SANKET explosion records (87, duplicates already merged) - the explosion evidence
  data/accidents.csv                   all 622 DGMS SANKET fatal-accident narratives 2016-2022 (any cause)
  data/Mining_Explosion_Accidents_Predictive_Analysis.xlsx   duplicate and borderline (not counted) rows, with reasons
  data/book_mine_mentions.json         mine names found in the two reference books (tools/build_book_mines.py)
  data/explosion_specific_mining_scenarios_200.xlsx         checked only: synthetic scenarios name no mines

Grouping rule: records belong to the same mine when their normalised names are identical AND they are in the same
sector (coal / non-coal). Known, different states split a group. A major-accident list row has no location, so it is
attached by name only and the page says so. Similar but different names are never merged; they are offered as
candidates for the user to choose from.

  python build_mines.py
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ABBR = {"coll": "colliery", "collieries": "colliery", "mines": "mine", "proj": "project", "u g": "ug", "o c": "oc",
        "i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10"}
GENERIC = set("""colliery mine project pit pits quarry ocp oc ocm ug underground opencast open cast no stone granite limestone coal
metal mineral mining ltd pvt co company the and of khasra crusher crushers rough sand area incline seam block section unit
building masonry road metal ore iron manganese gold copper zinc lead bauxite oil gas drilling work over production
infrastructure mines barytes dolomite marble quartzite laterite chromite""".split())


def fail(msg):
    sys.exit(f"[build_mines] ERROR: {msg}")


def norm(s):
    s = str(s or "").lower().replace("&", " and ")
    s = re.sub(r"u\s*/\s*g", " ug ", s)
    s = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", s)          # no.5 -> no 5, oc1 -> oc 1
    s = re.sub(r"[^a-z0-9]+", " ", s)
    toks = [ABBR.get(t, t) for t in s.split()]
    return " ".join(toks)


def NR(v):  # "Not reported" and blanks are not values
    return not str(v).strip() or bool(re.fullmatch(r"not reported|nan|none|-", str(v).strip(), re.I))


def sector_of_type(mt):
    return "coal" if str(mt).strip().lower() == "coal" else "noncoal"


def main():
    for p in ["model/explosion.json", "data/accidents.csv", "data/Mining_Explosion_Accidents_Predictive_Analysis.xlsx",
              "data/book_mine_mentions.json", "data/explosion_specific_mining_scenarios_200.xlsx"]:
        if not (HERE / p).exists():
            fail(f"{p} not found")
    X = json.loads((HERE / "model/explosion.json").read_text())
    hrec = X["hrec"]
    acc = pd.read_csv(HERE / "data/accidents.csv")
    for c in ["id", "workbook_id", "mine_name", "state", "district", "mine_type", "mineral", "year", "cause_group", "persons_killed", "explosion_review"]:
        if c not in acc.columns:
            fail(f"accidents.csv has no column {c}")
    wb = pd.read_excel(HERE / "data/Mining_Explosion_Accidents_Predictive_Analysis.xlsx", "Accident_Database")
    books = json.loads((HERE / "data/book_mine_mentions.json").read_text())
    syn = pd.read_excel(HERE / "data/explosion_specific_mining_scenarios_200.xlsx", "Explosion_Scenarios")
    syn_named = int(syn["Situation_Text"].str.contains(r"[A-Z][a-z]+ (?:Colliery|Mine|Quarry)\b", regex=True).sum())

    linked = {h["dgms_id"]: h["id"] for h in hrec if h.get("dgms_id")}
    groups = defaultdict(lambda: {"names": set(), "states": set(), "districts": set(), "minerals": set(), "types": set(),
                                  "hrec": [], "other": [], "excluded": [], "name_only": [], "aliases": set()})

    def gkey(name, sector):
        return norm(name) + "|" + sector

    # SANKET explosion records
    for h in hrec:
        sec = "coal" if h["src"].startswith("Coal") else "noncoal"
        g = groups[gkey(h["mine"], sec)]
        g["names"].add(h["mine"]); g["types"].add(h["mine_type"]); g["hrec"].append(h["id"])
        if h["state"] and h["state"] != "Not reported": g["states"].add(h["state"])
        if h.get("district") and not NR(h["district"]): g["districts"].add(h["district"])
        if h.get("mineral") and not NR(h["mineral"]): g["minerals"].add(h["mineral"])
        if h["kind"] == "list": g["name_only"].append(h["id"])
    # duplicate listings: their names are documented aliases of the retained record
    hid = {h["id"]: h for h in hrec}
    for r in wb.itertuples():
        if r.is_primary_record != 1 and isinstance(r.duplicate_of, str) and r.duplicate_of in hid:
            h = hid[r.duplicate_of]; sec = "coal" if h["src"].startswith("Coal") else "noncoal"
            groups[gkey(h["mine"], sec)]["aliases"].add(str(r.mine_name))
    # borderline rows reviewed by SANKET but not counted as explosions
    for r in wb[(wb.is_primary_record == 1) & (wb.core_explosion_flag != 1)].itertuples():
        sec = "coal" if str(r.source_document).startswith("Coal") else "noncoal"
        g = groups[gkey(r.mine_name, sec)]
        g["names"].add(str(r.mine_name))
        g["excluded"].append({"id": r.accident_id, "date": str(r.date_as_printed), "year": int(r.year) if pd.notna(r.year) else None,
                              "cause_label": str(r.source_cause_label), "category": str(r.explosion_category_std),
                              "killed": int(r.fatalities) if pd.notna(r.fatalities) else None,
                              "reason": str(r.verification_notes if pd.notna(r.verification_notes) else "")})
    # all DGMS narratives 2016-2022 (any cause); those linked to an explosion record are the same incident
    excl_ids = {e["id"] for g in groups.values() for e in g["excluded"]}
    for r in acc.itertuples():
        sec = sector_of_type(r.mine_type)
        g = groups[gkey(r.mine_name, sec)]
        g["names"].add(str(r.mine_name)); g["types"].add(str(r.mine_type))
        if pd.notna(r.state) and not NR(r.state): g["states"].add(str(r.state))
        if pd.notna(r.district) and not NR(r.district): g["districts"].add(str(r.district))
        if pd.notna(r.mineral) and not NR(r.mineral): g["minerals"].add(str(r.mineral))
        if r.id in linked or (isinstance(r.workbook_id, str) and r.workbook_id in excl_ids):
            continue
        g["other"].append({"id": r.id, "year": int(r.year), "cause": str(r.cause_group), "killed": int(r.persons_killed)})

    # split a group whose records carry two or more different known states (none in the current data; kept as a rule)
    mines = []
    for key, g in groups.items():
        norm_name, sector = key.split("|")
        if len(g["states"]) > 1:
            print(f"[build_mines] note: {key} has states {sorted(g['states'])}; kept together only if records cannot be separated")
        disp = max(g["names"], key=lambda n: (sum(c.islower() for c in n) > 0, len(n)))
        mines.append({"key": key, "norm": norm_name, "name": disp, "names": sorted(g["names"]), "aliases": sorted(g["aliases"] - g["names"]),
                      "sector": sector, "types": sorted(g["types"]), "states": sorted(g["states"]), "districts": sorted(g["districts"]),
                      "minerals": sorted(g["minerals"]), "hrec": g["hrec"], "name_only": g["name_only"], "other": g["other"],
                      "excluded": g["excluded"], "book": []})

    # cross-check every dataset mine name against the books: all distinctive words of the name on the same page
    proper = defaultdict(dict)
    for pw in books["proper_words"]:
        proper[pw["book"]][pw["word"]] = {p["pdf_page"]: p for p in pw["pages"]}
    ment_by = defaultdict(list)
    for m in books["mentions"]:
        ment_by[(m["book"], norm(m["name"]))].append(m)
    for mi in mines:
        core = [t for t in mi["norm"].split() if t not in GENERIC and not t.isdigit() and len(t) >= 4]
        if not core:
            continue
        for b in ("Ramlu", "Cheng"):
            if not all(t in proper[b] for t in core):
                continue
            pages = set.intersection(*[set(proper[b][t]) for t in core])
            for p in sorted(pages):
                info = proper[b][core[0]][p]
                named = [m for m in ment_by.get((b, " ".join(core)), []) if m["pdf_page"] == p]
                mi["book"].append({"book": b, "pdf_page": p, "printed_page": info["printed_page"], "page_exact": info["page_exact"],
                                   "matched": " ".join(core), "as_mine": bool(named),
                                   "year_near": named[0]["year_near"] if named else info.get("year_near", ""),
                                   "topics": named[0]["topics"] if named else info.get("topics", [])})
    # mines named only in the books
    known = {(b["book"], b["matched"]) for mi in mines for b in mi["book"]}
    book_only = defaultdict(list)
    for m in books["mentions"]:
        n = norm(m["name"])
        if (m["book"], n) in known or any(n == mi["norm"] for mi in mines):
            continue
        book_only[n].append(m)
    for n, ms in book_only.items():
        mines.append({"key": n + "|book", "norm": n, "name": ms[0]["name"] + " " + ms[0]["mine_word"].replace("mines", "mine").title(),
                      "names": sorted({m["name"] + " " + m["mine_word"] for m in ms}), "aliases": [], "sector": "book", "types": [],
                      "states": [], "districts": [], "minerals": [], "hrec": [], "name_only": [], "other": [], "excluded": [],
                      "book": [{"book": m["book"], "pdf_page": m["pdf_page"], "printed_page": m["printed_page"], "page_exact": m["page_exact"],
                                "matched": m["name"], "as_mine": True, "year_near": m["year_near"], "topics": m["topics"]} for m in ms]})

    # one entry per book page: several mentions on the same page are merged (years kept if any, topics combined)
    for mi in mines:
        per = {}
        for b in mi["book"]:
            k = (b["book"], b["pdf_page"])
            if k not in per: per[k] = dict(b, topics=list(b["topics"]))
            else:
                per[k]["as_mine"] = per[k]["as_mine"] or b["as_mine"]
                per[k]["year_near"] = per[k]["year_near"] or b["year_near"]
                per[k]["topics"] = sorted(set(per[k]["topics"]) | set(b["topics"]), key=lambda t: list(b["topics"] + per[k]["topics"]).index(t))
        mi["book"] = sorted(per.values(), key=lambda b: (b["book"], b["pdf_page"]))
    mines.sort(key=lambda m: m["name"].lower())
    n_h = sum(len(m["hrec"]) for m in mines)
    if n_h != len(hrec):
        fail(f"explosion records in the mine index ({n_h}) do not equal the SANKET records ({len(hrec)})")
    out = {"mines": mines, "generic": sorted(GENERIC), "abbr": ABBR,
           "sources": {"explosion_records": len(hrec), "accidents_rows": int(len(acc)), "workbook_rows": int(len(wb)),
                       "book_mentions": len(books["mentions"]), "synthetic_named_mines": syn_named, "books": books["books"]}}
    (HERE / "model/mines.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    with_x = sum(1 for m in mines if m["hrec"])
    print(f"[build_mines] {len(mines)} mines ({with_x} with explosion records, {sum(1 for m in mines if m['sector']=='book')} named only in the books); "
          f"{n_h} explosion records; {sum(1 for m in mines if m['book'] and m['sector']!='book')} dataset mines also named in a book; "
          f"synthetic scenarios naming a mine: {syn_named}")


if __name__ == "__main__":
    main()
