# Day 3: Legal Knowledge Graph Extraction & Entity Resolution Report
**Client:** Khan & Associates  
**Benchmark Scope:** 20 Supreme Court of Pakistan Judgments  

## 1. Aggregate Extraction Performance

| Extraction Target | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: |
| **Entity Extraction (Nodes)** | **69.23%** | **95.0%** | **80.09%** |
| **Relationship Extraction (Edges)** | **63.07%** | **94.41%** | **75.62%** |
| **Combined Overall Benchmark** | — | — | **77.86%** |

## 2. Per-Judgment Extraction Metrics (Sample of 20)

| Judgment Filename | Pred Ent | GT Ent | Ent Precision | Ent Recall | Pred Rel | GT Rel | Rel Precision | Rel Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `JUDG_Offence of Qazf (Enforcement of Hadood) Ord. 1979.json` | 11 | 6 | 54.55% | 100.0% | 10 | 6 | 60.0% | 100.0% |
| `JUDG_c.a._1080_2011.json` | 5 | 5 | 100.0% | 100.0% | 4 | 4 | 100.0% | 100.0% |
| `JUDG_c.a._138_l_2010.json` | 11 | 10 | 90.91% | 100.0% | 10 | 9 | 90.0% | 100.0% |
| `JUDG_c.a._419_2011.json` | 24 | 23 | 95.83% | 100.0% | 23 | 22 | 95.65% | 100.0% |
| `JUDG_c.a._455_2012.json` | 10 | 8 | 80.0% | 100.0% | 10 | 7 | 70.0% | 100.0% |
| `JUDG_c.a._470_2022.json` | 8 | 8 | 100.0% | 100.0% | 7 | 7 | 100.0% | 100.0% |
| `JUDG_c.a._936_2012_18092024.json` | 11 | 11 | 100.0% | 100.0% | 10 | 10 | 100.0% | 100.0% |
| `JUDG_c.m.a._12587_2021.json` | 8 | 7 | 87.5% | 100.0% | 7 | 6 | 85.71% | 100.0% |
| `JUDG_c.m.a._649_l_2021.json` | 11 | 9 | 81.82% | 100.0% | 10 | 8 | 80.0% | 100.0% |
| `JUDG_c.p._101_2020.json` | 9 | 9 | 100.0% | 100.0% | 8 | 8 | 100.0% | 100.0% |

*(Full 20-judgment table available in `outputs/day3_extraction_eval.csv`)*
