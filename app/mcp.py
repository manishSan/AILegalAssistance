from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from .db_pg import get_conn, fetch_all_dicts


class MCP:
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
                q = """
                SELECT case_id, file_path, doc_category, upload_date, document_title, metadata
                FROM documents WHERE case_id = %s AND doc_category = %s
                """
                return fetch_all_dicts(cur, q, [case_id, category])
            q = """
            SELECT case_id, file_path, doc_category, upload_date, document_title, metadata
            FROM documents WHERE case_id = %s
            """
            return fetch_all_dicts(cur, q, [case_id])

    # 3. get_case_timeline
    def get_case_timeline(self, case_id: str, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            if event_type:
                q = """
                SELECT case_id, event_date, event_type, description, amount
                FROM case_events WHERE case_id = %s AND event_type = %s
                ORDER BY event_date
                """
                return fetch_all_dicts(cur, q, [case_id, event_type])
            q = """
            SELECT case_id, event_date, event_type, description, amount
            FROM case_events WHERE case_id = %s
            ORDER BY event_date
            """
            return fetch_all_dicts(cur, q, [case_id])

    # 4. get_financial_summary
    def get_financial_summary(self, case_id: str) -> Dict[str, Any]:
        with get_conn() as conn, conn.cursor() as cur:
            # Totals by event_type
            q = """
            SELECT event_type, SUM(amount) AS total_amount
            FROM case_events
            WHERE case_id = %s AND amount IS NOT NULL
            GROUP BY event_type
            """
            rows = fetch_all_dicts(cur, q, [case_id])
            totals = defaultdict(float)
            for r in rows:
                try:
                    totals[str(r["event_type"]) or ""] += float(r["total_amount"]) if r["total_amount"] is not None else 0.0
                except Exception:
                    pass

            # Medical total: medical_treatment + medical-like expenses
            q_med = """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM case_events
            WHERE case_id = %s AND event_type = 'medical_treatment' AND amount IS NOT NULL
            """
            med_rows = fetch_all_dicts(cur, q_med, [case_id])
            med_total = float(med_rows[0]["total"]) if med_rows else 0.0

            q_exp_med = """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM case_events
            WHERE case_id = %s AND event_type = 'expense' AND amount IS NOT NULL
              AND (
                lower(description) LIKE '%%medical%%'
                OR lower(description) LIKE '%%therapy%%'
                OR lower(description) LIKE '%%prescription%%'
                OR lower(description) LIKE '%%pharmacy%%'
                OR lower(description) LIKE '%%imaging%%'
                OR lower(description) LIKE '%%mri%%'
                OR lower(description) LIKE '%%hospital%%'
              )
            """
            exp_med_rows = fetch_all_dicts(cur, q_exp_med, [case_id])
            med_total += float(exp_med_rows[0]["total"]) if exp_med_rows else 0.0

            # Lost wages from documents.metadata -> total_wage_loss
            q_docs = """
            SELECT metadata
            FROM documents
            WHERE case_id = %s
            """
            docs = fetch_all_dicts(cur, q_docs, [case_id])
            lost_wages = 0.0
            for d in docs:
                meta = d.get("metadata")
                if isinstance(meta, dict) and "total_wage_loss" in meta:
                    try:
                        lost_wages = float(meta["total_wage_loss"])  # last wins
                    except Exception:
                        pass

            return {
                "by_type": dict(totals),
                "total_medical": round(med_total, 2),
                "lost_wages": round(lost_wages, 2),
                "total_known": round(med_total + lost_wages, 2),
            }

    # 5. search_similar_cases (toy example)
    def search_similar_cases(self, case_type: str, keywords: List[str]) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            q = "SELECT * FROM cases WHERE case_type = %s"
            cases = fetch_all_dicts(cur, q, [case_type])
            results: List[Dict[str, Any]] = []
            for c in cases:
                score = 0
                summary = (c.get("case_summary") or "").lower()
                for kw in keywords:
                    if kw.lower() in summary:
                        score += 1
                if score:
                    results.append({"case": c, "score": score})
            return sorted(results, key=lambda x: x["score"], reverse=True)[:5]

    # 6. get_party_details
    def get_party_details(self, case_id: str, party_type: str) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            q = """
            SELECT case_id, party_type, name, contact_info, insurance_info
            FROM parties WHERE case_id = %s AND party_type = %s
            """
            return fetch_all_dicts(cur, q, [case_id, party_type])
