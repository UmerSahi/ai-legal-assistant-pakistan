# Khan & Associates — AI Legal Assistant User Guide
### Associate & Paralegal Practical Handbook

Welcome to the **Khan & Associates AI Legal Assistant**. This software is specifically engineered for Pakistani civil, commercial, criminal, and constitutional practice. It operates exclusively on verified statutes, authoritative Supreme Court and High Court law reports, and firm-approved commercial contract playbooks.

---

## 1. Accessing the Platform

1. Open your web browser (Chrome, Edge, or Firefox) and navigate to:
   `http://localhost:8000` (or firm internal IP).
2. Confirm your operational user identity and assigned matter ID at the top right header.
   - Example: `Bilal Ahmed (Associate) | Matter: MAT-2024-KHI-001`.

---

## 2. Conducting Statutory & Judicial Research

Navigate to the **⚖️ Legal Research & Citations** tab:

1. **Bilingual Search Support:**
   - Inquiries may be entered in formal English (e.g., *"What constitutes unlawful consideration under the Contract Act?"*) or colloquial Roman Urdu (e.g., *"Agar consideration unlawful ho to kya contract void hai?"*).
2. **Reviewing Grounded Answers:**
   - **Conclusion:** Direct statutory holding.
   - **Statutory Citations:** Specific Act name and section numbers (e.g., `The Contract Act, 1872 (Section 23)`).
   - **Quoted Source:** Verbatim text directly from the statutory gazette or law report.
   - **Citation Verification:** Confirms `Fabricated Citations: 0`.
3. **Out-of-Corpus Questions:**
   - If an inquiry involves foreign law (e.g., California civil code, English commercial acts) or facts not in the firm repository, the assistant will explicitly respond: **"No sufficient source found"**. Never force an ungrounded answer.

---

## 3. Auditing Contracts Against the Firm Playbook

Navigate to the **📋 Contract Playbook Review** tab:

1. **Inputting Agreement:**
   - Paste the counterparty's draft agreement into the text area.
2. **Initiating Audit:**
   - Click **Run Playbook Review**.
3. **Interpreting Badges:**
   - `[PASS]` ✅: Terms meet firm standard tolerances.
   - `[WARN]` ⚠️: Ambiguous or sub-optimal terms. Review suggested replacement wording.
   - `[FAIL]` ❌: Dangerous deviations (e.g., unlimited indemnity, foreign governing law, unilateral termination).
4. **Missing Mandatory Clauses:**
   - The system checks for compliance with **PECA 2016** (Data Protection), Anti-Bribery, Severability, and Entire Agreement.
5. **Word (.docx) Report:**
   - Formal reports with tracked redlines are saved to `outputs/sample_contract_review_report.docx`.

---

## 4. Comparing Contract Versions

Navigate to the **🔍 Version Comparison** tab:

1. Paste your firm standard draft into **Version 1** and counterparty markup into **Version 2**.
2. Click **Compare Drafts**.
3. The comparator lists all modified clauses alongside an executive **Legal Impact Analysis** explaining what the practical risk means in plain language.

---

## 5. Generating Legal Drafts

Navigate to the **✍️ Drafting Agent** tab:

1. Select your target document:
   - **Case Brief:** Structured procedural analysis of apex court judgments.
   - **Advocate Demand Notice:** Formal statutory legal notice for material contract breach under Section 73.
   - **Bespoke Clauses:** Standard limitation of liability, indemnity, and dispute resolution clauses tailored for Pakistani courts.
2. Click **Generate Draft**.
3. **Lawyer Review Mandatory:** Every draft carries the header stamp:  
   `DRAFT — for lawyer review`.  
   *Note: Associates must read and sign off on all drafts before dispatch to clients or opposing counsel.*

---

## 6. Multi-Hop Research & Knowledge Graph

Navigate to the **🕸️ Knowledge Graph & GraphRAG** tab:

1. For queries requiring precedent chains or check for bad law (e.g., *"Which cases interpreted Section 23 and were later overruled?"*):
2. Select **Auto Router** and click **Query Knowledge Graph**.
3. The system executes Cypher graph traversals and alerts you with a red banner if any cited case has an active `[:OVERRULES]` relationship.

---

## 7. Security Best Practices

- **Client Matter Segregation:** You can only query matters to which you are assigned. Attempting to query an unassigned matter will return `403 Forbidden`.
- **Automatic PII Redaction:** All CNICs, mobile numbers, and bank account numbers are automatically masked in system logs to protect client confidentiality under PECA 2016.
