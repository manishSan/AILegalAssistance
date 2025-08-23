import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SQL_PATH = Path("database_setup_sample.sql")

Case = Dict[str, Any]
Party = Dict[str, Any]
Document = Dict[str, Any]
CaseEvent = Dict[str, Any]


def _parse_json_like(value: str) -> Any:
    """Parse a Postgres JSONB literal that's inside single quotes.
    We do a very permissive parse by replacing single quotes with double where appropriate.
    """
    import json

    # Strip surrounding quotes if present
    v = value.strip()
    if v.startswith("'") and v.endswith("'"):
        v = v[1:-1]
    # Replace single quotes around keys with double quotes if needed
    # This is a heuristic; our sample JSON uses double quotes already.
    try:
        return json.loads(v)
    except Exception:
        return v


def load_database(case_filter: Optional[str] = None) -> Tuple[Dict[str, Case], List[Party], List[Document], List[CaseEvent]]:
    """Load data from the provided SQL file into in-memory structures.

    Returns:
        cases: dict keyed by case_id
        parties: list of party dicts
        documents: list of document dicts
        events: list of event dicts
    """
    if not SQL_PATH.exists():
        raise FileNotFoundError(f"Missing {SQL_PATH}")

    text = SQL_PATH.read_text(encoding="utf-8")

    cases: Dict[str, Case] = {}
    parties: List[Party] = []
    documents: List[Document] = []
    events: List[CaseEvent] = []

    # Parse INSERT INTO cases (... ) VALUES (...);
    case_pattern = re.compile(
        r"INSERT\s+INTO\s+cases\s*\(.*?\)\s*VALUES\s*\((.*?)\);",
        re.IGNORECASE | re.DOTALL,
    )
    case_match = case_pattern.search(text)
    if case_match:
        vals = _split_sql_values(case_match.group(1))
        if len(vals) >= 6:
            case_id = _strip_quotes(vals[0])
            cases[case_id] = {
                "case_id": case_id,
                "case_type": _strip_quotes(vals[1]),
                "date_filed": _strip_quotes(vals[2]),
                "status": _strip_quotes(vals[3]),
                "attorney_id": _to_int(vals[4]),
                "case_summary": _strip_quotes(vals[5]),
            }

    # Parse parties
    parties_pattern = re.compile(
        r"INSERT\s+INTO\s+parties\s*\(.*?\)\s*VALUES\s*(\(.*?\));",
        re.IGNORECASE | re.DOTALL,
    )
    pm = parties_pattern.search(text)
    if pm:
        tuples_text = pm.group(1)
        for tup in _split_sql_tuples(tuples_text):
            vals = _split_sql_values(tup)
            if len(vals) >= 5:
                parties.append(
                    {
                        "case_id": _strip_quotes(vals[0]),
                        "party_type": _strip_quotes(vals[1]),
                        "name": _strip_quotes(vals[2]),
                        "contact_info": _parse_json_like(vals[3]),
                        "insurance_info": _parse_json_like(vals[4]),
                    }
                )

    # Parse documents
    docs_pattern = re.compile(
        r"INSERT\s+INTO\s+documents\s*\(.*?\)\s*VALUES\s*(\(.*?\));",
        re.IGNORECASE | re.DOTALL,
    )
    dm = docs_pattern.search(text)
    if dm:
        tuples_text = dm.group(1)
        for tup in _split_sql_tuples(tuples_text):
            vals = _split_sql_values(tup)
            if len(vals) >= 6:
                documents.append(
                    {
                        "case_id": _strip_quotes(vals[0]),
                        "file_path": _strip_quotes(vals[1]),
                        "doc_category": _strip_quotes(vals[2]),
                        "upload_date": _strip_quotes(vals[3]),
                        "document_title": _strip_quotes(vals[4]),
                        "metadata": _parse_json_like(vals[5]),
                    }
                )

    # Parse case_events
    ev_pattern = re.compile(
        r"INSERT\s+INTO\s+case_events\s*\(.*?\)\s*VALUES\s*(\(.*?\));",
        re.IGNORECASE | re.DOTALL,
    )
    em = ev_pattern.search(text)
    if em:
        tuples_text = em.group(1)
        for tup in _split_sql_tuples(tuples_text):
            vals = _split_sql_values(tup)
            if len(vals) >= 4:
                events.append(
                    {
                        "case_id": _strip_quotes(vals[0]),
                        "event_date": _strip_quotes(vals[1]),
                        "event_type": _strip_quotes(vals[2]),
                        "description": _strip_quotes(vals[3]),
                        "amount": _to_float(vals[4]) if len(vals) > 4 else None,
                    }
                )

    if case_filter:
        parties = [p for p in parties if p["case_id"] == case_filter]
        documents = [d for d in documents if d["case_id"] == case_filter]
        events = [e for e in events if e["case_id"] == case_filter]
        cases = {k: v for k, v in cases.items() if k == case_filter}

    return cases, parties, documents, events


# --- Helpers ---

def _strip_quotes(s: str) -> str:
    s = s.strip()
    if s.upper() == "NULL":
        return ""
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1].replace("\\'", "'")
    return s


def _to_int(s: str) -> Optional[int]:
    try:
        return int(_strip_quotes(s))
    except Exception:
        return None


def _to_float(s: str) -> Optional[float]:
    try:
        return float(_strip_quotes(s))
    except Exception:
        return None


def _split_sql_values(group: str) -> List[str]:
    """Split a values group by commas, respecting quoted strings."""
    vals: List[str] = []
    buf = []
    in_str = False
    esc = False
    for ch in group:
        if in_str:
            if esc:
                buf.append(ch)
                esc = False
            elif ch == "\\":
                esc = True
                buf.append(ch)
            elif ch == "'":
                in_str = False
                buf.append(ch)
            else:
                buf.append(ch)
        else:
            if ch == "'":
                in_str = True
                buf.append(ch)
            elif ch == ",":
                vals.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
    if buf:
        vals.append("".join(buf).strip())
    return vals


def _split_sql_tuples(text: str) -> List[str]:
    """Split a multi-VALUES clause into individual tuple strings without outer parens."""
    tuples: List[str] = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                tuples.append(text[start:i])
                start = None
    return tuples
