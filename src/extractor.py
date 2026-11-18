"""
Legal Structure Extraction Module
Task 3: AI Legal Assistant (Khan & Associates)
Converts unstructured legal texts into domain-accurate structured JSON:
- Statutes: Act Title, Act No./Year, Preamble, Sections, Subsections, Provisos, Penalties
- Judgments: Court, Bench, Case No., Year, Parties, Citations, Legal Issues, Holding, Disposition
- Contracts: Title, Parties, Effective Date, Governing Law, Categorized Clauses
"""

import os
import re
import json
from typing import Dict, List, Any, Optional
import pymupdf


class LegalStructureExtractor:
    """Extracts domain-specific structured metadata and hierarchical trees from legal documents."""

    def __init__(self, parser=None):
        self.parser = parser

    # =========================================================================
    # 1. STATUTES EXTRACTION (Act -> Sections)
    # =========================================================================
    def extract_statute(self, pdf_path: str, doc_id: str = "") -> Dict[str, Any]:
        """Extracts Act title, preamble, and individual section structures from a Pakistani statute."""
        doc = pymupdf.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += (page.get_text() or "") + "\n"
        doc.close()

        filename = os.path.basename(pdf_path)
        base_name = os.path.splitext(filename)[0]

        # Extract Act Title
        act_title_match = re.search(r"((?:THE\s+)?(?:ANTI-MONEY\s+LAUNDERING|ANTI-TERRORISM|CODE\s+OF\s+CIVIL\s+PROCEDURE|CONTRACT|CODE\s+OF\s+CRIMINAL\s+PROCEDURE|PAKISTAN\s+PENAL\s+CODE|QANUN-E-SHAHADAT|SPECIFIC\s+RELIEF|MUSLIM\s+FAMILY\s+LAWS|CONSTITUTION\s+OF\s+THE\s+ISLAMIC\s+REPUBLIC\s+OF\s+PAKISTAN)[^,\n\r]*?(?:ACT|ORDER|ORDINANCE)?,?\s*(?:18\d\d|19\d\d|20\d\d)?)", full_text, re.IGNORECASE)
        if act_title_match:
            act_title = act_title_match.group(1).strip()
        else:
            # Fallback title from filename
            act_title = base_name.replace("-", " ").replace("_", " ").title()

        # Extract Act Number & Year
        act_num_match = re.search(r"(ACT\s+NO\.\s+[IVXLCDM\d]+\s+OF\s+\d{4}|ORDINANCE\s+NO\.\s+[IVXLCDM\d]+\s+OF\s+\d{4}|P\.O\.\s+NO\.\s+\d+\s+OF\s+\d{4})", full_text, re.IGNORECASE)
        act_number = act_num_match.group(1).strip() if act_num_match else "Act of Parliament"

        year_match = re.search(r"\b(18\d\d|19\d\d|20\d\d)\b", act_title + " " + act_number)
        act_year = int(year_match.group(1)) if year_match else 1900

        # Extract Preamble
        preamble_match = re.search(r"(WHEREAS\s+it\s+is\s+expedient\s+to[\s\S]*?(?:It\s+is\s+hereby\s+enacted\s+as\s+follows|CHAPTER|PART\s+I|1\.\s+Short\s+title))", full_text, re.IGNORECASE)
        preamble = preamble_match.group(1).strip() if preamble_match else "Preamble not explicitly stated."

        # Extract Sections
        # Patterns for section headers in Pakistani laws:
        # e.g., "1. Short title, extent...", "302. Punishment of qatl-i-amd.-", "Section 10."
        section_pattern = re.compile(
            r"(?:\n|^)(?:(?:SECTION\s+)?(\d+[A-Za-z]?)\.?\s+([A-Z][^\.\n\r]{2,80}?)(?:\.|\s*[-—–]))\s*\n?([\s\S]*?)(?=(?:\n(?:SECTION\s+)?\d+[A-Za-z]?\.?\s+[A-Z][^\.\n\r]{2,80}?(?:\.|\s*[-—–]))|\Z)",
            re.MULTILINE
        )

        sections = []
        matches = list(section_pattern.finditer(full_text))

        # If regex finds matches in the body
        for m in matches:
            sec_num = m.group(1).strip()
            sec_title = m.group(2).strip().replace("\n", " ")
            sec_body = m.group(3).strip()

            if len(sec_body) < 10 or len(sec_title) < 3:
                continue

            # Subsections e.g. (1), (2), (a), (b)
            subsections = re.findall(r"\(([0-9]+|[a-z])\)\s+([^\(\n\r]+)", sec_body)
            subs_list = [f"({s[0]}) {s[1].strip()}" for s in subsections]

            # Provisos
            provisos = re.findall(r"(Provided\s+(?:that|further\s+that)[\s\S]*?(?=\.|\n\n|\Z))", sec_body, re.IGNORECASE)
            provisos_list = [p.strip() for p in provisos]

            # Penalties
            penalty_match = re.search(r"(shall\s+be\s+punished[\s\S]*?(?:\.|\n|\Z))", sec_body, re.IGNORECASE)
            penalty_text = penalty_match.group(1).strip() if penalty_match else None

            sections.append({
                "section_number": sec_num,
                "section_title": sec_title,
                "section_text": sec_body[:1500], # Clean bounded snippet
                "full_text_length": len(sec_body),
                "subsections": subs_list[:5],
                "provisos": provisos_list[:3],
                "penalty": penalty_text
            })

        act_slug = re.sub(r'[^A-Za-z0-9]+', '_', base_name).strip('_').upper()[:16]
        matter_id = f"KA/STAT/PAK/{act_year}/{act_slug}"

        return {
            "doc_id": doc_id or f"STAT_{base_name}",
            "matter_id": matter_id,
            "filename": filename,
            "document_type": "statute",
            "jurisdiction": "Islamic Republic of Pakistan",
            "act_title": act_title,
            "act_number": act_number,
            "year": act_year,
            "preamble": preamble[:800],
            "total_sections_extracted": len(sections),
            "sections": sections
        }

    # =========================================================================
    # 2. JUDGMENTS EXTRACTION (Court, Parties, Citations, Holding)
    # =========================================================================
    def extract_judgment(self, pdf_path: str, doc_id: str = "", author_justice: str = "") -> Dict[str, Any]:
        """Extracts court, bench, case number, parties, citations, issues, holding, and disposition from a judgment."""
        doc = pymupdf.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += (page.get_text() or "") + "\n"
        doc.close()

        filename = os.path.basename(pdf_path)
        base_name = os.path.splitext(filename)[0]

        # 1. Court Identification
        court = "Supreme Court of Pakistan"
        if "HIGH COURT" in full_text[:1000]:
            court_match = re.search(r"(LAHORE|SINDH|PESHAWAR|ISLAMABAD|BALOCHISTAN)\s+HIGH\s+COURT", full_text[:1000], re.IGNORECASE)
            if court_match:
                court = f"{court_match.group(1).title()} High Court"

        # 2. Bench / Judges
        bench = []
        bench_match = re.search(r"(?:PRESENT|Present|Bench):\s*\n([\s\S]*?)(?=(?:CIVIL|CRIMINAL|CONSTITUTION|C\.A\.|Crl\.A|Date\s+of\s+Hearing|\.\.\.|\n\n\n))", full_text[:1500])
        if bench_match:
            raw_bench = bench_match.group(1).strip().split("\n")
            for line in raw_bench:
                line_clean = line.strip()
                if ("Justice" in line_clean or "CJ" in line_clean) and len(line_clean) < 80:
                    bench.append(line_clean)

        if not bench and author_justice:
            bench.append(author_justice)
        elif not bench:
            bench.append("Bench details in judgment record")

        # 3. Case Number & Year
        case_no_match = re.search(r"((?:CIVIL|CRIMINAL|CONSTITUTION|C\.M\.A\.|C\.R\.P\.|S\.M\.C\.)\s*(?:APPEAL|PETITION|REVIEW\s+PETITION|APPLICATION)?\s*NO\.?\s*[\d\w\-\/]+(?:\s*OF\s*\d{4})?)", full_text[:1500], re.IGNORECASE)
        case_number = case_no_match.group(1).strip() if case_no_match else base_name.upper().replace("_", " ")

        year_match = re.search(r"\b(19\d\d|20\d\d)\b", case_number + " " + filename)
        year = int(year_match.group(1)) if year_match else 2024

        # 4. Parties (Petitioner / Appellant vs Respondent)
        appellant = "Appellant / Petitioner"
        respondent = "Respondent / The State"

        parties_match = re.search(r"([\s\S]*?)\s*(?:Versus|VERSUS|vs\.?)\s*([\s\S]*?)(?=(?:For\s+the|Date\s+of\s+Hearing|JUDGMENT|ORDER))", full_text[:2000], re.IGNORECASE)
        if parties_match:
            app_raw = parties_match.group(1).strip().split("\n")
            resp_raw = parties_match.group(2).strip().split("\n")
            
            # Filter valid names
            valid_app = [l.strip() for l in app_raw if l.strip() and not re.search(r"(PRESENT|APPEAL|PETITION|IN\s+THE|JURISDICTION|\.\.\.)", l, re.IGNORECASE)]
            valid_resp = [l.strip() for l in resp_raw if l.strip() and not re.search(r"(For\s+the|Date|JUDGMENT|ORDER|\.\.\.)", l, re.IGNORECASE)]
            
            if valid_app:
                appellant = " ".join(valid_app[-2:])
            if valid_resp:
                respondent = " ".join(valid_resp[:2])

        case_title = f"{appellant} v. {respondent}"

        # 5. Citations Referred (e.g. PLD, SCMR, CLC, PCrLJ, MLD, SC)
        citation_pattern = re.compile(r"(\b(?:19|20)\d{2}\s+(?:SCMR|PLD|CLC|PCrLJ|MLD|YLR|SC)\s+\d+\b)", re.IGNORECASE)
        citations_found = list(set(citation_pattern.findall(full_text)))

        # 6. Statutes Cited
        statute_citations = []
        stat_patterns = [
            r"(?:Section|Sec\.)\s+\d+[A-Za-z]?\s+(?:of\s+the\s+)?(?:PPC|CPC|Cr\.?P\.?C\.?|Contract\s+Act|Constitution)",
            r"Article\s+\d+[A-Za-z]?\s+(?:of\s+the\s+Constitution)?",
            r"Order\s+[IVXLCDM\d]+\s+Rule\s+\d+"
        ]
        for sp in stat_patterns:
            matches = re.findall(sp, full_text, re.IGNORECASE)
            statute_citations.extend(matches)
        statute_citations = list(set(statute_citations))[:10]

        # 7. Holding & Disposition
        # Usually found in final 3 paragraphs of the judgment
        tail_text = full_text[-2500:] if len(full_text) > 2500 else full_text
        disposition = "Disposed on merits"
        if re.search(r"(appeal\s+is\s+allowed|petition\s+is\s+allowed|bail\s+is\s+granted|impugned\s+order\s+is\s+set\s+aside)", tail_text, re.IGNORECASE):
            disposition = "Allowed / Relief Granted"
        elif re.search(r"(appeal\s+is\s+dismissed|petition\s+is\s+dismissed|bail\s+is\s+declined|no\s+merit)", tail_text, re.IGNORECASE):
            disposition = "Dismissed"
        elif re.search(r"(remanded\s+back|matter\s+is\s+remanded)", tail_text, re.IGNORECASE):
            disposition = "Remanded to Trial/High Court"

        # Holding snippet
        holding_match = re.search(r"((?:For\s+(?:the\s+)?(?:foregoing|above)?\s*reasons|In\s+view\s+of\s+the\s+above|Accordingly|Consequently)[\s\S]*?\.)", tail_text, re.IGNORECASE)
        holding = holding_match.group(1).strip().replace("\n", " ") if holding_match else tail_text[-500:].replace("\n", " ").strip()

        case_slug = re.sub(r'[^A-Za-z0-9]+', '_', base_name).strip('_').upper()[:16]
        matter_id = f"KA/LIT/SC/{year}/{case_slug}"

        return {
            "doc_id": doc_id or f"JUDG_{base_name}",
            "matter_id": matter_id,
            "filename": filename,
            "document_type": "judgment",
            "court": court,
            "case_number": case_number,
            "case_title": case_title,
            "year": year,
            "bench": bench,
            "parties": {
                "appellant_petitioner": appellant,
                "respondent": respondent
            },
            "citations_referred": citations_found[:15],
            "statutes_cited": statute_citations,
            "disposition": disposition,
            "holding": holding[:800],
            "full_text_length": len(full_text)
        }

    # =========================================================================
    # 3. CONTRACTS EXTRACTION (Clauses)
    # =========================================================================
    def extract_contract(self, pdf_path: str, doc_id: str = "", contract_subtype: str = "general") -> Dict[str, Any]:
        """Extracts contract title, parties, effective date, governing law, and individual clauses into JSON."""
        doc = pymupdf.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += (page.get_text() or "") + "\n"
        doc.close()

        filename = os.path.basename(pdf_path)
        base_name = os.path.splitext(filename)[0]

        # Contract Title
        title_match = re.search(r"((?:EXECUTIVE\s+)?(?:EMPLOYMENT|COMMERCIAL\s+LEASE|SOFTWARE\s+DEVELOPMENT|NON-DISCLOSURE|SUPPLY|JOINT\s+VENTURE|SERVICES|LICENSE|PURCHASE|CONSULTING)\s+(?:AGREEMENT|DEED|CONTRACT))", full_text[:1000], re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip().title()
        else:
            title = base_name.replace("_", " ").replace("-", " ").title()

        # Effective Date
        date_match = re.search(r"(?:dated\s+as\s+of|executed\s+on|entered\s+into\s+on|this)\s+([0-9]{1,2}(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4})", full_text[:1500], re.IGNORECASE)
        effective_date = date_match.group(1).strip() if date_match else "Effective Date as specified"

        # Parties
        parties_match = re.search(r"(?:by\s+and\s+between:?|BETWEEN:?)\s*([\s\S]*?)\s*(?:AND:?|and:?)\s*([\s\S]*?)(?=(?:WHEREAS|Whereas|WITNESSETH|NOW,?\s+THEREFORE))", full_text[:2000], re.IGNORECASE)
        party_1 = "Party One"
        party_2 = "Party Two"
        if parties_match:
            p1 = parties_match.group(1).strip().replace("\n", " ")
            p2 = parties_match.group(2).strip().replace("\n", " ")
            if "AND:" in p2:
                p2 = p2.split("AND:")[-1].strip()
            elif "and:" in p2.lower():
                p2 = re.split(r"\band:\b", p2, flags=re.IGNORECASE)[-1].strip()
            if "(hereinafter" in p1:
                p1 = p1.split("(hereinafter")[0].strip()
            if "(hereinafter" in p2:
                p2 = p2.split("(hereinafter")[0].strip()
            party_1 = p1[:120].strip(" ;,\n")
            party_2 = p2[:120].strip(" ;,\n")

        # Governing Law
        gov_match = re.search(r"(?:governed\s+by|construed\s+in\s+accordance\s+with)[\s\S]*?(?:the\s+laws\s+of\s+([A-Za-z\s,]+?)(?:\.|\n|;))", full_text, re.IGNORECASE)
        governing_law = gov_match.group(0).strip() if gov_match else "Laws of Pakistan (Province of Punjab)" if "synthetic" in contract_subtype else "Specified State Law"

        # Clauses Extraction
        clause_pattern = re.compile(
            r"(?:\n|^)(?:(?:SECTION|ARTICLE|CLAUSE)\s+)?(\d+(?:\.\d+)?)\.?\s+([A-Z][A-Za-z\s,/&-]{2,60}?)(?:\.|\s*[-—–:]|\n)\s*([\s\S]*?)(?=(?:\n(?:(?:SECTION|ARTICLE|CLAUSE)\s+)?\d+(?:\.\d+)?\.?\s+[A-Z][A-Za-z\s,/&-]{2,60}?(?:\.|\s*[-—–:]|\n))|\nSCHEDULE|\Z)",
            re.MULTILINE
        )

        clauses = []
        matches = list(clause_pattern.finditer(full_text))

        for m in matches:
            c_num = m.group(1).strip()
            c_title = m.group(2).strip().replace("\n", " ")
            c_body = m.group(3).strip()

            if len(c_body) < 15 or len(c_title) < 3:
                continue

            # Classify clause taxonomy
            c_lower = (c_title + " " + c_body[:200]).lower()
            if any(k in c_lower for k in ["confidential", "proprietary", "trade secret"]):
                c_type = "Confidentiality"
            elif any(k in c_lower for k in ["terminat", "term of agreement", "expiration"]):
                c_type = "Termination"
            elif any(k in c_lower for k in ["indemnif", "hold harmless", "defend"]):
                c_type = "Indemnification"
            elif any(k in c_lower for k in ["governing law", "jurisdiction", "applicable law"]):
                c_type = "Governing Law"
            elif any(k in c_lower for k in ["payment", "compensation", "salary", "rent", "fee"]):
                c_type = "Payment & Compensation"
            elif any(k in c_lower for k in ["intellectual property", "patent", "copyright", "trademark"]):
                c_type = "Intellectual Property"
            elif any(k in c_lower for k in ["liability", "consequential damages", "cap"]):
                c_type = "Limitation of Liability"
            elif any(k in c_lower for k in ["dispute", "arbitrat", "mediation"]):
                c_type = "Dispute Resolution"
            elif any(k in c_lower for k in ["force majeure", "act of god"]):
                c_type = "Force Majeure"
            else:
                c_type = "General / Operational"

            clauses.append({
                "clause_number": c_num,
                "clause_heading": c_title,
                "clause_type": c_type,
                "text": c_body[:1200]
            })

        cont_slug = re.sub(r'[^A-Za-z0-9]+', '_', base_name).strip('_').upper()[:16]
        city_tag = "LHR" if "lahore" in base_name.lower() else "KHI" if "karachi" in base_name.lower() else "ISB" if "islamabad" in base_name.lower() else "COMM"
        matter_id = f"KA/CORP/{city_tag}/2026/{cont_slug}"

        return {
            "doc_id": doc_id or f"CONT_{base_name}",
            "matter_id": matter_id,
            "filename": filename,
            "document_type": "contract",
            "contract_subtype": contract_subtype,
            "title": title,
            "parties": {
                "party_one": party_1,
                "party_two": party_2
            },
            "effective_date": effective_date,
            "governing_law": governing_law[:150],
            "total_clauses_extracted": len(clauses),
            "clauses": clauses
        }

    # =========================================================================
    # 4. SCANNED URDU DOCUMENTS EXTRACTION
    # =========================================================================
    def extract_scanned_urdu(self, pdf_path: str, doc_id: str = "") -> Dict[str, Any]:
        """Extracts structured record for scanned Urdu legal documents."""
        filename = os.path.basename(pdf_path)
        base_name = os.path.splitext(filename)[0]

        type_map = {
            "kiraya_nama": ("معاہدہ کرایہ داری (کرایہ نامہ)", "Tenancy / Rent Agreement"),
            "fir_report": ("ابتدائی اطلاعی رپورٹ (ایف آئی آر)", "Police FIR Report"),
            "qanooni_notice": ("قانونی نوٹس", "Legal Recovery Notice"),
            "darkhwast_zamanat": ("درخواست ضمانت بعد از گرفتاری", "Post-Arrest Bail Petition"),
            "bayan_e_halfi": ("بیان حلفی", "Sworn Affidavit"),
            "iqrarnama_farokht": ("اقرار نامہ فروخت", "Agreement to Sell Land"),
            "mulazmat_muahida": ("ملازمت کا معاہدہ", "Employment Contract"),
            "mukhtar_nama_aam": ("مختار نامہ عام", "General Power of Attorney"),
            "dawa_naan_nafaqa": ("دعویٰ خرچہ نان و نفقہ", "Maintenance / Family Suit"),
            "hukamnama_adalat": ("حکم نامہ عدالت عالیہ", "High Court Judicial Order")
        }

        matched_urdu_title = "دستاویز قانونی"
        matched_en_title = "Urdu Legal Document"
        for key, (u_t, e_t) in type_map.items():
            if key in filename.lower():
                matched_urdu_title = u_t
                matched_en_title = e_t
                break

        # Extract city from filename if present
        cities = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Multan", "Faisalabad", "Peshawar", "Quetta", "Sialkot"]
        city = "Pakistan"
        for c in cities:
            if c.lower() in filename.lower():
                city = c
                break

        urdu_slug = re.sub(r'[^A-Za-z0-9]+', '_', base_name).strip('_').upper()[:16]
        city_code = city[:3].upper() if city != "Pakistan" else "GEN"
        matter_id = f"KA/LIT/URDU/{city_code}/2026/{urdu_slug}"

        return {
            "doc_id": doc_id or f"URDU_{base_name}",
            "matter_id": matter_id,
            "filename": filename,
            "document_type": "scanned_urdu",
            "title_urdu": matched_urdu_title,
            "category_en": matched_en_title,
            "jurisdiction_city": city,
            "language": "Urdu",
            "is_scanned": True,
            "processing_path": "Requires OCR ingestion"
        }


if __name__ == "__main__":
    extractor = LegalStructureExtractor()
    out_dir = "outputs/structured"

    print("\n--- 1. Testing Statute Extraction ---")
    stat_file = "data/data_sources/statutes/contract_act.pdf"
    if os.path.exists(stat_file):
        s_res = extractor.extract_statute(stat_file)
        with open(f"{out_dir}/statutes/{s_res['doc_id']}.json", "w", encoding="utf-8") as f:
            json.dump(s_res, f, indent=2, ensure_ascii=False)
        print(f"Statute: {s_res['act_title']} | Sections extracted: {s_res['total_sections_extracted']}")

    print("\n--- 2. Testing Judgment Extraction ---")
    judg_file = "data/data_sources/judgments_sample/Justice Aqeel Ahmed Abbasi/c.a._470_2022.pdf"
    if os.path.exists(judg_file):
        j_res = extractor.extract_judgment(judg_file, author_justice="Justice Aqeel Ahmed Abbasi")
        with open(f"{out_dir}/judgments/{j_res['doc_id']}.json", "w", encoding="utf-8") as f:
            json.dump(j_res, f, indent=2, ensure_ascii=False)
        print(f"Judgment: {j_res['case_number']} | Title: {j_res['case_title']} | Disposition: {j_res['disposition']}")

    print("\n--- 3. Testing Contract Extraction ---")
    cont_file = "data/data_sources/contracts/synthetic/01_employment_agreement_lahore.pdf"
    if os.path.exists(cont_file):
        c_res = extractor.extract_contract(cont_file, contract_subtype="synthetic")
        with open(f"{out_dir}/contracts/{c_res['doc_id']}.json", "w", encoding="utf-8") as f:
            json.dump(c_res, f, indent=2, ensure_ascii=False)
        print(f"Contract: {c_res['title']} | Clauses extracted: {c_res['total_clauses_extracted']}")
