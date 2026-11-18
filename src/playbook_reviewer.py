"""
Contract Playbook Risk Reviewer and Word (.docx) Report Generator
Task 2: AI Legal Assistant (Khan & Associates)

Features:
- Audits contract clauses against Khan & Associates' firm commercial playbook
- Assigns clause risk badges: [PASS] / [WARN] / [FAIL]
- Detects missing mandatory clauses (Data Protection, Anti-Corruption, Severability)
- Calculates overall contract risk score (0-100)
- Suggests approved alternative wording for flagged clauses
- Generates a styled Microsoft Word report (.docx) with comments and redlines
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
import json
from typing import Dict, List, Any, Tuple, Optional

try:
    import docx
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class FirmPlaybookReviewer:
    """Evaluates contract clauses against Khan & Associates' commercial playbook."""

    # Mandatory clauses that must exist in any enterprise agreement
    MANDATORY_CLAUSES = [
        ("Data Protection & Cybersecurity", r"\b(data\s+protection|peca|personal\s+data|privacy|gdpr)\b"),
        ("Anti-Bribery & Anti-Money Laundering", r"\b(anti-bribery|anti-corruption|money\s+laundering|aml\s+act|corrupt\s+practices)\b"),
        ("Severability", r"\b(severability|severable|invalidity\s+of\s+provision)\b"),
        ("Entire Agreement", r"\b(entire\s+agreement|merger\s+clause|supersedes\s+prior)\b")
    ]

    @classmethod
    def evaluate_clause(cls, category: str, text: str, heading: str = "") -> Dict[str, Any]:
        """
        Applies firm playbook rules to a single clause.
        Returns: {status: 'PASS' | 'WARN' | 'FAIL', risk_score: int, comments: str, replacement_wording: str}
        """
        c_low = f"{heading} {text}".lower()

        # -------------------------------------------------------------
        # 1. Governing Law
        # -------------------------------------------------------------
        if "governing law" in category.lower() or "governing law" in c_low:
            if "pakistan" in c_low or "punjab" in c_low or "sindh" in c_low or "islamabad" in c_low:
                return {
                    "status": "PASS",
                    "badge": "[PASS]",
                    "penalty": 0,
                    "finding": "Compliant: Governed by the laws of Pakistan with appropriate provincial jurisdiction.",
                    "comments": "Playbook compliant. Ensures local enforceability and cost-effective legal representation.",
                    "suggested_wording": ""
                }
            elif any(f_juris in c_low for f_juris in ["england", "english law", "new york", "delaware", "singapore", "california"]):
                return {
                    "status": "FAIL",
                    "badge": "[FAIL]",
                    "penalty": 35,
                    "finding": "UNACCEPTABLE: Foreign governing law designated without local carve-out.",
                    "comments": "High Risk: Subjecting client to foreign jurisdiction significantly escalates litigation costs and creates foreign currency exposure.",
                    "suggested_wording": (
                        "This Agreement shall be governed by, and construed in accordance with, the laws of the Islamic Republic of Pakistan. "
                        "The courts located in Lahore, Pakistan shall have exclusive jurisdiction to settle any dispute or claim arising out of or in connection with this Agreement."
                    )
                }
            else:
                return {
                    "status": "WARN",
                    "badge": "[WARN]",
                    "penalty": 15,
                    "finding": "Ambiguous Governing Law: Jurisdiction not explicitly defined.",
                    "comments": "Medium Risk: Vague governing law creates jurisdictional conflict of laws.",
                    "suggested_wording": (
                        "This Agreement and any dispute arising out of it shall be governed by and construed in accordance with the laws of the Islamic Republic of Pakistan."
                    )
                }

        # -------------------------------------------------------------
        # 2. Dispute Resolution / Arbitration
        # -------------------------------------------------------------
        if "dispute" in category.lower() or "arbitration" in category.lower() or "arbitration" in c_low:
            if "arbitration act, 1940" in c_low or ("arbitration" in c_low and ("lahore" in c_low or "karachi" in c_low or "pakistan" in c_low)):
                return {
                    "status": "PASS",
                    "badge": "[PASS]",
                    "penalty": 0,
                    "finding": "Compliant: Local arbitration under the Arbitration Act, 1940 seated in Pakistan.",
                    "comments": "Meets playbook standard for private, expeditious dispute settlement.",
                    "suggested_wording": ""
                }
            elif any(f_seat in c_low for f_seat in ["london", "paris", "icc", "siac", "lcia", "geneva"]):
                return {
                    "status": "WARN",
                    "badge": "[WARN]",
                    "penalty": 20,
                    "finding": "Foreign Arbitration Seat: Increases dispute resolution overhead.",
                    "comments": "Medium/High Risk: International arbitration costs may exceed contract value. Requires express reference to Pakistan's 2011 Recognition Act.",
                    "suggested_wording": (
                        "Any dispute, controversy, or claim arising under this Agreement shall be referred to and finally resolved by arbitration in Lahore, Pakistan, "
                        "under the Arbitration Act, 1940 by a sole arbitrator mutually appointed by the Parties."
                    )
                }

        # -------------------------------------------------------------
        # 3. Limitation of Liability
        # -------------------------------------------------------------
        if "liability" in category.lower() or "limitation of liability" in c_low:
            if "unlimited" in c_low or "no limit" in c_low or "shall not be limited" in c_low:
                return {
                    "status": "FAIL",
                    "badge": "[FAIL]",
                    "penalty": 35,
                    "finding": "UNACCEPTABLE: Unlimited liability exposes client to catastrophic financial exposure.",
                    "comments": "Critical Risk: Commercial contracts must include an aggregate liability cap tied to fees paid.",
                    "suggested_wording": (
                        "Except for breaches of confidentiality or gross negligence, the aggregate maximum liability of either Party arising out of or relating to this Agreement "
                        "shall not exceed the total fees actually paid by Client in the twelve (12) months preceding the claim. Neither Party shall be liable for indirect, incidental, or consequential damages."
                    )
                }
            elif "12 months" in c_low or "fees paid" in c_low or "total contract value" in c_low:
                return {
                    "status": "PASS",
                    "badge": "[PASS]",
                    "penalty": 0,
                    "finding": "Compliant: Liability capped at 12-month contract fees with consequential damages exclusion.",
                    "comments": "Standard market-aligned risk allocation.",
                    "suggested_wording": ""
                }
            else:
                return {
                    "status": "WARN",
                    "badge": "[WARN]",
                    "penalty": 15,
                    "finding": "Vague Liability Cap: Financial cap multiplier is undefined.",
                    "comments": "Recommend amending to cap liability explicitly at 12 months fees.",
                    "suggested_wording": (
                        "To the maximum extent permitted by applicable law, the aggregate liability of either party shall be strictly capped at the fees paid hereunder in the prior 12 months."
                    )
                }

        # -------------------------------------------------------------
        # 4. Indemnification
        # -------------------------------------------------------------
        if "indemn" in category.lower() or "indemn" in c_low:
            if "unilateral" in c_low or ("client shall indemnify" in c_low and "consultant shall indemnify" not in c_low and "service provider" not in c_low):
                return {
                    "status": "FAIL",
                    "badge": "[FAIL]",
                    "penalty": 30,
                    "finding": "UNACCEPTABLE: One-sided indemnification obligation imposed exclusively on client.",
                    "comments": "High Risk: Indemnities must be mutual and reciprocal.",
                    "suggested_wording": (
                        "Each Party ('Indemnifying Party') agrees to defend, indemnify, and hold harmless the other Party, its directors, and employees from and against any third-party claims, "
                        "damages, or liabilities arising directly from the Indemnifying Party's gross negligence, wilful misconduct, or material breach of this Agreement."
                    )
                }
            elif "mutual" in c_low or ("gross negligence" in c_low and "third party" in c_low):
                return {
                    "status": "PASS",
                    "badge": "[PASS]",
                    "penalty": 0,
                    "finding": "Compliant: Mutual indemnification with standard gross negligence carve-outs.",
                    "comments": "Balanced and enforceable under Pakistani contract law.",
                    "suggested_wording": ""
                }

        # -------------------------------------------------------------
        # 5. Non-Compete / Restrictive Covenants
        # -------------------------------------------------------------
        if "non-compete" in category.lower() or "non-compete" in c_low or "competing" in c_low or "restraint" in c_low:
            if "after termination" in c_low or "following termination" in c_low or "post-employment" in c_low or "2 years" in c_low or "3 years" in c_low:
                return {
                    "status": "FAIL",
                    "badge": "[FAIL]",
                    "penalty": 35,
                    "finding": "UNACCEPTABLE & VOID: Post-termination non-compete violates Section 27 of The Contract Act, 1872.",
                    "comments": "Critical Legal Issue: Under Section 27 of the Contract Act, 1872, agreements in restraint of trade/profession are void ab initio in Pakistan (see PLD 2021 SC 362).",
                    "suggested_wording": (
                        "During the term of this Agreement only, Employee/Consultant shall devote their professional attention to Company. "
                        "Company acknowledges that post-termination trade restrictions are void under Section 27 of The Contract Act, 1872, and the Parties agree to a reasonable 6-month non-solicitation of active clients instead."
                    )
                }
            else:
                return {
                    "status": "PASS",
                    "badge": "[PASS]",
                    "penalty": 0,
                    "finding": "Compliant: In-term restrictive covenant limited to non-solicitation.",
                    "comments": "Lawful during active term of employment or contract.",
                    "suggested_wording": ""
                }

        # -------------------------------------------------------------
        # 6. Termination
        # -------------------------------------------------------------
        if "termination" in category.lower() or "terminate" in c_low:
            if "immediate" in c_low and "without cause" in c_low:
                return {
                    "status": "WARN",
                    "badge": "[WARN]",
                    "penalty": 20,
                    "finding": "Immediate Termination for Convenience: Threatens commercial continuity.",
                    "comments": "Playbook requires minimum 30 days notice for termination for convenience.",
                    "suggested_wording": (
                        "Either Party may terminate this Agreement without cause upon providing at least thirty (30) days prior written notice to the other Party. "
                        "In the event of material breach, termination shall take effect only if such breach remains uncured following fifteen (15) days written notice."
                    )
                }
            elif "30 days" in c_low or "notice" in c_low:
                return {
                    "status": "PASS",
                    "badge": "[PASS]",
                    "penalty": 0,
                    "finding": "Compliant: Balanced termination rights with customary notice and cure periods.",
                    "comments": "Acceptable under Khan & Associates playbook.",
                    "suggested_wording": ""
                }

        # -------------------------------------------------------------
        # Default Pass
        # -------------------------------------------------------------
        return {
            "status": "PASS",
            "badge": "[PASS]",
            "penalty": 0,
            "finding": "Compliant: Standard commercial provision without notable legal deviations.",
            "comments": "No objection from legal risk standpoint.",
            "suggested_wording": ""
        }

    @classmethod
    def review_contract(cls, contract_json_path: str) -> Dict[str, Any]:
        """Runs full playbook review on a structured contract JSON file."""
        with open(contract_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        contract_title = data.get("title") or data.get("contract_title") or os.path.basename(contract_json_path)
        clauses = data.get("clauses", [])
        total_penalties = 0

        clause_reviews = []
        counts = {"PASS": 0, "WARN": 0, "FAIL": 0}

        all_text = " ".join([c.get("text", "") for c in clauses]).lower()

        # 1. Review existing clauses
        for c in clauses:
            heading = c.get("clause_heading") or c.get("clause_title", "")
            text = c.get("text", "")
            cat = c.get("clause_type") or c.get("category", "General")

            eval_res = cls.evaluate_clause(cat, text, heading)
            status = eval_res["status"]
            counts[status] += 1
            total_penalties += eval_res["penalty"]

            clause_reviews.append({
                "clause_number": c.get("clause_number", "1"),
                "heading": heading,
                "text": text,
                "category": cat,
                "status": status,
                "badge": eval_res["badge"],
                "finding": eval_res["finding"],
                "comments": eval_res["comments"],
                "suggested_wording": eval_res["suggested_wording"]
            })

        # 2. Check for missing mandatory clauses
        missing_clauses = []
        for name, pattern in cls.MANDATORY_CLAUSES:
            if not re.search(pattern, all_text):
                missing_clauses.append(name)
                total_penalties += 10

        # Overall risk calculation
        risk_score = min(100, max(0, total_penalties))
        if risk_score <= 25:
            risk_level = "LOW RISK (Approved with Minor Comments)"
            risk_color = "Green"
        elif risk_score <= 55:
            risk_level = "MEDIUM RISK (Requires Revision Before Execution)"
            risk_color = "Amber"
        else:
            risk_level = "HIGH RISK (Severe Red Flags - Do Not Sign As-Is)"
            risk_color = "Red"

        return {
            "contract_title": contract_title,
            "filename": os.path.basename(contract_json_path),
            "governing_law": data.get("governing_law", "Unspecified"),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "clause_counts": counts,
            "missing_clauses": missing_clauses,
            "clause_reviews": clause_reviews
        }

    @classmethod
    def export_word_report(cls, review_data: Dict[str, Any], output_path: str) -> str:
        """Generates a professional Word document (.docx) with formatted review tables and comments."""
        if not DOCX_AVAILABLE:
            print("[PlaybookReviewer] python-docx not installed, skipping DOCX generation.")
            return ""

        doc = Document()

        # Styles
        styles = doc.styles
        normal_style = styles['Normal']
        normal_style.font.name = 'Calibri'
        normal_style.font.size = Pt(11)

        # Title Header
        title = doc.add_paragraph()
        r = title.add_run("KHAN & ASSOCIATES — ADVOCATES & LEGAL CONSULTANTS\n")
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = RGBColor(18, 48, 86)  # Navy Blue

        sub = title.add_run("COMMERCIAL CONTRACT REVIEW & PLAYBOOK RISK AUDIT")
        sub.font.size = Pt(12)
        sub.font.bold = True
        sub.font.color.rgb = RGBColor(80, 80, 80)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph("—" * 55)

        # Executive Summary Section
        h1 = doc.add_heading("1. Executive Summary & Risk Rating", level=1)
        h1.runs[0].font.color.rgb = RGBColor(18, 48, 86)

        summary_table = doc.add_table(rows=5, cols=2)
        summary_table.style = 'Table Grid'
        summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        meta_rows = [
            ("Target Agreement:", str(review_data.get("contract_title"))),
            ("Governing Law Specified:", str(review_data.get("governing_law"))),
            ("Overall Risk Score:", f"{review_data.get('risk_score')}/100 — {review_data.get('risk_level')}"),
            ("Clause Compliance Breakdown:", f"Pass: {review_data['clause_counts']['PASS']} | Warning: {review_data['clause_counts']['WARN']} | Critical Fail: {review_data['clause_counts']['FAIL']}"),
            ("Missing Mandatory Provisions:", ", ".join(review_data.get("missing_clauses", [])) or "None (All mandatory provisions present)")
        ]

        for i, (label, val) in enumerate(meta_rows):
            cell_lbl = summary_table.rows[i].cells[0]
            cell_val = summary_table.rows[i].cells[1]
            cell_lbl.text = label
            cell_val.text = val
            cell_lbl.paragraphs[0].runs[0].font.bold = True
            cell_lbl.width = Inches(2.5)
            cell_val.width = Inches(4.5)

        doc.add_paragraph("\n")

        # Missing Clauses Warning Box
        if review_data.get("missing_clauses"):
            p_miss = doc.add_paragraph()
            r_miss = p_miss.add_run("WARNING — MISSING MANDATORY PLAYBOOK CLAUSES:\n")
            r_miss.font.bold = True
            r_miss.font.color.rgb = RGBColor(180, 0, 0)
            for mc in review_data["missing_clauses"]:
                p_miss.add_run(f"• {mc}: Playbook requires explicit inclusion to prevent statutory liability under Pakistani regulations.\n")

        # Clause-by-Clause Evaluation Section
        h2 = doc.add_heading("2. Clause-by-Clause Playbook Review & Lawyer Commentary", level=1)
        h2.runs[0].font.color.rgb = RGBColor(18, 48, 86)

        for review in review_data["clause_reviews"]:
            status = review["status"]
            badge = review["badge"]
            heading = review["heading"] or f"Clause {review['clause_number']}"

            p = doc.add_paragraph()
            r_num = p.add_run(f"{badge} Clause {review['clause_number']}: {heading}\n")
            r_num.font.bold = True
            if status == "FAIL":
                r_num.font.color.rgb = RGBColor(180, 0, 0)
            elif status == "WARN":
                r_num.font.color.rgb = RGBColor(180, 120, 0)
            else:
                r_num.font.color.rgb = RGBColor(0, 120, 0)

            # Original text
            p_orig = doc.add_paragraph()
            p_orig.paragraph_format.left_indent = Inches(0.25)
            r_orig_lbl = p_orig.add_run("Original Draft Text:\n")
            r_orig_lbl.font.italic = True
            r_orig_val = p_orig.add_run(f"\"{review['text'][:250]}...\"\n")
            r_orig_val.font.size = Pt(10)
            r_orig_val.font.color.rgb = RGBColor(90, 90, 90)

            # Lawyer Comments
            p_comm = doc.add_paragraph()
            p_comm.paragraph_format.left_indent = Inches(0.25)
            r_comm = p_comm.add_run(f"Firm Legal Assessment: {review['comments']}\n")
            r_comm.font.size = Pt(10)
            r_comm.font.bold = (status != "PASS")

            # Suggested Replacement Wording (if WARN or FAIL)
            if review.get("suggested_wording"):
                p_sug = doc.add_paragraph()
                p_sug.paragraph_format.left_indent = Inches(0.4)
                r_sug_lbl = p_sug.add_run("Recommended Redline Replacement (Khan & Associates Standard):\n")
                r_sug_lbl.font.bold = True
                r_sug_lbl.font.size = Pt(10)
                r_sug_lbl.font.color.rgb = RGBColor(18, 48, 86)
                r_sug_val = p_sug.add_run(f"\"{review['suggested_wording']}\"\n")
                r_sug_val.font.size = Pt(10)
                r_sug_val.font.italic = True

            doc.add_paragraph("—" * 40)

        # Signature Footer
        p_foot = doc.add_paragraph("\n\n")
        r_foot = p_foot.add_run("Prepared by: Khan & Associates AI Legal Assistant Engine\nApproved by: Advocate High Court / Corporate Partner\n")
        r_foot.font.size = Pt(10)
        r_foot.font.italic = True
        r_foot.font.color.rgb = RGBColor(100, 100, 100)

        doc.save(output_path)
        print(f"[PlaybookReviewer] Word report successfully saved to: {output_path}")
        return output_path


if __name__ == "__main__":
    sample_contract = "outputs/structured/contracts/CONT_01_employment_agreement_lahore.json"
    if os.path.exists(sample_contract):
        reviewer = FirmPlaybookReviewer()
        review_data = reviewer.review_contract(sample_contract)
        print(f"\n--- Contract Review: {review_data['contract_title']} ---")
        print(f"Risk Score: {review_data['risk_score']}/100 ({review_data['risk_level']})")
        print(f"Compliance Breakdown: {review_data['clause_counts']}")
        print(f"Missing Clauses: {review_data['missing_clauses']}")

        docx_out = "outputs/sample_contract_review_report.docx"
        reviewer.export_word_report(review_data, docx_out)
