# Grounded

A small retrieval-augmented question answering system over two parts of the
FCA Handbook (PRIN, including the Consumer Duty, and DISP 1, complaints
handling). Every claim in an answer cites the provision it rests on, and the
system refuses when the retrieved provisions do not answer the question.

The point of the project is the evaluation, not the chatbot. The question set
and scoring rules were written and approved before anything was tuned, the
held-out split was run once after the system was frozen, and the results below
include the parts that went badly.

## How it works

- `ingest.py` parses the Handbook PDFs into 430 provisions (456 passages; the
  19 provisions longer than the embedder's 256-token limit are split into
  parts) and stores them in SQLite with full-text search and embeddings.
- `retrieve.py` has three retrievers at the same k: keyword (SQLite FTS5,
  BM25), dense (MiniLM embeddings on ONNX Runtime, no PyTorch) and hybrid
  (reciprocal rank fusion of the two).
- `answer.py` shows the model the top 5 provisions and asks for JSON: a list of
  claims, each citing provision IDs, or a refusal. Cited IDs must exactly
  match a provision the model was shown, otherwise the output is rejected.
  Collections not marked as safe to send are never sent to a model.
- `app.py` is a local web page: ask a question, read the answer, click a
  citation to see the provision text.
- `evaluate.py` (retrieval) and `evaluate_answers.py` (answers) produce the
  reports in `eval/reports/`. Every script has a `--self-check` that runs
  offline, and each self-check was mutation-tested: the code was broken on
  purpose and the check had to fail.

## Evaluation design (fixed before tuning)

60 questions, each approved by hand: 40 answerable (exact wording,
paraphrase, and multi-provision questions that need every gold provision) and
20 unanswerable, 9 of them near misses where the Handbook touches the topic but
holds no answer. Stratified split: 36 development, 24 held-out.

Answers score +1 for a correct answer or a correct refusal, 0 for refusing an
answerable question, and -1 for a wrong or unsupported answer. Refusing
everything scores the unanswerable share (0.333), so a system has to beat
that. A Claude Opus judge labels correctness and whether each claim is
supported by its cited passages. Each configuration runs 3 times and the
spread is reported.

## Results

### Retrieval (recall@5, provision level, 95% Wilson intervals)

| Retriever | Dev (24 answerable) | Held-out (16 answerable) |
|---|---|---|
| keyword | 0.708 [0.51-0.85] | 0.688 [0.44-0.86] |
| dense | 0.708 [0.51-0.85] | 0.250 [0.10-0.49] |
| hybrid | 0.708 [0.51-0.85] | 0.562 [0.33-0.77] |

On dev the three retrievers tied. On held-out, dense search fell to 4 of 16
and dragged the hybrid down with it, while plain keyword search held up. The
held-out set is small, so the intervals are wide, but the dense drop is
the largest effect in the project. Held-out failures are listed in
`eval/reports/2026-11-24-retrieval-heldout.md`.

### Answers

| Split | Score per run | Always-refuse baseline |
|---|---|---|
| Dev (36 questions) | 0.778, 0.722, 0.750 | 0.333 |
| Held-out (24 questions) | 0.542, 0.542, 0.542 | 0.333 |

Held-out was run once, on 24 November 2026, after the retriever, prompt and
judge were frozen (commit `bfbd487`). It beats the always-refuse baseline but
falls well short of dev, and the drop is mostly retrieval: the hybrid
retriever showed the gold provision for only 9 of the 16 answerable
questions. All 8 unanswerable questions were refused in every run. When the
gold was shown, 24 of 27 answers were correct; when it was not, the model
refused 15 times and answered wrongly 6 times.

Reading the held-out errors one by one:

- a01 (3 of the 3 wrong answers with gold shown): the judge marked the answer
  correct, but one claim attributed a detail to DISP 1.6.2 that comes from
  its neighbour DISP 1.6.2A. The scoring rule counts any unsupported claim as
  a wrong answer, so this citation slip costs a full point. It is also the
  only unsupported claim across all three runs (hallucination rate 0.028).
- a30 and a39 (all 6 wrong answers without gold): multi-provision questions
  where only one of the two provisions was retrieved. The model answered the
  half it could see and said the passages did not cover the rest. The scoring
  table has no partial-answer outcome, so these count as wrong.

Report: `eval/reports/2026-11-24-answers-heldout-v1.md`.

On dev, when the gold provision was among the 5 shown, 49 of 51 answers were
correct. When it was not, the model mostly refused (12 of 21), but 6 answers
were wrong: multi-provision questions where only one of two provisions was
retrieved, and the model answered the half it could see without saying the
other half was missing. So the errors sit mainly in retrieval, not in
answering.

### What did not work

Eleven retrieval variants were tried on dev, with the list fixed before any
was run (RRF weighting, stemming, scoping out the MiFID and Lloyd's mirror
sections, and others). None was statistically distinguishable from the
baseline on 24 questions (best p = 0.25, uncorrected). The best-looking one
(scoping, 17/24 to 20/24) was written after reading the failures and half of
it was untested, so it was not adopted, and held-out ran on the untuned
baseline.

## Known limits

- Small evaluation: 24 dev and 16 held-out answerable questions.
- The judge model is not yet checked against human labels; a 35-claim blind
  sample is drawn and waiting to be labelled.
- Mirror provisions: DISP repeats some rules for MiFID firms and Lloyd's, and
  the model sometimes cites the mirror instead of the general rule.
- The demo runs locally through the Claude CLI. It is not deployed.
- Live acceptance (`eval/live_script.md`) is written but not yet passed, so
  the page's status is "built, not yet accepted".

## Running it

Python 3.12. Dependencies: pypdf, numpy, onnxruntime, tokenizers,
huggingface_hub. Download PRIN and DISP 1 as PDFs from the FCA Handbook site
by hand into `corpus/raw/` (the Handbook terms do not allow crawling), then:

```
python ingest.py
python app.py            # http://127.0.0.1:8000
python evaluate.py       # retrieval, dev split
```

The answer step calls a logged-in `claude` CLI.

## Licence of the content

Contains FCA Handbook material, (c) FCA, reused under the Open Government
Licence v3. The PDFs and the built database are not in this repository.
Nothing here is advice.
