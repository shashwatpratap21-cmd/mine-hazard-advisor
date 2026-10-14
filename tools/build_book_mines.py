#!/usr/bin/env python3
"""Index mine / colliery names mentioned in the two reference books.

Reads the books locally (Ramlu: OCR text per scanned page; Cheng: the PDF) and writes
data/book_mine_mentions.json with, for each mention: the name as printed, the book, the PDF page,
the printed page (read from the page header, or interpolated and marked approximate), any year
printed next to the name, and topic tags for words found near it. No book text is written out.

Usage: python tools/build_book_mines.py --ramlu-ocr DIR --cheng-pdf FILE [--out data/book_mine_mentions.json]
"""
import argparse, collections, glob, json, re, subprocess, sys
from pathlib import Path

MINE_WORD = r"(?:Colliery|Collieries|colliery|collieries|Mine|Mines|mine|mines|Pit|Pits|pit|Quarry|quarry|Experimental Mine|coal mine|Coal Mine)"
# Generic words that can precede "mine" but are not names (vocabulary, not a list of mine names)
GENERIC = set("""the this that these those a an any each every some many most such other same old new deep large small major
coal metal metalliferous underground opencast gassy fiery dangerous abandoned sealed working typical experimental model
research national federal us american chinese indian british german international north south east west united states
chapter figure table section preface abstract index keywords contents explosion explosions fire fires rescue disasters
mine mines mining modelling mitigating determining explosibility safety health act room gob areas atmosphere single
entry driving stoppi envi visas high central sions scue and of in at for from to with by on into whole entire
copper gold iron zinc lead uranium salt potash lignite bituminous anthracite base sulphide tin mica manganese
african canadian australian european asian advanced belowlground belowground several various numerous
""".split())
TOPICS = {"explosion": r"explo", "firedamp / methane": r"firedamp|fire-damp|methane|\bgas\b", "coal dust": r"coal[- ]?dust|\bdust\b",
          "fire / spontaneous heating": r"\bfire|spontaneous|heating", "inundation": r"inundat|water|flood", "rescue": r"rescu|trapped",
          "sealing": r"\bseal", "blasting": r"blast|shot ?fir|explosive"}

def ramlu_pages(d):
    for f in sorted(glob.glob(str(Path(d) / "p*.txt"))):
        yield int(re.search(r"p(\d+)", f).group(1)), open(f, errors="ignore").read()

def cheng_pages(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    for i in range(1, n + 1):
        yield i, subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), pdf, "-"], capture_output=True, text=True).stdout

def printed_numbers(book, pages):
    """PDF page -> (printed label, exact?) from page headers; gaps interpolated from neighbours."""
    found = {}
    for p, t in pages.items():
        lines = [l.strip() for l in t.split("\n") if l.strip()]
        if book == "Cheng":
            n = [int(x) for l in lines[:2] for x in re.findall(r"^\d{1,3}$", l)]
            if n: found[p] = (n[0], n[0])
        else:  # Ramlu: scanned two-page spreads, header numbers in short lines at top/bottom
            nums = [int(m.group(1)) for l in lines[:4] + lines[-4:] if len(l.split()) <= 9
                    for m in re.finditer(r"(?:^|\s)(\d{1,3})(?=\s|$)", l) if -30 <= int(m.group(1)) - 2 * p <= -10]
            if nums: lo = min(nums); found[p] = (lo, lo + 1)
    out = {}
    keys = sorted(found)
    for p in pages:
        if p in found:
            a, b = found[p]; out[p] = (f"{a}" if a == b else f"{a}–{b}", True); continue
        prev = max((k for k in keys if k < p), default=None); nxt = min((k for k in keys if k > p), default=None)
        ref = prev if prev is not None and (nxt is None or p - prev <= nxt - p) else nxt
        if ref is None: out[p] = ("not printed", False); continue
        step = 1 if book == "Cheng" else 2
        a = found[ref][0] + (p - ref) * step
        out[p] = (f"{a}" if step == 1 else f"{a}–{a+1}", False)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ramlu-ocr", required=True); ap.add_argument("--cheng-pdf", required=True)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data" / "book_mine_mentions.json"))
    a = ap.parse_args()
    books = {"Ramlu": dict(ramlu_pages(a.ramlu_ocr)), "Cheng": dict(cheng_pages(a.cheng_pdf))}
    if not books["Ramlu"] or not books["Cheng"]:
        sys.exit("ERROR: book text not found")
    mentions = []
    for book, pages in books.items():
        corpus = " ".join(pages.values())
        lower_words = set(re.findall(r"\b[a-z][a-z]+\b", corpus))
        freq = collections.Counter(re.findall(r"\b[a-z][a-z]+\b", corpus))
        common = {w for w, c in freq.items() if c >= 5}
        def ocr_slip(w):  # scanned text: a capitalised word one letter away from a common lowercase word ("Bassy" for "gassy")
            w = w.lower()
            return book == "Ramlu" and any(len(c) == len(w) and sum(x != y for x, y in zip(c, w)) == 1 for c in common if c[1:] == w[1:] or c[:-1] == w[:-1])
        def is_name(w):  # a word printed only with a capital letter in this book, and not generic vocabulary
            return w.lower() not in GENERIC and w.lower() not in lower_words and len(w) >= 4 and not w.isupper() and not ocr_slip(w)
        pn = printed_numbers(book, pages)
        rx = re.compile(r"\b((?:[A-Z][a-z]+(?:[- ](?:[A-Z][a-z]+|No\.? ?\d+))*))(?:,? (?:and|&) [A-Z][a-z]+)*\s+" + MINE_WORD + r"\b")
        for p, t in pages.items():
            flat = re.sub(r"\s+", " ", t)
            for m in rx.finditer(flat):
                words = [w for w in re.split(r"[- ]", m.group(1)) if w and not re.match(r"No\.?|\d", w)]
                while words and not is_name(words[0]): words = words[1:]   # drop leading generic words
                if not words or not all(is_name(w) or w in ("Upper", "Big", "Branch", "River", "Station", "Salt") for w in words): continue
                toks = m.group(1).split()
                toks = toks[toks.index(words[0]):] if words[0] in toks else words
                # a list such as "Orient No. 2 Centralia No. 5 Smith Mine": the mine word belongs to the last name
                segs, cur = [], []
                i = 0
                while i < len(toks):
                    if re.match(r"No\.?$", toks[i]) and i + 1 < len(toks) and toks[i + 1].isdigit():
                        cur += [toks[i], toks[i + 1]]; segs.append(cur); cur = []; i += 2; continue
                    if re.match(r"No\.?\d+$", toks[i]): cur.append(toks[i]); segs.append(cur); cur = []; i += 1; continue
                    cur.append(toks[i]); i += 1
                name = " ".join(cur if cur else (segs[-1] if segs else toks))
                win = flat[max(0, m.start() - 400): m.end() + 400].lower()
                lo = max(0, m.start() - 80); seg = flat[lo: m.end() + 80]
                ys = [(abs((lo + y.start()) - m.end()), y.group(1)) for y in re.finditer(r"\b(1[89]\d\d|20[0-2]\d)\b", seg)]
                yr = min(ys)[1] if ys else ""
                mentions.append({"name": name, "mine_word": m.group(0)[len(m.group(1)):].strip(), "book": book, "pdf_page": p,
                                 "printed_page": pn[p][0], "page_exact": pn[p][1], "year_near": yr,
                                 "topics": [k for k, r in TOPICS.items() if re.search(r, win)]})
        # also record every page on which each proper name occurs (for cross-checking dataset mine names later)
    names = collections.defaultdict(lambda: {"pages": set(), "info": {}})
    for b, pages in books.items():
        corpus = " ".join(pages.values()); lower_words = set(re.findall(r"\b[a-z][a-z]+\b", corpus))
        pn = printed_numbers(b, pages)
        ctx = re.compile(r"collier|\bmines?\b|\bpits?\b|disaster|explosion|inundation|\bminers\b|killed|coalfield", re.I)
        for p, t in pages.items():
            flat = re.sub(r"\s+", " ", t)
            for m in re.finditer(r"\b([A-Z][a-z]{3,})\b", flat):
                w = m.group(1)
                if w.lower() in lower_words or w.lower() in GENERIC:
                    continue
                after = flat[m.end(): m.end() + 40]
                # a name counts only where the text around it is about mines or mine accidents, and not as a company name
                if re.match(r"[\s\w.]{0,25}\b(?:Ltd|Limited|Pvt|Inc|Company|Corporation)\b", after) or not ctx.search(flat[max(0, m.start() - 80): m.end() + 80]):
                    continue
                key = (b, w.lower())
                if p not in names[key]["info"]:
                    lo = max(0, m.start() - 80); seg = flat[lo: m.end() + 80]
                    ys = [(abs((lo + y.start()) - m.end()), y.group(1)) for y in re.finditer(r"\b(1[89]\d\d|20[0-2]\d)\b", seg)]
                    win = flat[max(0, m.start() - 400): m.end() + 400].lower()
                    names[key]["info"][p] = {"year_near": min(ys)[1] if ys else "", "topics": [k for k, r in TOPICS.items() if re.search(r, win)]}
                names[key]["pages"].add((p, pn[p][0], pn[p][1]))
    proper = [{"book": b, "word": w, "pages": sorted([{"pdf_page": p, "printed_page": lab, "page_exact": ex, **v["info"][p]} for p, lab, ex in v["pages"]], key=lambda x: x["pdf_page"])}
              for (b, w), v in sorted(names.items())]
    out = {"_about": "Mine and colliery names found in the two reference books, with page numbers and topic tags only (no book text). "
                     "Names are detected automatically: a word printed only with a capital letter in that book, followed by Colliery/Mine/Pit/Quarry. "
                     "printed_page comes from the page header when page_exact is true, otherwise it is interpolated from neighbouring pages.",
           "books": {"Ramlu": "Ramlu, M.A. Mine Disasters and Mine Rescue, 2nd edition. Universities Press (India), 2007.",
                     "Cheng": "Cheng, J. (2018). Explosions in Underground Coal Mines: Risk Assessment and Control. Springer International Publishing."},
           "mentions": mentions, "proper_words": proper}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=0))
    print(f"{len(mentions)} mine-name mentions; {len(proper)} proper words indexed -> {a.out}")

if __name__ == "__main__":
    main()
