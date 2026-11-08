# Retrieval evaluation, dev split (untuned baseline)

```json
{
  "timestamp": "2026-11-08T00:31:28+00:00",
  "corpus_sha256": "24649b93ffefcd784d388f67ade0b83c8ad4fd1e4847c7799e80039f327b4c2d",
  "questions_sha256": "4c5aa45ba91af22486e0f759211280da91b3e9280b585549c7335c125057c68d",
  "split": "dev (answerable only)",
  "retrievers": {
    "keyword": "FTS5 BM25, OR-query of \\w+ terms",
    "dense": "sentence-transformers/all-MiniLM-L6-v2 ONNX, mean-pooled, cosine, max 256 tokens",
    "hybrid": "RRF k=60, each ranking to depth 50"
  },
  "fetch_depth_passages": 50,
  "recall_k": 5,
  "mrr_k": 10
}
```

Recall@5 is the share of questions whose gold (any/all per gold_mode) is in the top 5 distinct provisions, with a Wilson 95% interval. MRR@10 uses the first gold for `any` and the last gold for `all`; it has no interval here.

## Overall

| Retriever | n | recall@5 [95% Wilson] | MRR@10 |
|---|---|---|---|
| keyword | 24 | 0.708 (17/24) [0.51-0.85] | 0.439 |
| dense | 24 | 0.708 (17/24) [0.51-0.85] | 0.509 |
| hybrid | 24 | 0.708 (17/24) [0.51-0.85] | 0.532 |

## By question type

| Type | Retriever | n | recall@5 [95% Wilson] | MRR@10 |
|---|---|---|---|---|
| exact | keyword | 7 | 0.857 (6/7) [0.49-0.97] | 0.679 |
| exact | dense | 7 | 1.000 (7/7) [0.65-1.00] | 0.857 |
| exact | hybrid | 7 | 1.000 (7/7) [0.65-1.00] | 0.814 |
| paraphrase | keyword | 10 | 0.500 (5/10) [0.24-0.76] | 0.312 |
| paraphrase | dense | 10 | 0.600 (6/10) [0.31-0.83] | 0.438 |
| paraphrase | hybrid | 10 | 0.500 (5/10) [0.24-0.76] | 0.429 |
| multi | keyword | 7 | 0.857 (6/7) [0.49-0.97] | 0.380 |
| multi | dense | 7 | 0.571 (4/7) [0.25-0.84] | 0.262 |
| multi | hybrid | 7 | 0.714 (5/7) [0.36-0.92] | 0.397 |

## Failures (hybrid misses at k=5)

7 of 24 dev questions. Gold ranks come from the hybrid ranking deduplicated to provisions from a 50-passage fetch; "not in top fetch" means beyond that depth. Five of the seven have every gold within rank 9, so these are mostly ranking misses, not absent passages; two (a15, a18) are genuine wording gaps.

### a15 (paraphrase, gold_mode any)

Question: My complaint is really about another company's mistake. Can the firm pass it on to them?

Gold: DISP 1.7.1. Hybrid provision rank of each gold: DISP 1.7.1: 26. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- DISP 1.10.3: DISP 1.10.3 (part 1) For the purposes of DISP 1.10.2R, DISP 1.10.2-AR, DISP 1.10.2BR and DISP 1.10.2CR, when completing the return, the firm
- DISP 1.10.1B: Where a firm has forwarded to another respondent only part of a complaint or where two respondents may be jointly responsible for a complain
- DISP 1.1A.20: Complaints resolution Once a MiFID complaint has been received by a MiFID investment firm, the firm must: (1) investigate the complaint comp
- DISP 1.1A.25: MiFID Investment firms must communicate their position on the MiFID complaint to clients or potential clients and inform the clients or pote
- DISP 1.1A.4: A MiFID complaint is also a complaint about the equivalent business of a third country investment firm. [Note: see articles 39 and 41 of MiF

Why (guess, written by hand after reading the gold text): wording gap: the question says "pass it on" and "another company", the rule says "forward" and "another respondent"; DISP 1.10.1B (a reporting rule about forwarded complaints) takes the slot because it shares "another respondent" and "complaint".

### a16 (paraphrase, gold_mode any)

Question: Can a firm refuse to look at a complaint because it is too old?

Gold: DISP 1.8.1. Hybrid provision rank of each gold: DISP 1.8.1: 6. At k=5: keyword miss, dense hit.

Retrieved instead (hybrid top 5):

- DISP 1.1.10L: Although designated finance platforms are not required to comply with the complaints record rule, they must retain records in accordance wit
- DISP 1.9.1: A firm, a payment service provider or an e-money issuer, must keep a record of each complaint received and the measures taken for its resolu
- DISP 1.1A.28: Complaints time limits On receipt of a MiFID complaint, a MiFID investment firm must: (1) send the complainant a prompt written acknowledgem
- DISP 1.1A.34: DISP 2.8.1R sets out the circumstances in which the Ombudsman can consider a complaint, including where eight weeks have elapsed since its r
- DISP 1.1A.36: Complaints time barring If a MiFID investment firm receives a MiFID complaint which is outside the time limits for referral to the Financial

Why (guess, written by hand after reading the gold text): near miss (rank 6) plus duplicate topic: the MiFID mirror of the same rule (DISP 1.1A.36, "Complaints time barring") outranks the general one; "too old" never appears, the rule says "outside the time limits".

### a18 (paraphrase, gold_mode any)

Question: Which Principle says a firm has to be honest?

Gold: PRIN 2.1.1, PRIN 2A.2.2. Hybrid provision rank of each gold: PRIN 2.1.1: 22, PRIN 2A.2.2: not in top fetch. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- PRIN 1.1.7: Consequences of breaching the Principles Breaching a Principle makes a firm or other person to whom the Principles apply liable to disciplin
- PRIN 1.1.6: Standards in markets outside the United Kingdom As set out in PRIN 3.3 (Where?), Principles 1 (Integrity), 2 (Skill, care and diligence) and
- PRIN 3.3.1: PRIN 3.3.1 (part 1) Territorial application of the Principles Principle Territorial application Principles 1, 2 and 3 in a prudential contex
- PRIN 1.2.1: Characteristics of the client Principles 6 (Customers' interests), 7 (Communications with clients), 8 (Conflicts of interest), 9 (Customers:
- PRIN 3.2.3: Subject to PRIN 3.2.4R, Principles 3, 4 and (in so far as it relates to disclosing to the FCA) 11 (and this chapter) also: (1) apply to firm

Why (guess, written by hand after reading the gold text): wording gap and no stemming: the only "honest" text is "honesty" in PRIN 2A.2.2, and FTS5's default tokenizer does not stem, so keyword cannot match it; "Principle" pulls in PRIN 1 and 3 meta-provisions about the Principles instead; PRIN 2.1.1 is split in two parts and "integrity" is never asked about.

### a25 (paraphrase, gold_mode any)

Question: What steps does a firm have to take to look into a complaint properly?

Gold: DISP 1.4.1. Hybrid provision rank of each gold: DISP 1.4.1: 7. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- PRIN 2A.2.5: If a firm identifies through complaints, its internal monitoring or from any other source, that retail customers have suffered foreseeable h
- DISP 1.11.3: The Society must take reasonable steps to ensure that complaints by policyholders against members of the Society are dealt with under the Ll
- DISP 1.10.3: DISP 1.10.3 (part 1) For the purposes of DISP 1.10.2R, DISP 1.10.2-AR, DISP 1.10.2BR and DISP 1.10.2CR, when completing the return, the firm
- DISP 1.3.3: A respondent must put in place appropriate management controls and take reasonable steps to ensure that in handling complaints it identifies
- DISP 1.3.6: Where a firm identifies (from its complaints or otherwise) recurring or systemic problems in its provision of, or failure to provide, a fina

Why (guess, written by hand after reading the gold text): near miss (rank 7) and wording gap: "look into properly" against "investigate competently, diligently and impartially"; generic "firm must take reasonable steps" provisions win on shared words.

### a27 (paraphrase, gold_mode any)

Question: If an investment firm sorts out a MiFID complaint within three days, does it still have to follow the full time limit rules?

Gold: DISP 1.1A.23. Hybrid provision rank of each gold: DISP 1.1A.23: 7. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- DISP 1.1A.26: The explanation given by MiFID investment firms to clients or potential clients in accordance with DISP 1.1A.25R must also: (1) refer to the
- DISP 1.1A.36: Complaints time barring If a MiFID investment firm receives a MiFID complaint which is outside the time limits for referral to the Financial
- DISP 1.1A.28: Complaints time limits On receipt of a MiFID complaint, a MiFID investment firm must: (1) send the complainant a prompt written acknowledgem
- DISP 1.1A.34: DISP 2.8.1R sets out the circumstances in which the Ombudsman can consider a complaint, including where eight weeks have elapsed since its r
- DISP 1.1A.31: The explanation given by MiFID investment firms to clients or potential clients in accordance with DISP 1.1A.30R must also: (1) enclose a co

Why (guess, written by hand after reading the gold text): near miss (rank 7), MiFID crowding: five sibling DISP 1.1A provisions share "MiFID complaint" and "time limits"; the question's "three days" is "third business day" in the rule.

### a37 (multi, gold_mode all)

Question: When must a firm publish a summary of its complaints data, and by what date?

Gold: DISP 1.10A.1, DISP 1.10A.3. Hybrid provision rank of each gold: DISP 1.10A.1: 9, DISP 1.10A.3: 2. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- DISP 1.11.6E: Mode and content of publication The Society may choose how it publishes the complaints data summary. However, the complaints data summary sh
- DISP 1.10A.3: Time limits for publication (1) Where the firm's relevant reporting period (as defined in DISP 1.10.4 R or DISP 1.10.4A R as the case may be
- DISP 1.10A.7: Mode and content of publication Firms may choose how they publish the complaints data summary or total number of complaints (as appropriate)
- DISP 1.11.6A: Obligation to publish summary of complaints data Where, in accordance with DISP 1.11.6 R, the Society submits a report to the FCA reporting 
- DISP 1.10A.11: For firms reporting 500 or more complaints under DISP 1.10.1R(1) or 1000 or more complaints under DISP 1.10.1R(2) in the relevant reporting 

Why (guess, written by hand after reading the gold text): multi-provision: the dates rule DISP 1.10A.3 is rank 2, but the obligation rule DISP 1.10A.1 is rank 9, behind the Lloyd's (DISP 1.11) mirror provisions; DISP 1.10A.1 is also a split provision whose heading is truncated ("or total number of").

### a40 (multi, gold_mode all)

Question: What happens if a firm breaches a Principle: can the FCA discipline it, and can a customer sue under section 138D?

Gold: PRIN 1.1.7, PRIN 3.4.4. Hybrid provision rank of each gold: PRIN 1.1.7: 1, PRIN 3.4.4: 6. At k=5: keyword hit, dense miss.

Retrieved instead (hybrid top 5):

- PRIN 1.1.7: Consequences of breaching the Principles Breaching a Principle makes a firm or other person to whom the Principles apply liable to disciplin
- PRIN 2A.9.16: Obligation to notify the FCA Firms are reminded of their obligations under Principle 11 to inform the FCA of anything relating to the firm o
- PRIN 1.1.5: Taking group activities into account Principles 3 (Management and control), 4 (Financial prudence) and (in so far as it relates to disclosin
- PRIN 1.1.6: Standards in markets outside the United Kingdom As set out in PRIN 3.3 (Where?), Principles 1 (Integrity), 2 (Skill, care and diligence) and
- DISP 1.1.12: (1) A firm, payment service provider, electronic money issuer, designated credit reference agency or designated finance platform falling wit

Why (guess, written by hand after reading the gold text): multi-provision near miss: PRIN 1.1.7 is rank 1, PRIN 3.4.4 (section 138D) is rank 6; dense misses it entirely, keyword alone gets both, and RRF averages the two down to rank 6.

