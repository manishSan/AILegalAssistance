from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.db_pg import get_conn, fetch_all_dicts


class CaseData:
    def __init__(self, case_filter: Optional[str] = None) -> None:
        # case_filter is accepted for API compatibility; queries will filter by case_id as needed
        self.case_filter = case_filter

    # 1. get_case_details
    def get_case_details(self, case_id: str) -> Dict[str, Any]:
        with get_conn() as conn, conn.cursor() as cur:
            case_rows = fetch_all_dicts(cur, "SELECT * FROM cases WHERE case_id = %s", [case_id])
            if not case_rows:
                return {}
            party_rows = fetch_all_dicts(cur, "SELECT case_id, party_type, name, contact_info, insurance_info FROM parties WHERE case_id = %s", [case_id])
            return {"case": case_rows[0], "parties": party_rows}

    # 2. get_case_documents
    def get_case_documents(self, case_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            if category:
                return fetch_all_dicts(cur, "SELECT * FROM documents WHERE case_id = %s AND category = %s", [case_id, category])
            return fetch_all_dicts(cur, "SELECT * FROM documents WHERE case_id = %s", [case_id])

    # 3. get_case_timeline
    def get_case_timeline(self, case_id: str, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            if event_type:
                return fetch_all_dicts(cur, "SELECT * FROM case_events WHERE case_id = %s AND event_type = %s ORDER BY event_date", [case_id, event_type])
            return fetch_all_dicts(cur, "SELECT * FROM case_events WHERE case_id = %s ORDER BY event_date", [case_id])

    # 4. Get parties data
    def get_parties_data(self, case_id: str, party_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            if party_type:
                return fetch_all_dicts(cur, query="SELECT * FROM parties WHERE case_id = %s AND party_type = %s", params=[case_id, party_type])
            return fetch_all_dicts(cur, query="SELECT * FROM parties WHERE case_id = %s", params=[case_id])


if __name__ == "__main__":
    data = CaseData()
    # test
    # docs = data.get_case_documents(case_id="2024-PI-001")
    # import app.util as u
    # out = u.json_dumps(docs)
    # print(out)


    # out = data.get_case_timeline(case_id="2024-PI-001")
    # print(out)

    out = data.get_parties_data("2024-PI-001")
    print(out)