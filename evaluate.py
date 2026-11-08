"""Retrieval evaluation on the DEV split: recall@5 and MRR@10 at provision level
for keyword, dense and hybrid, with Wilson 95% intervals and per-type slices.
No LLM, no API calls. The held-out split is never scored.

Run:  python evaluate.py [--out eval/reports/<date>-retrieval-dev.md]
      python evaluate.py --self-check

Provision level: passages split for length ('DISP 1.1.3#2') count as their
provision, and a ranking is deduplicated to distinct provisions before the cut,
so every retriever shows the same number of provisions at k.
gold_mode any: a hit if at least one gold provision is in the top k; reciprocal
rank uses the first gold. gold_mode all: a hit only if every gold is in the top
k; reciprocal rank uses the rank of the LAST gold, i.e. where the set completes.
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

HERE = Path(__file__).parent
QUESTIONS = HERE / "eval" / "questions.jsonl"
MODES = ("keyword", "dense", "hybrid")
TYPES = ("exact", "paraphrase", "multi")
RECALL_K, MRR_K = 5, 10
DEPTH = 50  # passages fetched per query; dedup to provisions happens after


def load_dev(path: Path = QUESTIONS) -> list[dict]:
    """Answerable dev rows only. Held-out rows are dropped on parse, never kept."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["split"] == "dev" and r["type"] != "unanswerable":
            rows.append(r)
    assert_dev_only(rows)
    return rows


def assert_dev_only(rows: list[dict]) -> None:
    bad = [r["id"] for r in rows if r.get("split") != "dev"]
    assert not bad, f"refusing to score non-dev rows: {bad}"


def provisions(passage_ids: list[str]) -> list[str]:
    out = []
    for pid in passage_ids:
        p = pid.split("#")[0]
        if p not in out:
            out.append(p)
    return out


def hit(gold: list[str], ranked: list[str], mode: str, k: int) -> bool:
    top = set(ranked[:k])
    return all(g in top for g in gold) if mode == "all" else any(g in top for g in gold)


def rr(gold: list[str], ranked: list[str], mode: str, k: int) -> float:
    ranks = [ranked.index(g) + 1 for g in gold if g in ranked[:k]]
    if not ranks or (mode == "all" and len(ranks) < len(set(gold))):
        return 0.0
    return 1.0 / (max(ranks) if mode == "all" else min(ranks))


def wilson(x: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def summarise(rows: list[dict], ranked: dict[str, list[str]]) -> dict:
    hits = sum(hit(r["gold"], ranked[r["id"]], r["gold_mode"], RECALL_K) for r in rows)
    mrr = sum(rr(r["gold"], ranked[r["id"]], r["gold_mode"], MRR_K) for r in rows) / len(rows) if rows else 0.0
    return {"n": len(rows), "hits": hits, "recall": hits / len(rows) if rows else 0.0,
            "ci": wilson(hits, len(rows)), "mrr": mrr}


def corpus_sha(conn: sqlite3.Connection) -> str:
    """Recomputed from the passage rows the same way ingest.py does, then
    checked against the hash ingest recorded, so a stale db cannot pass."""
    shas = sorted(r[0] for r in conn.execute("SELECT sha256 FROM passages"))
    got = hashlib.sha256("".join(shas).encode()).hexdigest()
    meta = json.loads(conn.execute("SELECT json FROM meta").fetchone()[0])
    assert got == meta["corpus_sha256"], (got, meta["corpus_sha256"])
    return got


def run(out: Path) -> None:
    import retrieve as rt

    rows = load_dev()
    assert_dev_only(rows)
    conn = rt.connect()
    emb = rt.Embedder()
    ranked = {m: {} for m in MODES}
    for r in rows:
        for m in MODES:
            ranked[m][r["id"]] = provisions(rt.retrieve(conn, r["question"], DEPTH, m, emb))

    stats = {m: {"all": summarise(rows, ranked[m]),
                 **{t: summarise([r for r in rows if r["type"] == t], ranked[m]) for t in TYPES}}
             for m in MODES}
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "corpus_sha256": corpus_sha(conn),
        "questions_sha256": hashlib.sha256(QUESTIONS.read_bytes()).hexdigest(),
        "split": "dev (answerable only)",
        "retrievers": {"keyword": "FTS5 BM25, OR-query of \\w+ terms",
                       "dense": f"{rt.MODEL_REPO} ONNX, mean-pooled, cosine, max {rt.MAX_TOKENS} tokens",
                       "hybrid": f"RRF k={rt.RRF_K}, each ranking to depth 50"},
        "fetch_depth_passages": DEPTH, "recall_k": RECALL_K, "mrr_k": MRR_K,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(rows, ranked, stats, meta, conn), encoding="utf-8")
    print(f"wrote {out}")
    for m in MODES:
        s = stats[m]["all"]
        print(f"{m:8} recall@5 {s['recall']:.3f} [{s['ci'][0]:.2f}-{s['ci'][1]:.2f}]  MRR@10 {s['mrr']:.3f}")


def _fmt(s: dict) -> str:
    return f"{s['recall']:.3f} ({s['hits']}/{s['n']}) [{s['ci'][0]:.2f}-{s['ci'][1]:.2f}]"


def render(rows, ranked, stats, meta, conn) -> str:
    L = ["# Retrieval evaluation, dev split (untuned baseline)", "",
         "```json", json.dumps(meta, indent=2), "```", "",
         "Recall@5 is the share of questions whose gold (any/all per gold_mode) is in the top 5 "
         "distinct provisions, with a Wilson 95% interval. MRR@10 uses the first gold for `any` "
         "and the last gold for `all`; it has no interval here.", "",
         "## Overall", "", "| Retriever | n | recall@5 [95% Wilson] | MRR@10 |", "|---|---|---|---|"]
    for m in MODES:
        s = stats[m]["all"]
        L.append(f"| {m} | {s['n']} | {_fmt(s)} | {s['mrr']:.3f} |")
    L += ["", "## By question type", "", "| Type | Retriever | n | recall@5 [95% Wilson] | MRR@10 |",
          "|---|---|---|---|---|"]
    for t in TYPES:
        for m in MODES:
            s = stats[m][t]
            L.append(f"| {t} | {m} | {s['n']} | {_fmt(s)} | {s['mrr']:.3f} |")
    L += ["", "## Failures (hybrid misses at k=5)", ""]
    for r in rows:
        h = ranked["hybrid"][r["id"]]
        if hit(r["gold"], h, r["gold_mode"], RECALL_K):
            continue
        gold_ranks = ", ".join(f"{g}: {h.index(g) + 1 if g in h else 'not in top fetch'}" for g in r["gold"])
        others = ", ".join(f"{m} {'hit' if hit(r['gold'], ranked[m][r['id']], r['gold_mode'], RECALL_K) else 'miss'}"
                           for m in ("keyword", "dense"))
        L += [f"### {r['id']} ({r['type']}, gold_mode {r['gold_mode']})", "",
              f"Question: {r['question']}", "",
              f"Gold: {', '.join(r['gold'])}. Hybrid provision rank of each gold: {gold_ranks}. "
              f"At k=5: {others}.", "",
              "Retrieved instead (hybrid top 5):", ""]
        for p in h[:RECALL_K]:
            text = conn.execute("SELECT text FROM passages WHERE provision=? ORDER BY id", (p,)).fetchone()[0]
            L.append(f"- {p}: {' '.join(text.split())[:140]}")
        L += ["", "Why (guess): TODO", ""]
    return "\n".join(L) + "\n"


def _self_check() -> None:
    # Fixture: two any-mode questions and one all-mode question with fake rankings.
    ranks = {"q1": ["A 1", "B 2", "C 3", "D 4", "E 5", "F 6"],   # gold at rank 2
             "q2": ["X 1", "Y 2", "Z 3", "W 4", "V 5", "G 6"],   # gold at rank 6: outside @5, inside @10
             "q3": ["M 1", "N 2", "P 3", "Q 4", "R 5"]}          # both golds at 1 and 4
    rows = [{"id": "q1", "gold": ["B 2"], "gold_mode": "any", "split": "dev"},
            {"id": "q2", "gold": ["G 6"], "gold_mode": "any", "split": "dev"},
            {"id": "q3", "gold": ["M 1", "Q 4"], "gold_mode": "all", "split": "dev"}]
    s = summarise(rows, ranks)
    assert s["hits"] == 2 and abs(s["recall"] - 2 / 3) < 1e-9, s
    assert abs(s["mrr"] - (1 / 2 + 1 / 6 + 1 / 4) / 3) < 1e-9, s

    # Mutation 1: delete the gold provision from q1's ranking; recall must drop.
    cut = {**ranks, "q1": [p for p in ranks["q1"] if p != "B 2"]}
    assert summarise(rows, cut)["hits"] == 1, summarise(rows, cut)
    # Mutation 2: reverse a ranking; MRR must fall (q1 gold goes from rank 2 to 5).
    rev = {**ranks, "q1": ranks["q1"][::-1]}
    assert summarise(rows, rev)["mrr"] < s["mrr"], (summarise(rows, rev), s)
    assert rr(["B 2"], ranks["q1"][::-1], "any", 10) == 1 / 5
    # Mutation 3: all-mode with one of two golds retrieved scores 0 on both metrics,
    # while the same ranking under any-mode scores a hit.
    one = ["M 1", "N 2", "P 3", "S 4", "R 5"]
    assert not hit(["M 1", "Q 4"], one, "all", 5) and rr(["M 1", "Q 4"], one, "all", 10) == 0.0
    assert hit(["M 1", "Q 4"], one, "any", 5) and rr(["M 1", "Q 4"], one, "any", 10) == 1.0
    # All-mode reciprocal rank is set by the last gold, not the first.
    assert rr(["M 1", "Q 4"], ranks["q3"], "all", 10) == 1 / 4

    # Passage parts collapse to their provision, keeping first-seen order, so
    # three parts of one provision cannot fill the top k.
    assert provisions(["A#1", "B", "A#2", "C", "A"]) == ["A", "B", "C"]
    # Wilson: known value 2/3 -> [0.208, 0.939]; n=0 is defined.
    lo, hi = wilson(2, 3)
    assert abs(lo - 0.2077) < 1e-3 and abs(hi - 0.9385) < 1e-3, (lo, hi)
    assert wilson(0, 0) == (0.0, 0.0)
    # Held-out guard: a heldout row must be refused, and the real loader keeps dev only.
    try:
        assert_dev_only([{"id": "h1", "split": "heldout"}])
        raise SystemExit("heldout guard did not fire")
    except AssertionError:
        pass
    dev = load_dev()
    assert dev and all(r["split"] == "dev" and r["type"] != "unanswerable" for r in dev)
    print("self-check passed")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path,
                    default=HERE / "eval" / "reports" / f"{datetime.now():%Y-%m-%d}-retrieval-dev.md")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        _self_check()
    else:
        run(a.out)


if __name__ == "__main__":
    sys.exit(main())
