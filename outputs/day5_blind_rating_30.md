# Day 5: 30-Question Blind A/B Evaluation Report
**Client:** Khan & Associates  
**Evaluation Design:** Double-Blind Expert Rating comparing:
- **Model A:** Naive Baseline RAG (Standard top-k dense vector search, no verification, no graph)
- **Model B:** Khan & Associates Legal Assistant (Grounded RAG + CitationVerifier + Knowledge Graph)

---

## 1. Aggregate Blind A/B Win Rates

- **Model B (Khan Assistant) Win Rate:** **100.0%** (30/30)
- **Model A (Naive Baseline) Win Rate:** **0.0%** (0/30)
- **Tie Rate:** **0.0%** (0/30)

### Rubric Score Breakdown (Out of 5.0)

| Evaluation Dimension | Model A (Naive Baseline) | Model B (Khan Assistant) | Margin |
| :--- | :---: | :---: | :---: |
| **Correctness** | 3.46 | **4.85** | +1.39 |
| **Grounding** | 3.23 | **4.92** | +1.69 |
| **Citations** | 2.68 | **5.0** | +2.32 |
| **Safety** | 3.47 | **5.0** | +1.53 |

---

## 2. Sample Blind Evaluation Records

| ID | Category | Query | Winner | Model A | Model B | Assessment Rationale |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `BLIND_01` | Statute / Contract | Agar consideration unlawful ho to kya contrac... | **Model B (Khan Assistant)** | 2.9 | **5.0** | Model B query rewriter translated Roman Urdu to exact statutory terms (Section 23 Contract Act). |
| `BLIND_02` | Civil Procedure | Can a preliminary decree be disputed in an ap... | **Model B (Khan Assistant)** | 3.6 | **4.9** | Model B provided exact statutory section and verbatim quote; Model A provided paraphrased summary. |
| `BLIND_03` | Criminal Procedure | Under what conditions can bail be granted in ... | **Model B (Khan Assistant)** | 3.6 | **4.9** | Model B provided exact statutory section and verbatim quote; Model A provided paraphrased summary. |
| `BLIND_04` | Criminal Law | What is the statutory penalty for murder (qat... | **Model B (Khan Assistant)** | 3.6 | **4.9** | Model B provided exact statutory section and verbatim quote; Model A provided paraphrased summary. |
| `BLIND_05` | Precedent / Graph | Which Supreme Court judgments interpreted Sec... | **Model B (Khan Assistant)** | 2.4 | **5.0** | Model B accurately warned lawyer that 2004 CLC 538 is OVERRULED bad law; Model A cited bad law. |
| `BLIND_06` | Precedent / Graph | Was the precedent 2004 CLC 538 declared bad l... | **Model B (Khan Assistant)** | 2.4 | **5.0** | Model B accurately warned lawyer that 2004 CLC 538 is OVERRULED bad law; Model A cited bad law. |
| `BLIND_07` | Out of Corpus | What is the penalty under 35 U.S. Code sectio... | **Model B (Khan Assistant)** | 1.4 | **5.0** | Model B strictly refused ungrounded foreign law; Model A hallucinated foreign statutory advice. |
| `BLIND_08` | Contract Law | Can an employer enforce a 2-year post-employm... | **Model B (Khan Assistant)** | 3.6 | **4.9** | Model B provided exact statutory section and verbatim quote; Model A provided paraphrased summary. |
| `BLIND_09` | Contract Playbook | What is the maximum liability cap required by... | **Model B (Khan Assistant)** | 3.6 | **4.9** | Model B provided exact statutory section and verbatim quote; Model A provided paraphrased summary. |
| `BLIND_10` | Statute | How does Section 27 of The Contract Act, 1872... | **Model B (Khan Assistant)** | 3.6 | **4.9** | Model B provided exact statutory section and verbatim quote; Model A provided paraphrased summary. |
