"""Retrieval experiments on the DEV split. No model calls. retrieve.py is not
changed: every variant is built here from the keyword and dense rankings.

The variant list below was fixed BEFORE any of them was run (11 Nov 2026), and
every variant is reported, winners and losers alike. With 24 answerable dev
questions, a variant that gains one or two questions is inside the noise, and
ten tries make a lucky winner likely. Whatever looks best here is a hypothesis
to confirm once on held-out, not a result.

Variants:
  baseline      RRF k=60, keyword and dense weighted 1:1 (must reproduce retrieve.hybrid exactly)
  keyword       FTS5 BM25 alone
  dense         MiniLM alone
  keyword_stem  BM25 with SQLite's built-in porter stemming
  hybrid_stem   baseline with the stemmed keyword ranking
  rrf_k10       RRF k=10: rank 1 counts for much more than rank 5
  dense_x2      weighted RRF, dense counted twice
  keyword_x2    weighted RRF, keyword counted twice
  interleave    round-robin: keyword 1, dense 1, keyword 2, ... (no averaging)
  scope         baseline, with population-specific sections removed unless the
                question names that population (SCOPES below)
  scope_stem    scope and stemming together
Not tried: a cross-encoder reranker (a new model download and more RAM than
this machine has free).

Run:  python experiment_retrieval.py [--out eval/reports/<date>-retrieval-experiments-dev.md]
      python experiment_retrieval.py --self-check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from evaluate import DEPTH, MRR_K, QUESTIONS, RECALL_K, TYPES, corpus_sha, hit, load_dev, provisions, rr, summarise

HERE = Path(__file__).parent

# Sections that restate the general complaint rules for one population, and the
# words in a question that put that population in scope. From the 8 Nov failure
# review: gold matches the population the question names.
SCOPES = {"DISP 1.1A.": ("mifid", "investment firm"), "DISP 1.11.": ("lloyd", "society")}


def fuse(rankings: list[list[str]], weights: list[float], k: int = 60) -> list[str]:
    """Weighted reciprocal rank fusion. With weights 1,1 and k=60 this is retrieve.hybrid."""
    fused: dict[str, float] = {}
    for ranking, w in zip(rankings, weights):
        for rank, pid in enumerate(ranking, 1):
            fused[pid] = fused.get(pid, 0.0) + w / (k + rank)
    return sorted(fused, key=lambda p: -fused[p])


def interleave(a: list[str], b: list[str]) -> list[str]:
    out: list[str] = []
    for i in range(max(len(a), len(b))):
        for r in (a, b):
            if i < len(r) and r[i] not in out:
                out.append(r[i])
    return out


def in_scope(passage_id: str, question: str) -> bool:
    q = question.lower()
    return not any(passage_id.startswith(prefix) and not any(w in q for w in words)
                   for prefix, words in SCOPES.items())


def scoped(ranking: list[str], question: str) -> list[str]:
    return [p for p in ranking if in_scope(p, question)]


def variants(q: str, kw: list[str], kw_stem: list[str], de: list[str]) -> dict[str, list[str]]:
    return {
        "baseline": fuse([kw, de], [1, 1]),
        "keyword": kw,
        "dense": de,
        "keyword_stem": kw_stem,
        "hybrid_stem": fuse([kw_stem, de], [1, 1]),
        "rrf_k10": fuse([kw, de], [1, 1], k=10),
        "dense_x2": fuse([kw, de], [1, 2]),
        "keyword_x2": fuse([kw, de], [2, 1]),
        "interleave": interleave(kw, de),
        "scope": fuse([scoped(kw, q), scoped(de, q)], [1, 1]),
        "scope_stem": fuse([scoped(kw_stem, q), scoped(de, q)], [1, 1]),
    }


def sign_test(wins: int, losses: int) -> float:
    """Exact two-sided sign test; ties are dropped."""
    n = wins + losses
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(wins, losses) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def stem_index(conn: sqlite3.Connection) -> sqlite3.Connection:
    """The same passages in an in-memory FTS5 table with porter stemming. The real database is not touched."""
    mem = sqlite3.connect(":memory:")
    mem.execute("CREATE VIRTUAL TABLE passages_fts USING fts5(id UNINDEXED, text, tokenize='porter')")
    mem.executemany("INSERT INTO passages_fts(id, text) VALUES (?,?)", conn.execute("SELECT id, text FROM passages"))
    return mem


def run(out: Path) -> None:
    import retrieve as rt

    rows = load_dev()
    conn, emb = rt.connect(), rt.Embedder()
    mem = stem_index(conn)
    ranked: dict[str, dict[str, list[str]]] = {}
    for r in rows:
        q = r["question"]
        v = variants(q, rt.keyword(conn, q, DEPTH), rt.keyword(mem, q, DEPTH), rt.dense(conn, q, DEPTH, emb))
        # The harness must reproduce the shipped retriever before any variant means anything.
        assert v["baseline"][:DEPTH] == rt.hybrid(conn, q, DEPTH, emb), f"baseline differs from retrieve.hybrid on {r['id']}"
        for name, ranking in v.items():
            ranked.setdefault(name, {})[r["id"]] = provisions(ranking)

    def is_hit(name, r):
        return hit(r["gold"], ranked[name][r["id"]], r["gold_mode"], RECALL_K)

    def recip(name, r):
        return rr(r["gold"], ranked[name][r["id"]], r["gold_mode"], MRR_K)

    stats = {n: {"all": summarise(rows, ranked[n]),
                 **{t: summarise([r for r in rows if r["type"] == t], ranked[n]) for t in TYPES}} for n in ranked}
    base = stats["baseline"]["all"]
    assert base["hits"] == 17 and base["n"] == 24 and abs(base["mrr"] - 0.532) < 5e-4, base  # committed 8 Nov baseline

    meta = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "corpus_sha256": corpus_sha(conn),
            "questions_sha256": hashlib.sha256(QUESTIONS.read_bytes()).hexdigest(),
            "split": "dev (answerable only)", "n": len(rows), "variants_fixed_before_running": sorted(ranked),
            "scopes": {k: list(v) for k, v in SCOPES.items()}, "recall_k": RECALL_K, "mrr_k": MRR_K}
    L = ["# Retrieval experiments, dev split", "", "```json", json.dumps(meta, indent=2), "```", "",
         "The variant list was fixed before any variant was run and all of them are shown. Wins and losses "
         "are questions whose recall@5 outcome differs from the baseline; p is an exact two-sided sign test "
         "on those, uncorrected for the ten comparisons. Rank better/worse compares reciprocal rank at 10. "
         "With 24 questions nothing here is a finding until it holds on held-out.", "",
         "| Variant | recall@5 [95% Wilson] | MRR@10 | wins | losses | p | rank better | rank worse | exact | paraphrase | multi |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for n in ranked:
        s = stats[n]["all"]
        wins = [r["id"] for r in rows if is_hit(n, r) and not is_hit("baseline", r)]
        losses = [r["id"] for r in rows if not is_hit(n, r) and is_hit("baseline", r)]
        better = sum(recip(n, r) > recip("baseline", r) for r in rows)
        worse = sum(recip(n, r) < recip("baseline", r) for r in rows)
        L.append(f"| {n} | {s['recall']:.3f} ({s['hits']}/{s['n']}) [{s['ci'][0]:.2f}-{s['ci'][1]:.2f}] | {s['mrr']:.3f} | "
                 f"{len(wins)} {' '.join(wins)} | {len(losses)} {' '.join(losses)} | {sign_test(len(wins), len(losses)):.2f} | "
                 f"{better} | {worse} | " + " | ".join(f"{stats[n][t]['hits']}/{stats[n][t]['n']}" for t in TYPES) + " |")
    L += ["", "## Rank of the gold, per question", "",
          "Provision rank of the gold (last gold for multi questions needing all); `-` means outside the top 50 passages. "
          "Questions the baseline misses at 5 are marked with *.", "",
          "| id | type | " + " | ".join(ranked) + " |", "|---|---|" + "---|" * len(ranked)]
    for r in rows:
        cells = []
        for n in ranked:
            ranks = [ranked[n][r["id"]].index(g) + 1 if g in ranked[n][r["id"]] else None for g in r["gold"]]
            if r["gold_mode"] == "all":
                cells.append("-" if None in ranks else str(max(ranks)))
            else:
                got = [x for x in ranks if x]
                cells.append(str(min(got)) if got else "-")
        L.append(f"| {r['id']}{'' if is_hit('baseline', r) else '*'} | {r['type']} | " + " | ".join(cells) + " |")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    for n in ranked:
        s = stats[n]["all"]
        print(f"{n:13} recall@5 {s['hits']:2}/{s['n']}  MRR@10 {s['mrr']:.3f}")


def _self_check() -> None:
    a, b = ["x", "y", "z"], ["z", "w", "x"]
    # Equal weights: x = 1/61 + 1/63 and z = 1/63 + 1/61 tie, so first-seen order holds; y and w follow.
    assert fuse([a, b], [1, 1]) == ["x", "z", "y", "w"], fuse([a, b], [1, 1])
    # Doubling the second ranking must put its top item first; doubling the first must not.
    assert fuse([a, b], [1, 2])[0] == "z" and fuse([a, b], [2, 1])[0] == "x"
    # k decides rank-1 against consistency. p is ranked 1 and 4, q is ranked 2 and 2:
    # at k=1 the single top rank wins (0.70 against 0.67), at k=1000 the better mean rank wins.
    r1, r2 = ["p", "q", "m", "n"], ["n", "q", "m", "p"]
    assert fuse([r1, r2], [1, 1], k=1)[0] == "p" and fuse([r1, r2], [1, 1], k=1000)[0] == "q"
    assert interleave(a, b) == ["x", "z", "y", "w"] and interleave(["x"], ["x", "y"]) == ["x", "y"]

    # Scope: a population section is dropped unless the question names the population.
    ids = ["DISP 1.1A.36", "DISP 1.8.1", "DISP 1.11.3#2", "DISP 1.1.10", "DISP 1.10A.1"]
    assert scoped(ids, "Can a firm refuse an old complaint?") == ["DISP 1.8.1", "DISP 1.1.10", "DISP 1.10A.1"]
    assert scoped(ids, "What must a MiFID investment firm do?") == ["DISP 1.1A.36", "DISP 1.8.1", "DISP 1.1.10", "DISP 1.10A.1"]
    assert "DISP 1.11.3#2" in scoped(ids, "What must the Society of Lloyd's do?")
    # Neighbouring sections with similar numbers are never caught by the prefixes.
    assert in_scope("DISP 1.1.10", "q") and in_scope("DISP 1.10A.1", "q") and in_scope("DISP 1.10.1", "q")

    assert sign_test(0, 0) == 1.0 and abs(sign_test(5, 0) - 0.0625) < 1e-9 and sign_test(3, 3) == 1.0
    assert abs(sign_test(1, 6) - 0.125) < 1e-9, sign_test(1, 6)

    # Stemming index: 'forward' finds 'forwarding' only in the stemmed table.
    src = sqlite3.connect(":memory:")
    src.execute("CREATE TABLE passages(id TEXT, text TEXT)")
    src.execute("INSERT INTO passages VALUES ('P 1', 'forwarding with honesty')")
    src.execute("CREATE VIRTUAL TABLE passages_fts USING fts5(id UNINDEXED, text)")
    src.execute("INSERT INTO passages_fts SELECT id, text FROM passages")
    import retrieve as rt
    assert rt.keyword(src, "forward", 5) == [] and rt.keyword(stem_index(src), "forward", 5) == ["P 1"]
    # Porter does NOT merge honest and honesty (honesty stems to honesti), so
    # stemming cannot close the a18 wording gap. Measured 11 Nov, kept as a fact.
    assert rt.keyword(stem_index(src), "honest", 5) == []
    print("self-check passed")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path,
                    default=HERE / "eval" / "reports" / f"{datetime.now():%Y-%m-%d}-retrieval-experiments-dev.md")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    _self_check() if a.self_check else run(a.out)


if __name__ == "__main__":
    sys.exit(main())
