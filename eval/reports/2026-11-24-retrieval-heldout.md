# Retrieval evaluation, heldout split (untuned baseline)

```json
{
  "timestamp": "2026-11-24T19:19:34+00:00",
  "corpus_sha256": "24649b93ffefcd784d388f67ade0b83c8ad4fd1e4847c7799e80039f327b4c2d",
  "questions_sha256": "4c5aa45ba91af22486e0f759211280da91b3e9280b585549c7335c125057c68d",
  "split": "heldout (answerable only)",
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
| keyword | 16 | 0.688 (11/16) [0.44-0.86] | 0.490 |
| dense | 16 | 0.250 (4/16) [0.10-0.49] | 0.285 |
| hybrid | 16 | 0.562 (9/16) [0.33-0.77] | 0.388 |

## By question type

| Type | Retriever | n | recall@5 [95% Wilson] | MRR@10 |
|---|---|---|---|---|
| exact | keyword | 5 | 1.000 (5/5) [0.57-1.00] | 0.867 |
| exact | dense | 5 | 0.600 (3/5) [0.23-0.88] | 0.622 |
| exact | hybrid | 5 | 0.800 (4/5) [0.38-0.96] | 0.670 |
| paraphrase | keyword | 6 | 0.667 (4/6) [0.30-0.90] | 0.444 |
| paraphrase | dense | 6 | 0.167 (1/6) [0.03-0.56] | 0.190 |
| paraphrase | hybrid | 6 | 0.500 (3/6) [0.19-0.81] | 0.292 |
| multi | keyword | 5 | 0.400 (2/5) [0.12-0.77] | 0.167 |
| multi | dense | 5 | 0.000 (0/5) [0.00-0.43] | 0.062 |
| multi | hybrid | 5 | 0.400 (2/5) [0.12-0.77] | 0.222 |

## Failures (hybrid misses at k=5)

### a05 (exact, gold_mode any)

Question: Which Consumer Duty cross-cutting obligation deals with foreseeable harm to retail customers?

Gold: PRIN 2A.2.8. Hybrid provision rank of each gold: PRIN 2A.2.8: 10. At k=5: keyword hit, dense miss.

Retrieved instead (hybrid top 5):

- PRIN 2A.2.27: The cross-cutting obligations define how firms should act to deliver good outcomes for retail customers. Interaction between the cross-cutti
- PRIN 2A.1.10: (1) The cross-cutting obligations at PRIN 2A.2 set out the overarching conduct which firms must demonstrate when they act to deliver good ou
- PRIN 2A.2.25: Each of the cross-cutting obligations in this section requires firms to understand and take account of cognitive and behavioural biases and 
- PRIN 2A.9.1: General This section sets out the general obligation on firms to monitor under the Consumer Duty the outcomes that retail customers are expe
- PRIN 2A.9.2: The purpose of the monitoring obligation is to enable firms to identify whether there are any risks that they are not meeting the requiremen

Why (guess): TODO

### a13 (paraphrase, gold_mode any)

Question: How long does a firm have to resolve a complaint?

Gold: DISP 1.6.2, DISP 1.6.7. Hybrid provision rank of each gold: DISP 1.6.2: 38, DISP 1.6.7: 19. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- DISP 1.11.4: Referral to the Financial Ombudsman Service A complaint by a policyholder against a member of the Society may not be referred to the Financi
- DISP 1.2.3: Content of summary details The summary details concerning internal complaints handling procedures should cover at least: (1) how the respond
- DISP 1.4.3: The respondent should aim to resolve complaints at the earliest possible opportunity, minimising the number of unresolved complaints which n
- DISP 1.10.3: DISP 1.10.3 (part 1) For the purposes of DISP 1.10.2R, DISP 1.10.2-AR, DISP 1.10.2BR and DISP 1.10.2CR, when completing the return, the firm
- DISP 1.11.18: An individual member or former member who was an individual member should not have access to the schemes referred to in DISP 1.11.13 R unles

Why (guess): TODO

### a20 (paraphrase, gold_mode any)

Question: Is a firm still allowed to make a profit under the Consumer Duty?

Gold: PRIN 2A.2.4. Hybrid provision rank of each gold: PRIN 2A.2.4: 28. At k=5: keyword hit, dense miss.

Retrieved instead (hybrid top 5):

- PRIN 3.2.10: Interaction between the Consumer Duty and Principles 6 and 7 Principles 6 and 7 do not apply to a firm’s activities to the extent that the C
- PRIN 3.1.13: The Consumer Duty applies to: (1) a TP firm; and (2) a Gibraltar-based firm.
- PRIN 3.2.6: PRIN 3.2.6 (part 1) The Consumer Duty: additional application provisions (1) The Consumer Duty applies to a firm’s retail market business, i
- PRIN 2A.1.13: Guidance on responsibilities of firms in a product’s distribution chain (1) The Consumer Duty imposes obligations on firms towards retail cu
- PRIN 2A.1.17: PRIN 2A.1.17 (part 1) (1) In general terms, the Consumer Duty imposes a higher and more exacting standard of conduct in relation to a firm’s

Why (guess): TODO

### a24 (paraphrase, gold_mode any)

Question: Does a firm have to tell customers how its complaints process works?

Gold: DISP 1.2.1. Hybrid provision rank of each gold: DISP 1.2.1: not in top fetch. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- DISP 1.3.6: Where a firm identifies (from its complaints or otherwise) recurring or systemic problems in its provision of, or failure to provide, a fina
- PRIN 2A.2.5: If a firm identifies through complaints, its internal monitoring or from any other source, that retail customers have suffered foreseeable h
- DISP 1.1A.13: The complaints management policy must provide clear, accurate and up-to-date information about the complaints-handling process. This policy 
- DISP 1.3.3B: DISP 1.3.3B (part 1) The processes that a firm or CBTL firm should have in place in order to comply with DISP 1.3.3 R may include, taking in
- DISP 1.2.3: Content of summary details The summary details concerning internal complaints handling procedures should cover at least: (1) how the respond

Why (guess): TODO

### a29 (multi, gold_mode all)

Question: How do the deadlines for answering a payment services complaint differ from those for other complaints?

Gold: DISP 1.6.2, DISP 1.6.2A. Hybrid provision rank of each gold: DISP 1.6.2: 9, DISP 1.6.2A: 1. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- DISP 1.6.2A: EMD and PSD Complaints Where a complaint is an EMD complaint or a PSD complaint, the respondent must: (1) send a final response to the compl
- DISP 1.1.3A: The complaints reporting directions apply to a firm that provides payment services or issues electronic money in respect of: (1) complaints 
- DISP 1.1.10AB: The complaints reporting directions apply to a payment service provider that is not a firm in respect of complaints from payment service use
- DISP 1.9.1: A firm, a payment service provider or an e-money issuer, must keep a record of each complaint received and the measures taken for its resolu
- DISP 1.10B.2: (1) In contrast to the other provisions in DISP 1 which generally apply only to complaints from eligible complainants, the complaints report

Why (guess): TODO

### a30 (multi, gold_mode all)

Question: If a firm resolves a complaint within three business days, which rules does it skip and what must it send instead?

Gold: DISP 1.5.1, DISP 1.5.4. Hybrid provision rank of each gold: DISP 1.5.1: 2, DISP 1.5.4: 17. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- DISP 1.6.2A: EMD and PSD Complaints Where a complaint is an EMD complaint or a PSD complaint, the respondent must: (1) send a final response to the compl
- DISP 1.5.1: The following rules do not apply to a complaint that is resolved by a respondent by close of business on the third business day following th
- DISP 1.6.1: DISP 1.6.1 (part 1) Keeping the complainant informed On receipt of a complaint, a respondent must: (1) send the complainant a prompt written
- DISP 1.1A.28: Complaints time limits On receipt of a MiFID complaint, a MiFID investment firm must: (1) send the complainant a prompt written acknowledgem
- DISP 1.9.1: A firm, a payment service provider or an e-money issuer, must keep a record of each complaint received and the measures taken for its resolu

Why (guess): TODO

### a39 (multi, gold_mode all)

Question: What complaints procedures must a firm have, and how should it deal with recurring problems?

Gold: DISP 1.3.1, DISP 1.3.3. Hybrid provision rank of each gold: DISP 1.3.1: 12, DISP 1.3.3: 2. At k=5: keyword miss, dense miss.

Retrieved instead (hybrid top 5):

- DISP 1.3.6: Where a firm identifies (from its complaints or otherwise) recurring or systemic problems in its provision of, or failure to provide, a fina
- DISP 1.3.3: A respondent must put in place appropriate management controls and take reasonable steps to ensure that in handling complaints it identifies
- DISP 1.1.1: Purpose This chapter contains rules and guidance on how respondents should deal promptly and fairly with complaints in respect of business: 
- DISP 1.2.3: Content of summary details The summary details concerning internal complaints handling procedures should cover at least: (1) how the respond
- PRIN 2A.2.5: If a firm identifies through complaints, its internal monitoring or from any other source, that retail customers have suffered foreseeable h

Why (guess): TODO

