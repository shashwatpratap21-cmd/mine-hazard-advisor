"""Assemble the single-page site from template.html + model/model.json + model/explosion.json.

  python build_site.py            # writes index.html (GitHub Pages) and site_body.html (Claude artifact body)

Fails with a clear message if a model file is missing; run build_model.py / build_explosion.py first.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,'
        'initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:dark;padding-top:env(safe-area-inset-top,0px);'
        'padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font-size:14px}img{max-width:100%}'
        '[hidden]{display:none!important}</style></head><body>\n')


def load(p):
    p = HERE / p
    if not p.exists():
        sys.exit(f"[build_site] ERROR: {p} not found. Run build_model.py, build_explosion.py and build_mines.py first.")
    return p.read_text(encoding="utf-8").replace("</", "<\\/")


PDF_FIELDS = ["id", "group", "parameter", "value", "unit", "conditions", "inputs", "mechanism", "sector", "pdf_page", "printed_page",
              "section", "applicability", "limitations", "relevance", "status", "base", "triggers"]


def pdf_data():
    """data/pdf_technical_data.json, checked: every entry carries its source page, group, status and the fields the page shows."""
    import json
    import re
    d = json.loads((HERE / "data/pdf_technical_data.json").read_text(encoding="utf-8"))
    ids = set()
    for e in d["entries"]:
        miss = [f for f in PDF_FIELDS if f not in e]
        if miss:
            sys.exit(f"[build_site] ERROR: PDF entry {e.get('id')} lacks {miss}")
        if e["id"] in ids:
            sys.exit(f"[build_site] ERROR: duplicate PDF entry {e['id']}")
        ids.add(e["id"])
        if e["group"] not in d["groups"] or e["status"] not in ("verified", "flagged") or e["sector"] not in ("coal", "gas", "any"):
            sys.exit(f"[build_site] ERROR: PDF entry {e['id']} has an unknown group, status or sector")
        if not 1 <= e["pdf_page"] <= d["source"]["pdf_pages"]:
            sys.exit(f"[build_site] ERROR: PDF entry {e['id']} page {e['pdf_page']} is outside the PDF")
        if e["status"] == "flagged" and not e.get("flag"):
            sys.exit(f"[build_site] ERROR: flagged PDF entry {e['id']} has no flag text")
        if e["triggers"]:
            re.compile(e["triggers"])
    for name, c in d["calculators"].items():
        for u in c["uses"]:
            if u not in ids:
                sys.exit(f"[build_site] ERROR: calculator {name} uses unknown entry {u}")
    return json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def main():
    t = (HERE / "template.html").read_text(encoding="utf-8")
    body = t.replace("__DATA__", load("model/model.json")).replace("__XDATA__", load("model/explosion.json")).replace("__MDATA__", load("model/mines.json"))
    body = body.replace("__PDATA__", pdf_data()).replace("/*__PCALC__*/", load("pdf_calc.js"))
    (HERE / "site_body.html").write_text(body, encoding="utf-8")
    (HERE / "index.html").write_text(HEAD + body + "\n</body></html>\n", encoding="utf-8")
    print(f"index.html {len(body)/1e6:.2f} MB")


if __name__ == "__main__":
    main()
