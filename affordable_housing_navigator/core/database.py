"""Database repository for Tenant Cases and Living Briefs.

Supports SQLite persistent storage with a Firebase Firestore collection schema mapping.
Allows saving, retrieving, listing, filtering, and editing case records and briefs.
"""

import os
import json
import sqlite3
import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Firebase Firestore Document Schema Definition
# ---------------------------------------------------------------------------

class CaseDocument(BaseModel):
    """Schema corresponding 1:1 to a Firebase Firestore document in 'tenant_cases' collection."""
    case_id: str
    court_index_number: str
    tenant_name: str
    block_address: str
    metro_area: str = "New York"
    census_tract_geoid: str = "36061024500"
    hearing_date: str
    hearing_time: str = "09:30 AM"
    claimed_arrears: float = 0.0
    notice_type: str = "Nonpayment Petition"
    household_size: int = 1
    annual_income: float = 0.0
    hazard_narrative: str = ""
    status: str = "Active Intake"      # Active Intake, Brief Drafting, Brief Finalized, Hearing Ready
    urgency_level: str = "High"        # Critical, High, Medium, Low
    brief_markdown: str = ""
    brief_edits_count: int = 0
    corroborated_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    excluded_matches: List[Dict[str, Any]] = Field(default_factory=list)
    applicable_statutes: List[Dict[str, Any]] = Field(default_factory=list)
    eligible_funds: List[Dict[str, Any]] = Field(default_factory=list)
    tract_profile: Optional[Dict[str, Any]] = None
    building_location: Optional[Dict[str, Any]] = None
    caseworker_notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# SQLite Document Store with Firestore Schema compatibility
# ---------------------------------------------------------------------------

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "cases.db")


class CaseRepository:
    """Persistent storage for tenant cases, briefs, and caseworker notes."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._seed_default_cases_if_empty()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_cases (
                    case_id TEXT PRIMARY KEY,
                    court_index_number TEXT,
                    tenant_name TEXT,
                    block_address TEXT,
                    metro_area TEXT,
                    hearing_date TEXT,
                    claimed_arrears REAL,
                    status TEXT,
                    urgency_level TEXT,
                    document_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cases_hearing ON tenant_cases(hearing_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cases_status ON tenant_cases(status)")
            conn.commit()

    def save_case(self, case_doc: CaseDocument) -> CaseDocument:
        case_doc.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc_json = case_doc.model_dump_json()

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO tenant_cases (
                    case_id, court_index_number, tenant_name, block_address,
                    metro_area, hearing_date, claimed_arrears, status,
                    urgency_level, document_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(case_id) DO UPDATE SET
                    court_index_number = excluded.court_index_number,
                    tenant_name = excluded.tenant_name,
                    block_address = excluded.block_address,
                    metro_area = excluded.metro_area,
                    hearing_date = excluded.hearing_date,
                    claimed_arrears = excluded.claimed_arrears,
                    status = excluded.status,
                    urgency_level = excluded.urgency_level,
                    document_json = excluded.document_json,
                    updated_at = excluded.updated_at
            """, (
                case_doc.case_id,
                case_doc.court_index_number,
                case_doc.tenant_name,
                case_doc.block_address,
                case_doc.metro_area,
                case_doc.hearing_date,
                case_doc.claimed_arrears,
                case_doc.status,
                case_doc.urgency_level,
                doc_json,
                case_doc.created_at,
                case_doc.updated_at,
            ))
            conn.commit()
        return case_doc

    def get_case(self, case_id: str) -> Optional[CaseDocument]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT document_json FROM tenant_cases WHERE case_id = ?", (case_id,)).fetchone()
            if not row:
                return None
            data = json.loads(row["document_json"])
            return CaseDocument(**data)

    def list_cases(
        self,
        status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT document_json FROM tenant_cases ORDER BY hearing_date ASC"
        with self._get_connection() as conn:
            rows = conn.execute(query).fetchall()
            results = []
            for r in rows:
                doc = json.loads(r["document_json"])
                if status and status != "All" and doc.get("status") != status:
                    continue
                if search_query:
                    sq = search_query.lower()
                    matches = (
                        sq in doc.get("tenant_name", "").lower() or
                        sq in doc.get("court_index_number", "").lower() or
                        sq in doc.get("block_address", "").lower()
                    )
                    if not matches:
                        continue
                results.append(doc)
            return results

    def update_brief(self, case_id: str, new_brief_markdown: str, notes: Optional[str] = None) -> Optional[CaseDocument]:
        case = self.get_case(case_id)
        if not case:
            return None
        case.brief_markdown = new_brief_markdown
        case.brief_edits_count += 1
        if notes is not None:
            case.caseworker_notes = notes
        case.status = "Brief Finalized" if case.brief_edits_count > 1 else "Brief Drafting"
        return self.save_case(case)

    def delete_case(self, case_id: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM tenant_cases WHERE case_id = ?", (case_id,))
            conn.commit()
            return cur.rowcount > 0

    def _seed_default_cases_if_empty(self):
        with self._get_connection() as conn:
            count = conn.execute("SELECT count(*) as c FROM tenant_cases").fetchone()["c"]
            if count > 0:
                return

        # Seed Marisol V. (Washington Heights)
        marisol_brief = """# CIVIL COURT OF THE CITY OF NEW YORK · COUNTY OF NEW YORK · HOUSING PART
Index No. LT-029481/26/NY

## TENANT STABILIZATION BRIEF & INTAKE MEMORANDUM
**Tenant:** Marisol V. · **Household:** 3 Persons · **Claimed Arrears:** $3,350.00
**Hearing:** Monday, Nov 23, 2026 at 09:30 AM · **Courtroom:** Room 523 (111 Centre St)
**Property:** 1000 Block of St. Nicholas Ave, Manhattan · **Tract:** 36061024500

---

### Section 1: Corroborating Municipal Records (NYC HPD/311)
- `311-2026-1042-01` [✓ Kept · Class C Immediately Hazardous]: Heat & Hot Water failure reported since Nov 1, 2026. Still OPEN.
- `311-2026-1042-02` [✓ Kept · Class B Hazardous]: Water intrusion & black mold spreading along bathroom ceiling. Still OPEN.
- `DECOY-NEWY-05` [~~Excluded~~ Closed: Abated repair]: Commercial plumbing decoy filtered out.

### Section 2: Statutory Legal Defenses & Counterclaims
1. **NY Real Property Law § 235-b (Warranty of Habitability):** Pleading per se rent abatement for lack of heat during heating season and bathroom mold intrusion flaring child's asthma.
2. **NYC Admin Code § 27-2115 (Housing Maintenance Code):** Landlord failed to cure Class C violation within statutory 24-hour window.
3. **NY RPAPL § 711(2):** Demand verification of strict compliance with 14-day statutory written demand condition precedent.

### Section 3: Emergency Arrears Relief Matches
- **One Shot Deal (HRA Emergency Assistance):** QUALIFIED ($3,350 arrears under $15k limit; income under 200% FPL).
- **Emergency Repair Program ($5,500 grant):** QUALIFIED (Unlocked by verified Class C heat violation).
- **Right to Counsel (Local Law 136):** QUALIFIED (Washington Heights zip code).

### Section 4: Evidentiary Boundary
- What the record can't prove yet: Specific indoor temperature logs during November to calculate exact abatement percentage.

**Caseworker Review:** Verified by Hearth Intake Desk.
"""
        case_1 = CaseDocument(
            case_id="case-lt-029481-26",
            court_index_number="LT-029481/26/NY",
            tenant_name="Marisol V.",
            block_address="1000 Block of St. Nicholas Ave",
            metro_area="New York",
            census_tract_geoid="36061024500",
            hearing_date="2026-11-23",
            hearing_time="09:30 AM",
            claimed_arrears=3350.0,
            notice_type="Nonpayment Petition",
            household_size=3,
            annual_income=31000.0,
            hazard_narrative="The radiators have been cold since early November. I run the oven for heat. Black mold is spreading around the tub, and water leaks through the bathroom wall. Daniela's asthma has gotten worse.",
            status="Hearing Ready",
            urgency_level="Critical",
            brief_markdown=marisol_brief,
            brief_edits_count=1,
            building_location={
                "building_address": "1000 Block of St. Nicholas Ave",
                "census_tract_geoid": "36061024500",
                "latitude": 40.836626,
                "longitude": -73.942098,
                "google_maps_url": "https://www.google.com/maps/search/?api=1&query=1000%20Block%20of%20St.%20Nicholas%20Ave%2C%20New%20York%2C%20NY",
                "google_maps_embed_url": "https://www.google.com/maps?q=1000%20Block%20of%20St.%20Nicholas%20Ave%2C%20New%20York%2C%20NY&output=embed",
                "google_street_view_url": "https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=40.836626,-73.942098"
            },
            corroborated_evidence=[
                {"request_id": "311-2026-1042-01", "hazard_category": "Heat and Hot Water", "inspection_status": "Open", "block_address": "1000 Block of St. Nicholas Ave", "complaint_narrative": "Radiators completely cold throughout apartment line."},
                {"request_id": "311-2026-1042-02", "hazard_category": "Water Intrusion & Mold", "inspection_status": "Open", "block_address": "1000 Block of St. Nicholas Ave", "complaint_narrative": "Severe black mold growth on shower tiles and drywall leak."}
            ],
            applicable_statutes=[
                {"code_citation": "NY RPL § 235-b", "ordinance_title": "Implied Warranty of Habitability", "relevance_rationale": "Rent abatement counterclaim for lack of heat and mold."},
                {"code_citation": "NYC Admin Code § 27-2115", "ordinance_title": "24-Hour Heat Cure Mandate", "relevance_rationale": "Class C heat deficiency not cured within 24 hours."}
            ],
            eligible_funds=[
                {"program_name": "One Shot Deal (HRA)", "administering_agency": "NYC DSS / HRA", "verdict": "QUALIFIED", "max_assistance_amount": "$15,000", "action_item": "File emergency HRA application."},
                {"program_name": "Emergency Repair Program", "administering_agency": "NYC HPD", "verdict": "QUALIFIED", "max_assistance_amount": "$5,500", "action_item": "Habitability gate unlocked by open 311 violations."}
            ]
        )

        # Seed Hector M. (Mott Haven, Bronx)
        case_2 = CaseDocument(
            case_id="case-lt-018274-26",
            court_index_number="LT-018274/26/BX",
            tenant_name="Hector M.",
            block_address="500 Block of E 138th St",
            metro_area="New York",
            census_tract_geoid="36005002500",
            hearing_date="2026-11-25",
            hearing_time="10:00 AM",
            claimed_arrears=4100.0,
            notice_type="Nonpayment Petition",
            household_size=2,
            annual_income=28500.0,
            hazard_narrative="Ceiling plaster collapsed after roof leak during heavy rains in October. Landlord has ignored requests and filed eviction.",
            status="Active Intake",
            urgency_level="High",
            brief_markdown="## Case Brief: Hector M. (Mott Haven)\n\nDefective 14-day demand and structural water damage under RPL § 235-b."
        )

        # Seed Fatima K. (Grand Concourse, Bronx)
        case_3 = CaseDocument(
            case_id="case-lt-033109-26",
            court_index_number="LT-033109/26/BX",
            tenant_name="Fatima K.",
            block_address="1200 Block of Grand Concourse",
            metro_area="New York",
            census_tract_geoid="36005018900",
            hearing_date="2026-12-02",
            hearing_time="09:30 AM",
            claimed_arrears=2800.0,
            notice_type="Nonpayment Petition",
            household_size=4,
            annual_income=34000.0,
            hazard_narrative="Chronic rodent infestation and peeling paint in children's bedroom. Public assistance rent checks were improperly held by management.",
            status="Brief Drafting",
            urgency_level="Medium",
            brief_markdown="## Case Brief: Fatima K. (Grand Concourse)\n\nPleading Spiegel Law defense (Social Services Law § 143-b) for withholding rent checks while hazardous violations exist."
        )

        # Seed Devon B. (Flatbush, Brooklyn)
        case_4 = CaseDocument(
            case_id="case-lt-009412-26",
            court_index_number="LT-009412/26/KN",
            tenant_name="Devon B.",
            block_address="200 Block of Flatbush Ave",
            metro_area="New York",
            census_tract_geoid="36047016100",
            hearing_date="2026-12-08",
            hearing_time="11:00 AM",
            claimed_arrears=5200.0,
            notice_type="Nonpayment Petition",
            household_size=1,
            annual_income=24000.0,
            hazard_narrative="Rent stabilized lease rider was omitted and rent was improperly hiked above legal regulated threshold. CityFHEPS supplement voucher is in review.",
            status="Brief Finalized",
            urgency_level="Low",
            brief_markdown="## Case Brief: Devon B. (Flatbush)\n\nRent overcharge counterclaim and CityFHEPS preservation grant match."
        )

        self.save_case(case_1)
        self.save_case(case_2)
        self.save_case(case_3)
        self.save_case(case_4)


case_repo = CaseRepository()
