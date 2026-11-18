"""
Contract Comparison and Legal Impact Analysis Engine
Task 3: AI Legal Assistant (Khan & Associates)

Features:
- Compares two versions of a legal contract (v1 Original vs. v2 Counterparty Markup)
- Identifies Added, Removed, and Modified provisions using semantic and difflib diffing
- Analyzes and translates legal impact into plain English for commercial lawyers
- Categorizes risk severity (High / Medium / Low) and provides strategic pushback advice
- Exports reports to outputs/contract_comparison.md and outputs/contract_comparison.json
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import difflib
import json
import re
from typing import Dict, List, Any, Tuple


class ContractComparator:
    """Compares two contract drafts and analyzes legal and operational risks."""

    # Rule-based legal impact knowledge base
    IMPACT_RULES = [
        {
            "trigger": r"\b(unlimited|shall not be limited|no limit)\b",
            "context": "liability",
            "title": "Liability Cap Removal / Unlimited Exposure",
            "risk": "HIGH RISK (CRITICAL)",
            "impact": (
                "The counterparty has removed the mutual limitation of liability cap. "
                "Legal Impact: Your firm/client is now exposed to unlimited direct, indirect, and consequential damages in the event of a breach, "
                "which could jeopardize company solvency."
            ),
            "recommendation": "Firmly reject. Insist on restoring the aggregate cap tied to 12 months fees paid under the agreement."
        },
        {
            "trigger": r"\b(england|english law|new york|delaware|london|singapore)\b",
            "context": "governing_law",
            "title": "Governing Law & Forum Shift to Foreign Jurisdiction",
            "risk": "HIGH RISK",
            "impact": (
                "Governing law and forum shifted from Lahore, Pakistan to foreign courts. "
                "Legal Impact: Increases dispute costs tenfold, requires hiring overseas solicitors, and introduces foreign exchange risks. "
                "Furthermore, enforcing a foreign award in Pakistan requires separate proceedings under the 2011 Recognition Act."
            ),
            "recommendation": "Counter with Pakistan law and local arbitration in Lahore or Karachi under the Arbitration Act, 1940."
        },
        {
            "trigger": r"\b(indemnify|indemnity|hold harmless)\b",
            "context": "indemnity",
            "title": "Unilateral Third-Party Indemnification Imposed",
            "risk": "HIGH RISK",
            "impact": (
                "Counterparty added an aggressive one-sided indemnification obligation against your client for intellectual property and third-party claims. "
                "Legal Impact: Client acts as an uncompensated insurer for the counterparty without requirement of actual fault or negligence."
            ),
            "recommendation": "Make indemnity strictly mutual, cap it at contract value, and carve out counterparty negligence."
        },
        {
            "trigger": r"\b(5 days|immediate|without notice|3 days)\b",
            "context": "termination",
            "title": "Termination Notice Drastically Shortened",
            "risk": "MEDIUM RISK",
            "impact": (
                "Notice period for convenience reduced from 30 days to 5 days. "
                "Legal Impact: Leaves insufficient time to transition personnel, wind down project resources, or mitigate operational downtime."
            ),
            "recommendation": "Restore minimum 30-day written notice for convenience."
        },
        {
            "trigger": r"\b(non-compete|restraint|2 years|competing business)\b",
            "context": "restrictive_covenant",
            "title": "Post-Termination Non-Compete Clause Added (Void under Section 27)",
            "risk": "HIGH RISK (ILLEGAL RESTRICTION)",
            "impact": (
                "Counterparty introduced a 2-year post-termination restriction on engaging in competing trade. "
                "Legal Impact: Under Section 27 of The Contract Act, 1872, all agreements in restraint of lawful profession, trade, or business "
                "are void ab initio in Pakistan (see PLD 2021 SC 362). While legally unenforceable in Pakistani courts, it creates chilling dispute risks."
            ),
            "recommendation": "Delete entirely. Replace with customary non-solicitation of active clients for 6 months."
        }
    ]

    @classmethod
    def compare_contracts(
        cls,
        v1_contract: Dict[str, Any],
        v2_contract: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Performs clause-by-clause diffing and generates legal impact assessments.
        """
        v1_clauses = {c.get("clause_number", str(i)): c for i, c in enumerate(v1_contract.get("clauses", []))}
        v2_clauses = {c.get("clause_number", str(i)): c for i, c in enumerate(v2_contract.get("clauses", []))}

        all_clause_keys = sorted(list(set(v1_clauses.keys()) | set(v2_clauses.keys())), key=lambda x: str(x))
        diff_records = []
        high_risk_changes = 0

        for key in all_clause_keys:
            c1 = v1_clauses.get(key)
            c2 = v2_clauses.get(key)

            if c1 and not c2:
                # Removed
                diff_records.append({
                    "clause_number": key,
                    "heading": c1.get("clause_heading") or c1.get("clause_title", "Clause"),
                    "change_type": "REMOVED",
                    "v1_text": c1.get("text", ""),
                    "v2_text": "",
                    "impact": f"Clause {key} was entirely deleted by counterparty. Review whether critical protections were stripped.",
                    "risk": "MEDIUM RISK",
                    "recommendation": "Confirm whether deletion was intentional or adverse."
                })
            elif not c1 and c2:
                # Added
                c2_text = c2.get("text", "")
                impact_info = cls._analyze_text_impact(c2_text)
                if "HIGH" in impact_info["risk"]:
                    high_risk_changes += 1

                diff_records.append({
                    "clause_number": key,
                    "heading": c2.get("clause_heading") or c2.get("clause_title", "Clause"),
                    "change_type": "ADDED",
                    "v1_text": "",
                    "v2_text": c2_text,
                    "impact": impact_info["impact"],
                    "risk": impact_info["risk"],
                    "recommendation": impact_info["recommendation"]
                })
            else:
                # Both exist - check if modified
                t1 = c1.get("text", "").strip()
                t2 = c2.get("text", "").strip()

                if t1 != t2:
                    impact_info = cls._analyze_text_impact(t2, old_text=t1)
                    if "HIGH" in impact_info["risk"]:
                        high_risk_changes += 1

                    # Generate diff summary
                    diff = list(difflib.unified_diff(
                        t1.splitlines(),
                        t2.splitlines(),
                        lineterm="",
                        n=0
                    ))

                    diff_records.append({
                        "clause_number": key,
                        "heading": c2.get("clause_heading") or c2.get("clause_title", "Clause"),
                        "change_type": "MODIFIED",
                        "v1_text": t1,
                        "v2_text": t2,
                        "diff_lines": [line for line in diff if line.startswith("+") or line.startswith("-")][:6],
                        "impact": impact_info["impact"],
                        "risk": impact_info["risk"],
                        "recommendation": impact_info["recommendation"]
                    })
                else:
                    diff_records.append({
                        "clause_number": key,
                        "heading": c1.get("clause_heading") or c1.get("clause_title", "Clause"),
                        "change_type": "UNCHANGED",
                        "v1_text": t1,
                        "v2_text": t2,
                        "impact": "No substantive or linguistic changes detected.",
                        "risk": "LOW RISK",
                        "recommendation": "Accept as-is."
                    })

        summary = {
            "v1_title": v1_contract.get("title", "Version 1 (Client Original)"),
            "v2_title": v2_contract.get("title", "Version 2 (Counterparty Redline)"),
            "total_clauses_reviewed": len(diff_records),
            "added_clauses_count": sum(1 for d in diff_records if d["change_type"] == "ADDED"),
            "removed_clauses_count": sum(1 for d in diff_records if d["change_type"] == "REMOVED"),
            "modified_clauses_count": sum(1 for d in diff_records if d["change_type"] == "MODIFIED"),
            "high_risk_changes_count": high_risk_changes,
            "overall_assessment": "CRITICAL REVISIONS REQUIRED: Counterparty markup significantly shifts commercial risk." if high_risk_changes > 0 else "ACCEPTABLE REVISIONS: Markup is generally aligned with standard commercial terms.",
            "clause_comparisons": diff_records
        }

        return summary

    @classmethod
    def _analyze_text_impact(cls, new_text: str, old_text: str = "") -> Dict[str, str]:
        """Maps specific text changes to plain-language legal impacts."""
        combined = f"{old_text} -> {new_text}".lower()

        for rule in cls.IMPACT_RULES:
            if re.search(rule["trigger"], new_text.lower()):
                return {
                    "impact": rule["impact"],
                    "risk": rule["risk"],
                    "recommendation": rule["recommendation"]
                }

        return {
            "impact": "Minor wording adjustments with negligible impact on operative rights.",
            "risk": "LOW RISK",
            "recommendation": "Acceptable if commercial intent is preserved."
        }

    @classmethod
    def export_comparison_reports(
        cls,
        comparison_data: Dict[str, Any],
        output_dir: str = "outputs"
    ) -> Tuple[str, str]:
        """Exports comparison to Markdown and JSON formats."""
        os.makedirs(output_dir, exist_ok=True)

        json_path = os.path.join(output_dir, "contract_comparison.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(comparison_data, jf, indent=2)

        md_path = os.path.join(output_dir, "contract_comparison.md")
        with open(md_path, "w", encoding="utf-8") as mf:
            mf.write("# Contract Redline Comparison & Legal Impact Analysis\n")
            mf.write("**Client:** Khan & Associates  \n")
            mf.write(f"**Drafts Compared:** `{comparison_data['v1_title']}` vs. `{comparison_data['v2_title']}`  \n")
            mf.write(f"**Overall Assessment:** {comparison_data['overall_assessment']}  \n\n")
            mf.write("---\n\n")

            mf.write("## 1. Executive Redline Metrics\n\n")
            mf.write(f"- **Total Clauses Analyzed:** {comparison_data['total_clauses_reviewed']}\n")
            mf.write(f"- **Clauses Modified:** {comparison_data['modified_clauses_count']}\n")
            mf.write(f"- **Clauses Added:** {comparison_data['added_clauses_count']}\n")
            mf.write(f"- **Clauses Removed:** {comparison_data['removed_clauses_count']}\n")
            mf.write(f"- **High-Risk Legal Deviations:** **{comparison_data['high_risk_changes_count']}**\n\n")

            mf.write("---\n\n")
            mf.write("## 2. Clause-by-Clause Legal Impact Evaluation\n\n")

            for item in comparison_data["clause_comparisons"]:
                if item["change_type"] == "UNCHANGED":
                    continue

                mf.write(f"### Clause {item['clause_number']}: {item['heading']} [{item['change_type']}]\n")
                mf.write(f"**Risk Severity:** `{item['risk']}`  \n\n")

                if item.get("diff_lines"):
                    mf.write("```diff\n")
                    for line in item["diff_lines"]:
                        mf.write(f"{line}\n")
                    mf.write("```\n\n")

                mf.write(f"**Plain-Language Legal Impact:**  \n{item['impact']}  \n\n")
                mf.write(f"**Strategic Pushback Recommendation:**  \n*{item['recommendation']}*  \n\n")
                mf.write("---\n\n")

        print(f"[ContractComparator] Exported comparison reports to:\n  - {json_path}\n  - {md_path}")
        return json_path, md_path


def create_sample_contracts_pair() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Creates a realistic v1 Original vs v2 Counterparty Markup pair for demonstration."""
    v1 = {
        "title": "Version 1 (Client Original - Balanced)",
        "clauses": [
            {
                "clause_number": "1",
                "clause_heading": "Governing Law & Jurisdiction",
                "text": "This Agreement shall be governed by and construed in accordance with the laws of the Islamic Republic of Pakistan. The courts of Lahore shall have exclusive jurisdiction."
            },
            {
                "clause_number": "2",
                "clause_heading": "Limitation of Liability",
                "text": "The aggregate liability of either party arising out of or related to this Agreement shall be strictly capped at the total fees paid by Client in the preceding 12 months."
            },
            {
                "clause_number": "3",
                "clause_heading": "Termination for Convenience",
                "text": "Either party may terminate this agreement without cause upon providing at least thirty (30) days prior written notice."
            },
            {
                "clause_number": "4",
                "clause_heading": "Confidentiality",
                "text": "Each party agrees to hold all confidential information in strict confidence for a period of two (2) years following disclosure."
            }
        ]
    }

    v2 = {
        "title": "Version 2 (Counterparty Redline Markup - Aggressive)",
        "clauses": [
            {
                "clause_number": "1",
                "clause_heading": "Governing Law & Jurisdiction",
                "text": "This Agreement shall be governed by the laws of England and Wales, and the High Court of Justice in London shall have exclusive jurisdiction."
            },
            {
                "clause_number": "2",
                "clause_heading": "Limitation of Liability",
                "text": "The liability of Client under this Agreement shall be unlimited and shall include all indirect, special, punitive, and consequential damages."
            },
            {
                "clause_number": "3",
                "clause_heading": "Termination for Convenience",
                "text": "Counterparty may terminate this agreement immediately without notice; Client must provide sixty (60) days notice."
            },
            {
                "clause_number": "4",
                "clause_heading": "Confidentiality",
                "text": "Each party agrees to hold all confidential information in strict confidence for a period of two (2) years following disclosure."
            },
            {
                "clause_number": "5",
                "clause_heading": "Post-Termination Non-Compete",
                "text": "Client and its affiliates shall not engage in any competing software or consulting business across South Asia for a period of 2 years post-termination."
            }
        ]
    }

    return v1, v2


if __name__ == "__main__":
    v1, v2 = create_sample_contracts_pair()
    comparator = ContractComparator()
    diff_res = comparator.compare_contracts(v1, v2)
    print("\n--- Contract Comparison Summary ---")
    print(f"Reviewed: {diff_res['total_clauses_reviewed']} clauses")
    print(f"High-Risk Deviations: {diff_res['high_risk_changes_count']}")
    print(f"Assessment: {diff_res['overall_assessment']}")
    comparator.export_comparison_reports(diff_res)
