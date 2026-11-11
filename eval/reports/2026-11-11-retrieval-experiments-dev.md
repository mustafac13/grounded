# Retrieval experiments, dev split

```json
{
  "timestamp": "2026-11-11T09:33:46+00:00",
  "corpus_sha256": "24649b93ffefcd784d388f67ade0b83c8ad4fd1e4847c7799e80039f327b4c2d",
  "questions_sha256": "4c5aa45ba91af22486e0f759211280da91b3e9280b585549c7335c125057c68d",
  "split": "dev (answerable only)",
  "n": 24,
  "variants_fixed_before_running": [
    "baseline",
    "dense",
    "dense_x2",
    "hybrid_stem",
    "interleave",
    "keyword",
    "keyword_stem",
    "keyword_x2",
    "rrf_k10",
    "scope",
    "scope_stem"
  ],
  "scopes": {
    "DISP 1.1A.": [
      "mifid",
      "investment firm"
    ],
    "DISP 1.11.": [
      "lloyd",
      "society"
    ]
  },
  "recall_k": 5,
  "mrr_k": 10
}
```

The variant list was fixed before any variant was run and all of them are shown. Wins and losses are questions whose recall@5 outcome differs from the baseline; p is an exact two-sided sign test on those, uncorrected for the ten comparisons. Rank better/worse compares reciprocal rank at 10. With 24 questions nothing here is a finding until it holds on held-out.

| Variant | recall@5 [95% Wilson] | MRR@10 | wins | losses | p | rank better | rank worse | exact | paraphrase | multi |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.708 (17/24) [0.51-0.85] | 0.532 | 0  | 0  | 1.00 | 0 | 0 | 7/7 | 5/10 | 5/7 |
| keyword | 0.708 (17/24) [0.51-0.85] | 0.439 | 1 a40 | 1 a08 | 1.00 | 4 | 9 | 6/7 | 5/10 | 6/7 |
| dense | 0.708 (17/24) [0.51-0.85] | 0.509 | 1 a16 | 1 a35 | 1.00 | 5 | 10 | 7/7 | 6/10 | 4/7 |
| keyword_stem | 0.625 (15/24) [0.43-0.79] | 0.443 | 2 a27 a40 | 4 a06 a08 a32 a35 | 0.69 | 3 | 10 | 5/7 | 6/10 | 4/7 |
| hybrid_stem | 0.708 (17/24) [0.51-0.85] | 0.484 | 1 a27 | 1 a08 | 1.00 | 3 | 8 | 6/7 | 6/10 | 5/7 |
| rrf_k10 | 0.792 (19/24) [0.60-0.91] | 0.547 | 2 a16 a40 | 0  | 0.50 | 4 | 3 | 7/7 | 6/10 | 6/7 |
| dense_x2 | 0.750 (18/24) [0.55-0.88] | 0.537 | 1 a16 | 0  | 1.00 | 4 | 2 | 7/7 | 6/10 | 5/7 |
| keyword_x2 | 0.708 (17/24) [0.51-0.85] | 0.543 | 1 a40 | 1 a08 | 1.00 | 3 | 5 | 6/7 | 5/10 | 6/7 |
| interleave | 0.750 (18/24) [0.55-0.88] | 0.459 | 3 a16 a37 a40 | 2 a28 a35 | 1.00 | 6 | 8 | 7/7 | 5/10 | 6/7 |
| scope | 0.833 (20/24) [0.64-0.93] | 0.541 | 3 a16 a25 a37 | 0  | 0.25 | 3 | 1 | 7/7 | 7/10 | 6/7 |
| scope_stem | 0.792 (19/24) [0.60-0.91] | 0.520 | 2 a25 a27 | 0  | 0.50 | 4 | 6 | 7/7 | 7/10 | 5/7 |

## Rank of the gold, per question

Provision rank of the gold (last gold for multi questions needing all); `-` means outside the top 50 passages. Questions the baseline misses at 5 are marked with *.

| id | type | baseline | keyword | dense | keyword_stem | hybrid_stem | rrf_k10 | dense_x2 | keyword_x2 | interleave | scope | scope_stem |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a02 | exact | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| a03 | exact | 1 | 1 | 2 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 |
| a04 | exact | 2 | 2 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 |
| a06 | exact | 1 | 4 | 1 | 8 | 2 | 1 | 1 | 2 | 2 | 1 | 2 |
| a08 | exact | 5 | 15 | 2 | 20 | 6 | 4 | 3 | 6 | 4 | 5 | 5 |
| a09 | exact | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| a11 | exact | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| a15* | paraphrase | 26 | 8 | - | 35 | 65 | 23 | 53 | 20 | 15 | 20 | 54 |
| a16* | paraphrase | 6 | 49 | 2 | - | 11 | 3 | 5 | 7 | 4 | 3 | 8 |
| a17 | paraphrase | 1 | 2 | 3 | 1 | 1 | 1 | 1 | 1 | 3 | 1 | 1 |
| a18* | paraphrase | 22 | - | 6 | 31 | 21 | 16 | 19 | 49 | 10 | 22 | 21 |
| a19 | paraphrase | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| a21 | paraphrase | 1 | 4 | 1 | 4 | 1 | 1 | 1 | 1 | 2 | 1 | 1 |
| a23 | paraphrase | 3 | 1 | 1 | 1 | 2 | 2 | 3 | 1 | 1 | 4 | 1 |
| a25* | paraphrase | 7 | 27 | 21 | 26 | 6 | 15 | 7 | 7 | 37 | 5 | 5 |
| a27* | paraphrase | 7 | 21 | 8 | 3 | 3 | 10 | 6 | 8 | 14 | 7 | 3 |
| a28 | paraphrase | 2 | 4 | 4 | 3 | 2 | 2 | 2 | 2 | 6 | 2 | 2 |
| a32 | multi | 2 | 2 | 3 | 6 | 4 | 2 | 2 | 2 | 3 | 2 | 4 |
| a33 | multi | 2 | 2 | 2 | 4 | 3 | 2 | 2 | 2 | 2 | 2 | 3 |
| a35 | multi | 2 | 5 | 6 | 6 | 4 | 3 | 2 | 3 | 8 | 2 | 4 |
| a36 | multi | 2 | 2 | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| a37* | multi | 9 | 8 | 13 | 13 | 11 | 9 | 9 | 8 | 5 | 5 | 6 |
| a38 | multi | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| a40* | multi | 6 | 3 | 41 | 2 | 8 | 2 | 9 | 2 | 4 | 6 | 8 |
