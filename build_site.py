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


def main():
    t = (HERE / "template.html").read_text(encoding="utf-8")
    body = t.replace("__DATA__", load("model/model.json")).replace("__XDATA__", load("model/explosion.json")).replace("__MDATA__", load("model/mines.json"))
    (HERE / "site_body.html").write_text(body, encoding="utf-8")
    (HERE / "index.html").write_text(HEAD + body + "\n</body></html>\n", encoding="utf-8")
    print(f"index.html {len(body)/1e6:.2f} MB")


if __name__ == "__main__":
    main()
