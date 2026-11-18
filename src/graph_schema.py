"""
Legal Knowledge Graph Schema Definition
Day 3: Legal Knowledge Graph & GraphRAG (Khan & Associates)

Defines:
- Node Types: Act, Section, Case, Court, Judge, Party, Clause, Contract
- Relationship Types: CITES, INTERPRETS, OVERRULES, FOLLOWS, DECIDED_BY, PRESIDED_BY,
                      HAS_PARTY, CONTAINS_SECTION, CONTAINS_CLAUSE, GOVERNED_BY
- Schema Metadata, Constraints, and Mermaid Diagram Generation
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class NodeSchema:
    name: str
    primary_key: str
    properties: List[str]
    description: str
    color: str


@dataclass
class RelationshipSchema:
    name: str
    source_node: str
    target_node: str
    properties: List[str]
    description: str


class LegalGraphSchema:
    """Canonical schema for Khan & Associates Legal Knowledge Graph."""

    NODES: Dict[str, NodeSchema] = {
        "Act": NodeSchema(
            name="Act",
            primary_key="act_id",
            properties=["act_id", "title", "year", "act_number", "jurisdiction"],
            description="Statutory Act passed by Parliament or Provincial Assembly (e.g., Contract Act, 1872)",
            color="#4CAF50"  # Green
        ),
        "Section": NodeSchema(
            name="Section",
            primary_key="section_id",
            properties=["section_id", "number", "title", "act_id", "text"],
            description="Individual statutory section or article (e.g., Section 23)",
            color="#8BC34A"  # Light Green
        ),
        "Case": NodeSchema(
            name="Case",
            primary_key="case_id",
            properties=["case_id", "title", "citation", "year", "court", "disposition", "holding", "is_overruled", "overruled_by"],
            description="Judicial decision or precedent (e.g., PLD 2021 SC 362, C.A. 419/2011)",
            color="#2196F3"  # Blue
        ),
        "Court": NodeSchema(
            name="Court",
            primary_key="court_id",
            properties=["court_id", "name", "jurisdiction", "city"],
            description="Judicial forum or tribunal (e.g., Supreme Court of Pakistan, Lahore High Court)",
            color="#FF9800"  # Orange
        ),
        "Judge": NodeSchema(
            name="Judge",
            primary_key="judge_id",
            properties=["judge_id", "name", "title", "role"],
            description="Presiding judicial officer or Justice (e.g., Justice Umar Ata Bandial, Justice Syed Mansoor Ali Shah)",
            color="#9C27B0"  # Purple
        ),
        "Party": NodeSchema(
            name="Party",
            primary_key="party_id",
            properties=["party_id", "name", "type"],  # type: corporate, individual, state
            description="Litigant or signatory (e.g., Federation of Pakistan, Mia Corp Pvt Ltd)",
            color="#607D8B"  # Gray-Blue
        ),
        "Contract": NodeSchema(
            name="Contract",
            primary_key="contract_id",
            properties=["contract_id", "title", "effective_date", "governing_law"],
            description="Commercial agreement or deed (e.g., Employment Agreement Lahore)",
            color="#009688"  # Teal
        ),
        "Clause": NodeSchema(
            name="Clause",
            primary_key="clause_id",
            properties=["clause_id", "number", "title", "contract_id", "category", "text"],
            description="Operational contract clause (e.g., Clause 14 Governing Law & Arbitration)",
            color="#00BCD4"  # Cyan
        )
    }

    RELATIONSHIPS: List[RelationshipSchema] = [
        RelationshipSchema(
            name="CITES",
            source_node="Case",
            target_node="Case",
            properties=["page", "paragraph", "weight"],
            description="Judicial citation where one case references or discusses another"
        ),
        RelationshipSchema(
            name="INTERPRETS",
            source_node="Case",
            target_node="Section",
            properties=["scope", "ratio_decidendi", "key_finding"],
            description="Judicial interpretation or constitutional construction of a statutory section"
        ),
        RelationshipSchema(
            name="OVERRULES",
            source_node="Case",
            target_node="Case",
            properties=["overruling_year", "bench_size", "grounds"],
            description="Higher or larger bench declaring an earlier precedent invalid / bad law"
        ),
        RelationshipSchema(
            name="FOLLOWS",
            source_node="Case",
            target_node="Case",
            properties=["applied_ratio"],
            description="Subsequent decision adhering to and affirming earlier binding ratio"
        ),
        RelationshipSchema(
            name="DECIDED_BY",
            source_node="Case",
            target_node="Court",
            properties=["bench_type"],  # e.g., Full Bench, Division Bench
            description="Court forum that pronounced the judgment"
        ),
        RelationshipSchema(
            name="PRESIDED_BY",
            source_node="Case",
            target_node="Judge",
            properties=["role", "authored_judgment"],  # role: CJ, Member Judge
            description="Judges constituting the bench that adjudicated the case"
        ),
        RelationshipSchema(
            name="HAS_PARTY",
            source_node="Case",
            target_node="Party",
            properties=["role"],  # appellant, petitioner, respondent, defendant
            description="Litigants involved in the proceedings"
        ),
        RelationshipSchema(
            name="CONTAINS_SECTION",
            source_node="Act",
            target_node="Section",
            properties=["chapter", "part"],
            description="Statute hierarchy linking Act to its sections"
        ),
        RelationshipSchema(
            name="CONTAINS_CLAUSE",
            source_node="Contract",
            target_node="Clause",
            properties=["order"],
            description="Contract structure linking contract to its contractual clauses"
        ),
        RelationshipSchema(
            name="GOVERNED_BY",
            source_node="Contract",
            target_node="Act",
            properties=["jurisdiction"],
            description="Statutory legal framework governing the commercial agreement"
        ),
        RelationshipSchema(
            name="PARTY_TO",
            source_node="Party",
            target_node="Contract",
            properties=["role"],  # employer, employee, lessor, lessee
            description="Signatories to a commercial contract"
        )
    ]

    @classmethod
    def get_mermaid_diagram(cls) -> str:
        """Generates Mermaid class / ER diagram representing the legal knowledge graph schema."""
        lines = [
            "classDiagram",
            "    direction TB",
            "    class Act {",
            "        +string act_id",
            "        +string title",
            "        +int year",
            "    }",
            "    class Section {",
            "        +string section_id",
            "        +string number",
            "        +string title",
            "    }",
            "    class Case {",
            "        +string case_id",
            "        +string citation",
            "        +string holding",
            "        +bool is_overruled",
            "    }",
            "    class Court {",
            "        +string court_id",
            "        +string name",
            "    }",
            "    class Judge {",
            "        +string judge_id",
            "        +string name",
            "    }",
            "    class Party {",
            "        +string party_id",
            "        +string name",
            "    }",
            "    class Contract {",
            "        +string contract_id",
            "        +string title",
            "    }",
            "    class Clause {",
            "        +string clause_id",
            "        +string number",
            "    }",
            "    Act \"1\" --> \"*\" Section : CONTAINS_SECTION",
            "    Case \"*\" --> \"*\" Case : CITES",
            "    Case \"*\" --> \"*\" Case : OVERRULES",
            "    Case \"*\" --> \"*\" Case : FOLLOWS",
            "    Case \"*\" --> \"*\" Section : INTERPRETS",
            "    Case \"*\" --> \"1\" Court : DECIDED_BY",
            "    Case \"*\" --> \"*\" Judge : PRESIDED_BY",
            "    Case \"*\" --> \"*\" Party : HAS_PARTY",
            "    Contract \"1\" --> \"*\" Clause : CONTAINS_CLAUSE",
            "    Contract \"*\" --> \"1\" Act : GOVERNED_BY",
            "    Party \"*\" --> \"*\" Contract : PARTY_TO"
        ]
        return "\n".join(lines)

    @classmethod
    def get_cypher_constraints(cls) -> List[str]:
        """Returns Cypher schema DDL statements for uniqueness constraints and indexes."""
        return [
            "CREATE CONSTRAINT act_id_unique IF NOT EXISTS FOR (a:Act) REQUIRE a.act_id IS UNIQUE;",
            "CREATE CONSTRAINT section_id_unique IF NOT EXISTS FOR (s:Section) REQUIRE s.section_id IS UNIQUE;",
            "CREATE CONSTRAINT case_id_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.case_id IS UNIQUE;",
            "CREATE CONSTRAINT court_id_unique IF NOT EXISTS FOR (co:Court) REQUIRE co.court_id IS UNIQUE;",
            "CREATE CONSTRAINT judge_id_unique IF NOT EXISTS FOR (j:Judge) REQUIRE j.judge_id IS UNIQUE;",
            "CREATE CONSTRAINT party_id_unique IF NOT EXISTS FOR (p:Party) REQUIRE p.party_id IS UNIQUE;",
            "CREATE CONSTRAINT contract_id_unique IF NOT EXISTS FOR (ct:Contract) REQUIRE ct.contract_id IS UNIQUE;",
            "CREATE CONSTRAINT clause_id_unique IF NOT EXISTS FOR (cl:Clause) REQUIRE cl.clause_id IS UNIQUE;",
            "CREATE INDEX case_citation_idx IF NOT EXISTS FOR (c:Case) ON (c.citation);",
            "CREATE INDEX section_num_idx IF NOT EXISTS FOR (s:Section) ON (s.number);"
        ]


if __name__ == "__main__":
    print("Legal Graph Schema defined:")
    print(f"Nodes: {list(LegalGraphSchema.NODES.keys())}")
    print(f"Relationships: {[r.name for r in LegalGraphSchema.RELATIONSHIPS]}")
    print("\nMermaid Diagram:\n")
    print(LegalGraphSchema.get_mermaid_diagram())
