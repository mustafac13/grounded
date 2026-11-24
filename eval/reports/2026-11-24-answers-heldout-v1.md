# Answer evaluation, heldout split

```json
{
  "timestamp": "2026-11-24T19:37:40+00:00",
  "corpus_sha256": "24649b93ffefcd784d388f67ade0b83c8ad4fd1e4847c7799e80039f327b4c2d",
  "questions_sha256": "4c5aa45ba91af22486e0f759211280da91b3e9280b585549c7335c125057c68d",
  "split": "heldout, 24 questions (16 answerable, 8 unanswerable)",
  "retriever": "hybrid",
  "k_provisions": 5,
  "runs": 3,
  "answer_model": [
    "claude-sonnet-5-5"
  ],
  "judge_model": [
    "claude-opus-5-5"
  ],
  "prompt_version": "v1",
  "judge_version": "v1",
  "refusal_rule": "model-only (no retrieval-score floor)",
  "tokens_answer_in_out": [
    155195,
    16580
  ],
  "tokens_judge_in_out": [
    81758,
    6829
  ],
  "failed_calls_retried": 0
}
```

Score is the mean of +1 (correct answer or correct refusal), 0 (false refusal or invalid output) and -1 (wrong or unsupported answer). Refusing everything would score 8/24 = 0.333. Support labels come from the judge model only; the human sample in `heldout-v1/human_sample.md` is not labelled yet, so judge agreement is unknown.

## Per run

| Run | Score | Right outcome [95% Wilson] | correct | correct refusal | false refusal | invalid | wrong |
|---|---|---|---|---|---|---|---|
| 1 | 0.542 | 16/24 [0.47-0.82] | 8 | 8 | 5 | 0 | 3 |
| 2 | 0.542 | 16/24 [0.47-0.82] | 8 | 8 | 5 | 0 | 3 |
| 3 | 0.542 | 16/24 [0.47-0.82] | 8 | 8 | 5 | 0 | 3 |

Spread across runs: min 0.542, median 0.542, max 0.542.

Correct answers that did NOT cite the gold provision, per run: run 1: none; run 2: none; run 3: none. These count +1 in the score as designed, but each one rests on a provision the labelling does not accept as gold, so read them before quoting the score.

## Support (judge labels)

| Run | Claims | Material | Hallucination rate | Citation precision | Coverage |
|---|---|---|---|---|---|
| 1 | 34 | 34 | 0.029 | 0.971 | 1.000 |
| 2 | 36 | 36 | 0.028 | 0.972 | 1.000 |
| 3 | 36 | 36 | 0.028 | 0.972 | 1.000 |

Hallucination rate = unsupported material claims / material claims. Citation precision = cited claims whose citations support them / cited claims. Coverage = claims with at least one citation / claims.

## Answerable questions by whether retrieval found the gold

Pooled over runs. This separates retrieval misses from answer mistakes. A question whose gold provision was not shown should be refused; an answer marked correct there was built from a different provision (a mirror provision for another population, for example) and needs reading.

| Gold in the passages shown | correct | false refusal | invalid | wrong |
|---|---|---|---|---|
| yes (9 questions) | 24 | 0 | 0 | 3 |
| no (7 questions) | 0 | 15 | 0 | 6 |

## Every question

| id | type | gold shown | outcome per run |
|---|---|---|---|
| a01 | exact | yes | wrong / wrong / wrong |
| a05 | exact | no | false_refusal / false_refusal / false_refusal |
| a07 | exact | yes | correct / correct / correct |
| a10 | exact | yes | correct / correct / correct |
| a12 | exact | yes | correct / correct / correct |
| a13 | paraphrase | no | false_refusal / false_refusal / false_refusal |
| a14 | paraphrase | yes | correct / correct / correct |
| a20 | paraphrase | no | false_refusal / false_refusal / false_refusal |
| a22 | paraphrase | yes | correct / correct / correct |
| a24 | paraphrase | no | false_refusal / false_refusal / false_refusal |
| a26 | paraphrase | yes | correct / correct / correct |
| a29 | multi | no | false_refusal / false_refusal / false_refusal |
| a30 | multi | no | wrong / wrong / wrong |
| a31 | multi | yes | correct / correct / correct |
| a34 | multi | yes | correct / correct / correct |
| a39 | multi | no | wrong / wrong / wrong |
| u01 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u02 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u05 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u06 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u12 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u13 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u18 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u20 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |

## Outputs that were not right (run 1)

### a01 (exact): wrong

Question: What must a respondent send the complainant by the end of eight weeks after its receipt of the complaint?

Reference: Either a final response (accepting the complaint, offering redress without accepting it, or rejecting it with reasons, enclosing the Financial Ombudsman Service leaflet and website address, saying the complainant may now refer to the Ombudsman, and saying whether the firm waives the referral time limits), or a written response explaining why it cannot yet give a final response and when it expects to, and that the complainant may now refer to the Ombudsman.

Gold: DISP 1.6.2. Shown: DISP 1.6.2A, DISP 1.6.7, DISP 1.6.1, DISP 1.6.2, DISP 1.1A.28.

- Subject to DISP 1.6.2AR (which applies to EMD and PSD complaints), a respondent must, by the end of eight weeks after receiving the complaint, send the complainant either a 'final response' or a written response explaining why it cannot yet give a final response. [DISP 1.6.2] (material True, supported False)
- A 'final response' is a written response that accepts the complaint (offering redress or remedial action where appropriate), or offers redress or remedial action without accepting the complaint, or rejects the complaint and gives reasons. [DISP 1.6.2] (material True, supported True)
- A final response must also enclose a copy of the Financial Ombudsman Service's standard explanatory leaflet, provide the FOS website address, inform the complainant that they may now refer the complaint to the FOS if still dissatisfied, and indicate whether the respondent consents to waive the relevant time limits in DISP 2.8.2 R or DISP 2.8.7 R. [DISP 1.6.2] (material True, supported True)
- The alternative written response must explain why the respondent cannot make a final response and indicate when it expects to be able to provide one, inform the complainant that they may now refer the complaint to the FOS, indicate whether the respondent consents to waive the relevant time limits if the complaint turns out to be outside them, enclose the FOS standard explanatory leaflet, and provide the FOS website address. [DISP 1.6.2] (material True, supported True)

Judge: correct=True. The answer matches the reference in full; claim 1's gloss that DISP 1.6.2AR covers EMD and PSD complaints comes from DISP 1.6.2A, which that claim does not cite.

### a05 (exact): false_refusal

Question: Which Consumer Duty cross-cutting obligation deals with foreseeable harm to retail customers?

Reference: A firm must avoid causing foreseeable harm to retail customers.

Gold: PRIN 2A.2.8. Shown: PRIN 2A.2.27, PRIN 2A.1.10, PRIN 2A.2.25, PRIN 2A.9.1, PRIN 2A.9.2.

Refused: The passages describe the cross-cutting obligations generally but do not identify any obligation dealing with avoiding foreseeable harm to retail customers.

### a13 (paraphrase): false_refusal

Question: How long does a firm have to resolve a complaint?

Reference: Eight weeks from receipt to send a final response, or a written response explaining the delay.

Gold: DISP 1.6.2, DISP 1.6.7. Shown: DISP 1.11.4, DISP 1.2.3, DISP 1.4.3, DISP 1.10.3, DISP 1.11.18.

Refused: The passages do not state a general time limit for a firm to resolve a complaint; they only say complaints should be resolved at the earliest possible opportunity and give an eight-week point that applies to complaints against members of Lloyd's.

### a20 (paraphrase): false_refusal

Question: Is a firm still allowed to make a profit under the Consumer Duty?

Reference: Yes. Acting in good faith does not stop a firm pursuing legitimate commercial interests or seeking a profit, provided it complies with the Duty.

Gold: PRIN 2A.2.4. Shown: PRIN 3.2.10, PRIN 3.1.13, PRIN 3.2.6, PRIN 2A.1.13, PRIN 2A.1.17.

Refused: The passages cover the scope and application of the Consumer Duty and its relationship to Principles 6 and 7, but none of them says whether a firm may or may not make a profit under it.

### a24 (paraphrase): false_refusal

Question: Does a firm have to tell customers how its complaints process works?

Reference: Yes. It must publish information on its internal complaints procedures, refer eligible complainants to it (in writing at or after the point of sale for most products), and provide it in writing free of charge on request and when acknowledging a complaint.

Gold: DISP 1.2.1. Shown: DISP 1.3.6, PRIN 2A.2.5, DISP 1.1A.13, DISP 1.3.3B, DISP 1.2.3.

Refused: The passages say what a complaints management policy and summary details of complaints procedures should contain, but none states that a firm must give this information to customers.

### a29 (multi): false_refusal

Question: How do the deadlines for answering a payment services complaint differ from those for other complaints?

Reference: Other complaints: a final or written response within eight weeks. Payment services and e-money complaints: a final response within 15 business days, or in exceptional circumstances a holding response within 15 and a final response within 35 business days.

Gold: DISP 1.6.2, DISP 1.6.2A. Shown: DISP 1.6.2A, DISP 1.1.3A, DISP 1.1.10AB, DISP 1.9.1, DISP 1.10B.2.

Refused: The passages set out the deadlines for EMD and PSD complaints (15 business days, or 35 in exceptional circumstances), but none states the deadlines for other complaints, so no comparison can be made.

### a30 (multi): wrong

Question: If a firm resolves a complaint within three business days, which rules does it skip and what must it send instead?

Reference: The complaints time limit and forwarding rules do not apply; it must promptly send a summary resolution communication saying the complaint is resolved, that the complainant may be able to refer to the Ombudsman, whether it waives the time limits, and the Ombudsman's website.

Gold: DISP 1.5.1, DISP 1.5.4. Shown: DISP 1.6.2A, DISP 1.5.1, DISP 1.6.1, DISP 1.1A.28, DISP 1.9.1.

- A complaint resolved by close of business on the third business day after the day it is received is exempt from two sets of rules: the complaints time limit rules and the complaints forwarding rules. [DISP 1.5.1] (material True, supported True)
- DISP 1.5.1 only disapplies those rules. It does not say what the firm must send instead, and none of the other supplied passages say so either. [DISP 1.5.1] (material True, supported True)

Judge: correct=False. The answer names the two disapplied rule sets but leaves out the essential requirement to send a summary resolution communication and what it must contain.

### a39 (multi): wrong

Question: What complaints procedures must a firm have, and how should it deal with recurring problems?

Reference: Effective and transparent procedures for reasonable and prompt handling of complaints, plus management controls to identify and remedy recurring or systemic problems through root cause analysis.

Gold: DISP 1.3.1, DISP 1.3.3. Shown: DISP 1.3.6, DISP 1.3.3, DISP 1.1.1, DISP 1.2.3, PRIN 2A.2.5.

- The passages do not set out a full list of complaints procedures a firm must have. They say only that summary details of internal complaints handling procedures should cover at least how the respondent fulfils its obligation to handle and seek to resolve relevant complaints and, where the complaint falls within the Financial Ombudsman Service's jurisdiction, that an unresolved complainant may be entitled to refer it to the Ombudsman. [DISP 1.2.3] (material True, supported True)
- A respondent must put in place appropriate management controls and take reasonable steps to ensure that, in handling complaints, it identifies and remedies any recurring or systemic problems. [DISP 1.3.3] (material True, supported True)
- Examples of how to do this are analysing the causes of individual complaints to identify common root causes, considering whether those root causes may also affect other processes or products (including those not complained of), and correcting root causes where reasonable to do so. [DISP 1.3.3] (material True, supported True)
- Where a firm identifies recurring or systemic problems, it should consider whether it ought to act regarding customers who may have suffered detriment but have not complained, and if so take appropriate and proportionate measures to ensure they are given appropriate redress or a proper opportunity to obtain it. [DISP 1.3.6] (material True, supported True)
- In doing so, the firm should ascertain the scope and severity of the consumer detriment that might have arisen, and consider whether it is fair and reasonable to proactively undertake a redress or remediation exercise, which may include contacting customers who have not complained. [DISP 1.3.6] (material True, supported True)
- If a firm identifies, through complaints, internal monitoring or any other source, that retail customers have suffered foreseeable harm as a result of its acts or omissions, it must act in good faith and take appropriate action to rectify the situation, including providing redress where appropriate. [PRIN 2A.2.5] (material True, supported True)

Judge: correct=False. The recurring-problems part is covered, but the answer omits the core requirement for effective, transparent procedures for reasonable and prompt complaint handling.

