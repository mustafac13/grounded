# Live acceptance script (written 24 Nov 2026, before anyone ran the page)

Run `python app.py`, open http://127.0.0.1:8000 and ask each question in order.
For every answer, open every citation and check the passage actually says the
claim. Record per question: seconds shown on the page, outcome, and whether
every citation supported its claim. Status stays "built, not yet accepted"
until the full script passes 3 times on the same questions.

Locked targets (design note): "Working..." visible under 0.5 s after Ask;
warm answer or refusal p95 under 12 s; a hung model shows an error within
1 s of the 20 s timeout.

These are new questions, not rows from `questions.jsonl`. Three expected
provisions (DISP 1.3.1AA, DISP 1.9.1, DISP 1.6.2) are also gold for held-out
questions; this script was written after the system was frozen for held-out
(commit bfbd487) and changes nothing the held-out run uses, so the overlap
cannot affect that number. Expected provisions and absent
topics were checked against `grounded.db` (corpus 24649b93).

| # | Question | Expect | Provision(s) |
|---|---|---|---|
| 1 | Can a firm charge a customer for making a complaint? | answer: no, free of charge | DISP 1.3.1A |
| 2 | If I phone a firm's complaints line, can they charge me more than a basic rate? | answer: no more than basic rate | DISP 1.3.1AA |
| 3 | What does a firm have to do once it has received a complaint? | answer: investigate competently, diligently, impartially; assess fairly; offer redress where appropriate | DISP 1.4.1 |
| 4 | When does a complaint count as resolved? | answer: complainant has indicated acceptance of the response | DISP 1.5.2A |
| 5 | What should a firm send a complainant straight after receiving a complaint? | answer: a prompt written acknowledgement | DISP 1.6.1 |
| 6 | What records does a firm have to keep about complaints? | answer: each complaint and the measures taken for its resolution | DISP 1.9.1 |
| 7 | How often must a firm report its complaints to the FCA? | answer: twice a year | DISP 1.10.1 |
| 8 | Does the Consumer Duty make a firm a fiduciary for its customers? | answer: no fiduciary relationship created | PRIN 2A.1.11 |
| 9 | When a complaint comes in, what must the firm do first, and how long does it then have to send a final response? | answer from BOTH: acknowledgement, then final response within eight weeks | DISP 1.6.1 + DISP 1.6.2 |
| 10 | How much does the FSCS pay out if my bank fails? | refuse (FSCS not in collection) | none |
| 11 | What is the maximum interest a payday lender can charge? | refuse (CONC not in collection) | none |
| 12 | What is the minimum capital a bank must hold? | refuse (prudential rules not in collection) | none |

Before baseline (design note): ask the same 12 with plain keyword lookup,
`python retrieve.py "<question>" --mode keyword`, and record whether the
expected provision is in its top 5.

Measured 24 Nov, before the page was used, no model calls (top 5 distinct
provisions, 9 answerable questions; a two-provision question needs both):

| Retriever | Expected provision(s) in top 5 | Misses |
|---|---|---|
| keyword (the "before") | 7/9 | Q6 DISP 1.9.1, Q7 DISP 1.10.1 |
| hybrid (what the page uses) | 7/9 | Q5 DISP 1.6.1, Q7 DISP 1.10.1 |

So on Q5 and Q7 the page is expected to refuse or answer from another
provision: a retrieval miss, not a page fault. Record what it actually does.

## Results

| Pass | Date | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 | Q11 | Q12 | p95 s | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | | | | | | | |
| 2 | | | | | | | | | | | | | | | |
| 3 | | | | | | | | | | | | | | | |
