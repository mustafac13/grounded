"""Three retrievers over one passage store: keyword (FTS5 BM25), dense (MiniLM
ONNX) and hybrid (reciprocal rank fusion). All three take the same k, so a
comparison between them is a comparison of ranking, not of budget.

Run:  python retrieve.py "how long to resolve a complaint" [--mode hybrid] [-k 5]
      python retrieve.py --self-check
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np

DB_PATH = Path(os.environ.get("GROUNDED_DB", Path(__file__).parent / "grounded.db"))
MODEL_REPO = "sentence-transformers/all-MiniLM-L6-v2"
# MiniLM's position limit. Passages longer than this are split at ingest, so
# nothing past the cap goes unembedded (measured cost of ignoring it: Phase 0).
MAX_TOKENS = 256
BATCH = 32
RRF_K = 60  # standard RRF constant; flattens the gap between rank 1 and rank 2


def _hf_file(filename: str) -> str:
    # hf_xet stalls on this machine; plain HTTP works.
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from huggingface_hub import hf_hub_download

    try:
        return hf_hub_download(MODEL_REPO, filename, local_files_only=True)
    except Exception:
        return hf_hub_download(MODEL_REPO, filename)


class Embedder:
    """Mean-pooled, L2-normalised MiniLM embeddings on onnxruntime, no torch."""

    def __init__(self) -> None:
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.session = ort.InferenceSession(
            _hf_file("onnx/model.onnx"), providers=["CPUExecutionProvider"]
        )
        self.tokenizer = Tokenizer.from_file(_hf_file("tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS)
        self.tokenizer.enable_padding()
        self._needs_type_ids = any(i.name == "token_type_ids" for i in self.session.get_inputs())

    def encode(self, texts: list[str]) -> np.ndarray:
        out = []
        for start in range(0, len(texts), BATCH):
            encs = self.tokenizer.encode_batch(texts[start : start + BATCH])
            ids = np.array([e.ids for e in encs], dtype=np.int64)
            mask = np.array([e.attention_mask for e in encs], dtype=np.int64)
            feeds = {"input_ids": ids, "attention_mask": mask}
            if self._needs_type_ids:
                feeds["token_type_ids"] = np.zeros_like(ids)
            hidden = self.session.run(None, feeds)[0]
            m = mask[..., None].astype(np.float32)
            emb = (hidden * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
            emb /= np.clip(np.linalg.norm(emb, axis=1, keepdims=True), 1e-9, None)
            out.append(emb.astype(np.float32))
        return np.vstack(out) if out else np.zeros((0, 384), np.float32)


SCHEMA = """
CREATE TABLE IF NOT EXISTS passages(
  id TEXT PRIMARY KEY,      -- provision ID, '#n' suffix when split for length
  provision TEXT NOT NULL,  -- e.g. DISP 1.6.2R; gold labels use this
  collection TEXT NOT NULL,
  text TEXT NOT NULL,
  status TEXT,              -- R rule, G guidance, D direction, E evidential
  doc_date TEXT,
  sha256 TEXT NOT NULL,
  vec BLOB NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS passages_fts USING fts5(id UNINDEXED, text);
"""


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def _fts_query(q: str) -> str:
    """Free text to a safe FTS5 OR-query. Keeping only \\w+ runs drops FTS5
    punctuation (quotes, hyphens, colons), and lowercasing defuses the
    operators, which FTS5 only recognises in upper case (AND, NOT, NEAR)."""
    return " OR ".join(re.findall(r"\w+", q.lower()))


def keyword(conn: sqlite3.Connection, q: str, k: int) -> list[str]:
    fq = _fts_query(q)
    if not fq:
        return []
    rows = conn.execute(
        "SELECT id FROM passages_fts WHERE passages_fts MATCH ? ORDER BY bm25(passages_fts) LIMIT ?",
        (fq, k),
    ).fetchall()
    return [r[0] for r in rows]


def dense(conn: sqlite3.Connection, q: str, k: int, emb: Embedder) -> list[str]:
    # ponytail: brute-force cosine; PRIN + DISP 1 is a few thousand passages at most.
    rows = conn.execute("SELECT id, vec FROM passages").fetchall()
    if not rows:
        return []
    mat = np.vstack([np.frombuffer(v, dtype=np.float32) for _, v in rows])
    scores = mat @ emb.encode([q])[0]
    return [rows[int(i)][0] for i in np.argsort(-scores)[:k]]


def hybrid(conn: sqlite3.Connection, q: str, k: int, emb: Embedder, depth: int = 50) -> list[str]:
    """Reciprocal rank fusion of the two rankings, each taken to `depth`."""
    fused: dict[str, float] = {}
    for ranking in (keyword(conn, q, depth), dense(conn, q, depth, emb)):
        for rank, pid in enumerate(ranking, 1):
            fused[pid] = fused.get(pid, 0.0) + 1.0 / (RRF_K + rank)
    return sorted(fused, key=lambda p: -fused[p])[:k]


def retrieve(conn, q: str, k: int, mode: str, emb: Embedder | None = None) -> list[str]:
    if mode == "keyword":
        return keyword(conn, q, k)
    emb = emb or Embedder()
    return dense(conn, q, k, emb) if mode == "dense" else hybrid(conn, q, k, emb)


def add_passages(conn, rows: list[dict], emb: Embedder) -> None:
    """rows: id, provision, collection, text, status, doc_date, sha256."""
    vecs = emb.encode([r["text"] for r in rows])
    conn.executemany(
        "INSERT INTO passages VALUES (?,?,?,?,?,?,?,?)",
        [(r["id"], r["provision"], r["collection"], r["text"], r.get("status"), r.get("doc_date"),
          r["sha256"], v.tobytes())
         for r, v in zip(rows, vecs)],
    )
    conn.executemany("INSERT INTO passages_fts(id, text) VALUES (?,?)", [(r["id"], r["text"]) for r in rows])
    conn.commit()


def _self_check() -> None:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    emb = Embedder()
    docs = {
        "DISP 1.6.2R": "A firm must send a final response to a complainant within eight weeks of receiving the complaint.",
        "PRIN 2.1.1R": "A firm must conduct its business with integrity.",
        "PRIN 2A.2.1R": "A firm must act to deliver good outcomes for retail customers.",
        "DISP 1.3.1R": "Effective and transparent procedures for the reasonable and prompt handling of complaints.",
    }
    add_passages(conn, [{"id": p, "provision": p, "collection": "t", "text": t, "sha256": "x"}
                        for p, t in docs.items()], emb)
    # Exact term: keyword must find it.
    assert keyword(conn, "eight weeks", 1) == ["DISP 1.6.2R"], keyword(conn, "eight weeks", 1)
    # BM25 order: "firm" is in three passages, "integrity" in one; the rare
    # term must win. (A one-match query cannot tell best-first from worst-first.)
    assert keyword(conn, "firm integrity", 1) == ["PRIN 2.1.1R"], keyword(conn, "firm integrity", 4)
    # FTS5 syntax in user text must not crash the query.
    assert keyword(conn, 'NOT "integrity" AND -firm:', 4)
    # Paraphrase with no shared content word: dense must find it, keyword cannot.
    q = "being honest and trustworthy"
    assert dense(conn, q, 1, emb) == ["PRIN 2.1.1R"], dense(conn, q, 4, emb)
    assert "PRIN 2.1.1R" not in keyword(conn, q, 4)
    # Hybrid honours k and carries the passage either retriever ranks first.
    h = hybrid(conn, "how long does a firm have to answer a complaint", 2, emb)
    assert len(h) == 2 and "DISP 1.6.2R" in h, h
    # Fusion must actually carry the dense ranking: this passage is invisible
    # to keyword, so a hybrid that silently drops dense cannot return it.
    assert "PRIN 2.1.1R" in hybrid(conn, q, 2, emb), hybrid(conn, q, 4, emb)
    print("self-check passed")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--mode", choices=["keyword", "dense", "hybrid"], default="hybrid")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        _self_check()
        return
    if not a.query:
        ap.error("give a query")
    conn = connect()
    for pid in retrieve(conn, a.query, a.k, a.mode):
        status, text = conn.execute("SELECT status, text FROM passages WHERE id=?", (pid,)).fetchone()
        print(f"{pid} {status} :: {' / '.join(text.splitlines())[:160]}")


if __name__ == "__main__":
    sys.exit(main())
