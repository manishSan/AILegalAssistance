from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from .db_pg import get_conn, fetch_all_dicts


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
                return fetch_all_dicts(cur, "SELECT * FROM timeline WHERE case_id = %s AND event_type = %s ORDER BY event_date", [case_id, event_type])
            return fetch_all_dicts(cur, "SELECT * FROM timeline WHERE case_id = %s ORDER BY event_date", [case_id])

    # 4. get_financial_summary
    def get_financial_summary(self, case_id: str) -> Dict[str, Any]:
        with get_conn() as conn, conn.cursor() as cur:
            meds = fetch_all_dicts(cur, "SELECT amount FROM medical_bills WHERE case_id = %s", [case_id])
            wages = fetch_all_dicts(cur, "SELECT amount FROM lost_wages WHERE case_id = %s", [case_id])
            total_medical = sum(x.get("amount", 0) or 0 for x in meds)
            lost_wages = sum(x.get("amount", 0) or 0 for x in wages)
            return {
                "total_medical": float(total_medical),
                "lost_wages": float(lost_wages),
                "total_known": float(total_medical + lost_wages),
            }

    # 5. search_similar_cases (toy example)
    def search_similar_cases(self, case_type: str, keywords: List[str]) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            rows = fetch_all_dicts(cur, "SELECT case_id, case_type, summary FROM similar_cases WHERE case_type = %s", [case_type])
            scores: Dict[str, int] = defaultdict(int)
            for r in rows:
                text = (r.get("summary") or "").lower()
                for kw in keywords:
                    if kw.lower() in text:
                        scores[r["case_id"]] += 1
            ordered = sorted(rows, key=lambda r: scores.get(r["case_id"], 0), reverse=True)
            return ordered[:5]
