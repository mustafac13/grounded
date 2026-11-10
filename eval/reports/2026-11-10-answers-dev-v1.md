# Answer evaluation, dev split

```json
{
  "timestamp": "2026-11-10T23:46:39+00:00",
  "corpus_sha256": "24649b93ffefcd784d388f67ade0b83c8ad4fd1e4847c7799e80039f327b4c2d",
  "questions_sha256": "4c5aa45ba91af22486e0f759211280da91b3e9280b585549c7335c125057c68d",
  "split": "dev, 36 questions (24 answerable, 12 unanswerable)",
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
    256531,
    23821
  ],
  "tokens_judge_in_out": [
    152494,
    9016
  ],
  "failed_calls_retried": 0
}
```

Score is the mean of +1 (correct answer or correct refusal), 0 (false refusal or invalid output) and -1 (wrong or unsupported answer). Refusing everything would score 12/36 = 0.333. Support labels come from the judge model only; the human sample in `dev-v1/human_sample.md` is not labelled yet, so judge agreement is unknown.

## Per run

| Run | Score | Right outcome [95% Wilson] | correct | correct refusal | false refusal | invalid | wrong |
|---|---|---|---|---|---|---|---|
| 1 | 0.778 | 30/36 [0.68-0.92] | 18 | 12 | 4 | 0 | 2 |
| 2 | 0.722 | 29/36 [0.65-0.90] | 17 | 12 | 4 | 0 | 3 |
| 3 | 0.750 | 29/36 [0.65-0.90] | 17 | 12 | 5 | 0 | 2 |

Spread across runs: min 0.722, median 0.750, max 0.778.

Correct answers that did NOT cite the gold provision, per run: run 1: a16; run 2: a16; run 3: a16. These count +1 in the score as designed, but each one rests on a provision the labelling does not accept as gold, so read them before quoting the score.

## Support (judge labels)

| Run | Claims | Material | Hallucination rate | Citation precision | Coverage |
|---|---|---|---|---|---|
| 1 | 59 | 59 | 0.000 | 1.000 | 1.000 |
| 2 | 61 | 61 | 0.016 | 0.984 | 1.000 |
| 3 | 57 | 57 | 0.000 | 1.000 | 1.000 |

Hallucination rate = unsupported material claims / material claims. Citation precision = cited claims whose citations support them / cited claims. Coverage = claims with at least one citation / claims.

## Answerable questions by whether retrieval found the gold

Pooled over runs. This separates retrieval misses from answer mistakes. A question whose gold provision was not shown should be refused; an answer marked correct there was built from a different provision (a mirror provision for another population, for example) and needs reading.

| Gold in the passages shown | correct | false refusal | invalid | wrong |
|---|---|---|---|---|
| yes (17 questions) | 49 | 1 | 0 | 1 |
| no (7 questions) | 3 | 12 | 0 | 6 |

## Every question

| id | type | gold shown | outcome per run |
|---|---|---|---|
| a02 | exact | yes | correct / correct / correct |
| a03 | exact | yes | correct / correct / correct |
| a04 | exact | yes | correct / correct / correct |
| a06 | exact | yes | correct / correct / correct |
| a08 | exact | yes | correct / correct / correct |
| a09 | exact | yes | correct / correct / correct |
| a11 | exact | yes | correct / correct / correct |
| a15 | paraphrase | no | false_refusal / false_refusal / false_refusal |
| a16 | paraphrase | no | correct / correct / correct |
| a17 | paraphrase | yes | correct / wrong / correct |
| a18 | paraphrase | no | false_refusal / false_refusal / false_refusal |
| a19 | paraphrase | yes | correct / correct / correct |
| a21 | paraphrase | yes | correct / correct / false_refusal |
| a23 | paraphrase | yes | correct / correct / correct |
| a25 | paraphrase | no | false_refusal / false_refusal / false_refusal |
| a27 | paraphrase | no | false_refusal / false_refusal / false_refusal |
| a28 | paraphrase | yes | correct / correct / correct |
| a32 | multi | yes | correct / correct / correct |
| a33 | multi | yes | correct / correct / correct |
| a35 | multi | yes | correct / correct / correct |
| a36 | multi | yes | correct / correct / correct |
| a37 | multi | no | wrong / wrong / wrong |
| a38 | multi | yes | correct / correct / correct |
| a40 | multi | no | wrong / wrong / wrong |
| u03 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u04 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u07 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u08 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u09 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u10 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u11 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u14 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u15 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u16 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u17 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |
| u19 | unanswerable | - | correct_refusal / correct_refusal / correct_refusal |

## Outputs that were not right (run 1)

### a15 (paraphrase): false_refusal

Question: My complaint is really about another company's mistake. Can the firm pass it on to them?

Reference: Yes, if it has reasonable grounds to think the other firm is solely or jointly responsible. It must forward it promptly in writing, tell the complainant promptly in a final response why and give the other firm's contact details, and deal with any part it is jointly responsible for.

Gold: DISP 1.7.1. Shown: DISP 1.10.3, DISP 1.10.1B, DISP 1.1A.20, DISP 1.1A.25, DISP 1.1A.4.

Refused: The passages do not say whether or how a firm may pass a complaint on to another company; they only mention assessing whether another respondent is responsible and how forwarded or jointly handled complaints are reported.

### a18 (paraphrase): false_refusal

Question: Which Principle says a firm has to be honest?

Reference: Principle 1 (Integrity): a firm must conduct its business with integrity. The Consumer Duty's good-faith standard (PRIN 2A.2.2) also names honesty explicitly; either is accepted.

Gold: PRIN 2.1.1, PRIN 2A.2.2. Shown: PRIN 1.1.7, PRIN 1.1.6, PRIN 3.3.1, PRIN 1.2.1, PRIN 3.2.3.

Refused: The passages name Principle 1 as 'Integrity' but never mention honesty or say that Principle 1 requires a firm to be honest.

### a25 (paraphrase): false_refusal

Question: What steps does a firm have to take to look into a complaint properly?

Reference: Investigate competently, diligently and impartially; assess fairly, consistently and promptly whether to uphold it and what redress fits; offer redress where appropriate; explain its decision clearly; and comply promptly with any redress accepted.

Gold: DISP 1.4.1. Shown: PRIN 2A.2.5, DISP 1.11.3, DISP 1.10.3, DISP 1.3.3, DISP 1.3.6.

Refused: The passages do not set out the steps a firm must take to investigate an individual complaint; they only cover analysing complaint root causes, dealing with systemic problems, and reporting.

### a27 (paraphrase): false_refusal

Question: If an investment firm sorts out a MiFID complaint within three days, does it still have to follow the full time limit rules?

Reference: No. If resolved by close of business on the third business day it may comply with DISP 1.1A.24R to 1.1A.27G instead of 1.1A.28R to 1.1A.34G.

Gold: DISP 1.1A.23. Shown: DISP 1.1A.26, DISP 1.1A.36, DISP 1.1A.28, DISP 1.1A.34, DISP 1.1A.31.

Refused: The passages do not say whether resolving a MiFID complaint within three days exempts a firm from the time limit rules; DISP 1.1A.25R, which would set out any such treatment, is not included.

### a37 (multi): wrong

Question: When must a firm publish a summary of its complaints data, and by what date?

Reference: When its report shows 500 or more complaints (1000 for certain small credit, claims management and funeral plan firms). By 31 August if the reporting period ends between January and June, or by 28 February the following year if it ends between July and December.

Gold: DISP 1.10A.1, DISP 1.10A.3. Shown: DISP 1.11.6E, DISP 1.10A.3, DISP 1.10A.7, DISP 1.11.6A, DISP 1.10A.11.

- Where a firm's relevant reporting period ends between 1 January and 30 June, the firm must publish the complaints data summary no later than 31 August of the same year. [DISP 1.10A.3] (material True, supported True)
- Where a firm's relevant reporting period ends between 1 July and 31 December, the firm must publish the complaints data summary no later than 28 February of the following year. [DISP 1.10A.3] (material True, supported True)
- A firm with only a limited permission must publish the total number of complaints received no later than 28 February of the following year. [DISP 1.10A.3] (material True, supported True)

Judge: correct=False. The deadlines are accurate, but the answer omits the 500/1000-complaint threshold that triggers the duty to publish.

### a40 (multi): wrong

Question: What happens if a firm breaches a Principle: can the FCA discipline it, and can a customer sue under section 138D?

Reference: The firm is liable to disciplinary sanctions, with the onus on the FCA to show fault; but a breach of PRIN gives no private right of action under section 138D.

Gold: PRIN 1.1.7, PRIN 3.4.4. Shown: PRIN 1.1.7, PRIN 2A.9.16, PRIN 1.1.5, PRIN 1.1.6, DISP 1.1.12.

- Breaching a Principle makes a firm (or other person to whom the Principles apply) liable to disciplinary sanctions. [PRIN 1.1.7] (material True, supported True)
- The onus is on the FCA to show that the firm has been at fault in some way, and what counts as fault varies between Principles; for example, under Principle 2 a breach requires a failure to act with due skill, care and diligence, and under Principle 3 a firm is not in breach merely because it failed to control or prevent unforeseeable risks. [PRIN 1.1.7] (material True, supported True)

Judge: correct=False. Both claims are supported by PRIN 1.1.7, but the answer never says that a breach of PRIN gives no private right of action under section 138D, which the reference treats as essential.

