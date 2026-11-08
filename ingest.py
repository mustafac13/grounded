"""FCA Handbook PDFs to a passage store: one passage per provision, split only
when a provision is longer than the embedder can read.

Source PDFs are downloaded by hand from handbook.fca.org.uk ("View Sourcebook
as PDF" / "View Chapter as PDF") into corpus/raw/. The Handbook terms forbid
crawlers (cl. 35.3), so nothing here fetches. Text (c) FCA, reused under the
Open Government Licence v3.0.

Run:  python ingest.py               # rebuild grounded.db from corpus/raw/*.pdf
      python ingest.py --self-check
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import retrieve as rt

RAW = Path(__file__).parent / "corpus" / "raw"
COLLECTION = "fca-prin-disp1"
# Which provisions each PDF may contribute: a stray "DISP 2.8.2" in the DISP 1
# PDF is not a DISP 1 provision.
SCOPE = {"PRIN": "PRIN ", "DISP": "DISP 1."}
TOKEN_BUDGET = rt.MAX_TOKENS - 6  # headroom under the cap for the part prefix

# Text comes from pypdf's layout mode, which keeps each line's horizontal
# position. A provision starts with its ID at column 0, then its status letter
# (R rule, G guidance, D direction, E evidential), then the text, all on one
# line. Cross-references that wrap onto a new line are indented, so they can
# never match. (Plain extraction prints some IDs after their own text, which
# put the opening of DISP 1.6.2 on the end of DISP 1.6.1B.)
# Provision suffixes run past F and come in three shapes: DISP 1.1.10G,
# DISP 1.3.1AA, DISP 1.1.5-A.
_ID = r"(?:PRIN|DISP) \d+[A-Z]?\.\d+[A-Z]?\.\d+(?:-?[A-Z]{1,2})?"
START = re.compile(rf"^({_ID}) +([RGEDPC])\b *(.*)$")
FURNITURE = re.compile(r"^(PRIN|DISP|\.|CHAPTER|SOURCEBOOK)$|www\.handbook\.fca\.org\.uk")
SECTION = re.compile(r"^Section : ")
OUT_OF_SCOPE = re.compile(r"\b(Annex|Sch|TP)\b")


def _heading_like(line: str) -> bool:
    return len(line) < 80 and line[:1].isupper() and not re.search(r"[.;:,]$", line)


def parse(text: str, prefix: str) -> list[dict]:
    """Layout-mode text to provisions [{provision, status, heading, body}]."""
    out: list[dict] = []
    cur: dict | None = None
    skipping = False
    pending: list[str] = []  # lines between a section break and the next provision
    for raw in text.splitlines():
        line = raw.strip()
        if not line or FURNITURE.search(line):
            continue
        if SECTION.match(line):
            # A section break ends the current provision. Annexes, schedules and
            # transitional provisions are forms and tables, out of scope for
            # v1: drop everything until the next real section.
            skipping = bool(OUT_OF_SCOPE.search(line))
            if cur:
                out.append(cur)
            cur, pending = None, []
            continue
        m = START.match(raw.rstrip())  # unstripped: column 0 is the signal
        if m and not skipping and m[1].startswith(prefix):
            # _heading_like drops a wrapped section-title tail ("understanding"),
            # which starts lower case.
            heading = [l for l in pending[-2:] if _heading_like(l)]
            if cur:
                # Subheadings ("Purpose") print just before the provision they
                # introduce; move them off the end of the previous one.
                while (len(heading) < 2 and len(cur["lines"]) > 1 and _heading_like(cur["lines"][-1])
                       and re.search(r"[.;:)\]]$", cur["lines"][-2])):  # ] closes "[Note: ...]"
                    heading.insert(0, cur["lines"].pop())
                out.append(cur)
            cur = {"provision": m[1], "status": m[2], "heading": " ".join(heading),
                   "lines": [m[3]] if m[3] else []}
            pending = []
            continue
        if cur and not skipping:
            cur["lines"].append(line)
        elif not cur:
            pending.append(line)
    if cur:
        out.append(cur)
    for p in out:
        # Layout mode pads indents and table columns with runs of spaces.
        p["body"] = re.sub(r"[ \t]+", " ", "\n".join(p.pop("lines")))
    return out


def split(p: dict, tok) -> list[dict]:
    """One passage per provision; an over-budget provision is packed greedily
    into parts at word boundaries, keeping its own whitespace. Every part
    carries its provision ID and heading so it makes sense retrieved alone."""
    head = f"{p['heading']}\n" if p["heading"] else ""
    whole = head + p["body"]
    if len(tok.encode(whole).ids) <= TOKEN_BUDGET:
        return [{"id": p["provision"], "provision": p["provision"], "status": p["status"], "text": whole}]
    prefix = f"{p['provision']} (part 99) {head}"
    parts, buf = [], ""
    # ponytail: re-tokenises the growing buffer per word, quadratic in part
    # length; fine at 250-token parts.
    for word in re.findall(r"\S+\s*", p["body"]):
        if buf and len(tok.encode(prefix + buf + word).ids) > TOKEN_BUDGET:
            parts.append(buf.strip())
            buf = ""
        buf += word
    parts.append(buf.strip())
    return [{"id": f"{p['provision']}#{i}", "provision": p["provision"], "status": p["status"],
             "text": f"{p['provision']} (part {i}) {head}{b}"}
            for i, b in enumerate(parts, 1)]


def reference_tokenizer():
    """Uncapped MiniLM tokenizer: the shipped tokenizer.json truncates at 128,
    which would measure every passage as fitting."""
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(rt._hf_file("tokenizer.json"))
    tok.no_truncation()
    tok.no_padding()  # it also pads to 128, so every short passage measured 128
    assert len(tok.encode("word " * 500).ids) > 400, "tokenizer still truncating"
    assert len(tok.encode("word").ids) < 10, "tokenizer still padding"
    return tok


def pdf_text(path: Path) -> str:
    import logging

    from pypdf import PdfReader

    # Layout mode skips rotated text; in these PDFs that is only the chapter
    # cover titles (checked word-by-word against plain mode, 29 Oct 2026).
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    return "\n".join(page.extract_text(extraction_mode="layout") or "" for page in PdfReader(path).pages)


def build(pdfs: list[Path], db_path: Path = rt.DB_PATH) -> dict:
    tok = reference_tokenizer()
    rows, sources = [], []
    for pdf in pdfs:
        text = pdf_text(pdf)
        # Every page carries the sourcebook code alone on a header line.
        book = re.search(r"(?m)^\s*(PRIN|DISP)\s*$", text)
        if not book:
            sys.exit(f"{pdf.name}: not a PRIN or DISP PDF")
        book = book[1]
        date = re.search(r"www\.handbook\.fca\.org\.uk .*?(\w+ \d{4})", text)
        provisions = parse(text, SCOPE[book])
        for p in provisions:
            for part in split(p, tok):
                part.update(collection=COLLECTION, doc_date=date[1] if date else None,
                            sha256=hashlib.sha256(part["text"].encode()).hexdigest())
                rows.append(part)
        sources.append({"file": pdf.name, "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                        "provisions": len(provisions), "doc_date": date[1] if date else None})
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate passage IDs"
    over = [r["id"] for r in rows if len(tok.encode(r["text"]).ids) > rt.MAX_TOKENS]
    assert not over, f"passages over the embedder cap: {over[:5]}"

    if db_path.exists():
        db_path.unlink()  # always rebuild from scratch: no stale rows, no skip logic
    conn = rt.connect(db_path)
    rt.add_passages(conn, rows, rt.Embedder())
    meta = {
        "collection": COLLECTION,
        "corpus_sha256": hashlib.sha256("".join(sorted(r["sha256"] for r in rows)).encode()).hexdigest(),
        "passages": len(rows),
        "provisions": len({r["provision"] for r in rows}),
        "split_provisions": len({r["provision"] for r in rows if "#" in r["id"]}),
        "sources": sources,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    conn.execute("CREATE TABLE meta(json TEXT)")
    conn.execute("INSERT INTO meta VALUES (?)", (json.dumps(meta),))
    conn.commit()
    conn.close()
    return meta


# Layout-mode shape, copied from the real DISP 1 PDF and cut down.
SAMPLE = """                                                                         DISP
Section : DISP 1.6 Complaints time limit rules
                           Final response
DISP 1.6.2            R    The respondent must, by the end of eight weeks after its receipt of the
                           complaint, send the complainant a final response, subject to
                           DISP 1.6.3 R and to the rules on referral.
                           [Note: article 6(1) of the UCITS implementing Directive]
                           Complainant's written acceptance
DISP 1.6.4            R    DISP 1.6.2 R does not apply if the complainant has already accepted, as in
                           DISP 1.6.4 R.
DISP 2.8.2            R    is out of scope for a DISP 1 corpus.
DISP 1 Treating complainants fairly         www.handbook.fca.org.uk          October 2026
                                                                         DISP
DISP 1.6.5            G    The respondent should keep records.
DISP 1.6.5-A          G    Hyphenated IDs exist.
DISP 1.6.5AA          R    Two-letter suffixes exist.
DISP 1.6.5G           R    Suffixes run past F.
Section : DISP 1.7 Root cause analysis
                           This section is about lessons learned.
DISP 1.7.1            R
                                  Firm type                    Applies?
                                  Banks in the UK              yes, in full
Section : DISP 1 Annex 1 Complaints return form
                           This annex consists only of forms.
DISP 1.8.1            R    applies to this form.
"""


def _self_check() -> None:
    ps = parse(SAMPLE, "DISP 1.")
    got = [p["provision"] for p in ps]
    # Only column-0 IDs with a status letter start provisions: not the indented
    # wrapped cross-references (1.6.3 R, 1.6.4 R.), not out-of-scope IDs
    # (2.8.2), not IDs inside an annex (1.8.1).
    assert got == ["DISP 1.6.2", "DISP 1.6.4", "DISP 1.6.5", "DISP 1.6.5-A", "DISP 1.6.5AA",
                   "DISP 1.6.5G", "DISP 1.7.1"], got
    by = {p["provision"]: p for p in ps}
    assert [p["status"] for p in ps] == ["R", "R", "G", "G", "R", "R", "R"]
    # Subheading moves to the provision it introduces, not the one before.
    assert by["DISP 1.6.4"]["heading"] == "Complainant's written acceptance", by["DISP 1.6.4"]
    assert "acceptance" not in by["DISP 1.6.2"]["body"], by["DISP 1.6.2"]["body"]
    assert by["DISP 1.6.2"]["heading"] == "Final response"
    # Wrapped cross-references stay inside the provision that cited them.
    assert "DISP 1.6.3 R and to the rules" in by["DISP 1.6.2"]["body"], by["DISP 1.6.2"]["body"]
    assert "as in\nDISP 1.6.4 R." in by["DISP 1.6.4"]["body"], by["DISP 1.6.4"]["body"]
    # Page furniture is stripped and layout padding collapsed.
    body = by["DISP 1.6.4"]["body"]
    assert "www.handbook" not in body and "DISP" not in body.split("\n") and "  " not in body, body
    # A section break ends a provision: the next section's intro is not its tail.
    assert "lessons" not in by["DISP 1.6.5G"]["body"], by["DISP 1.6.5G"]["body"]
    # The running page header must not pass for a subheading either.
    assert by["DISP 1.6.5"]["heading"] == "", by["DISP 1.6.5"]
    # A table provision keeps the table that follows its ID; the annex is dropped.
    t = by["DISP 1.7.1"]
    assert "Banks in the UK yes, in full" in t["body"] and "forms" not in t["body"], t

    tok = reference_tokenizer()
    long_p = {"provision": "PRIN 2A.2.1", "status": "R", "heading": "Good faith",
              "body": "\n".join(f"({i}) a firm must act in good faith towards retail customers" for i in range(80))}
    parts = split(long_p, tok)
    assert len(parts) > 1 and all(len(tok.encode(p["text"]).ids) <= rt.MAX_TOKENS for p in parts), \
        [len(tok.encode(p["text"]).ids) for p in parts]
    assert [p["id"] for p in parts][:2] == ["PRIN 2A.2.1#1", "PRIN 2A.2.1#2"]
    assert all(p["provision"] == "PRIN 2A.2.1" and "Good faith" in p["text"] for p in parts)
    joined = " ".join(p["text"] for p in parts)
    assert "(0) a firm" in joined and "(79) a firm" in joined, "split lost content"
    # One unbroken wall of text (tables extract this way) must still split.
    wall = split({"provision": "PRIN 1.1.1", "status": "G", "heading": "", "body": "word " * 600}, tok)
    assert len(wall) > 1 and all(len(tok.encode(p["text"]).ids) <= rt.MAX_TOKENS for p in wall)
    short = split({"provision": "PRIN 2.1.1", "status": "R", "heading": "", "body": "A firm must act with integrity."}, tok)
    assert [p["id"] for p in short] == ["PRIN 2.1.1"]
    print("self-check passed")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        pdfs = sorted(RAW.glob("*.pdf"))
        if not pdfs:
            sys.exit(f"no PDFs in {RAW}")
        print(json.dumps(build(pdfs), indent=1))
