from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    text: str
    doc_path: Path
    page: int
    title: Optional[str]

    def cite(self) -> str:
        t = f"{self.title} - " if self.title else ""
        return f"{t}{self.doc_path.name}, p.{self.page}"


class SimpleRAG:
    def __init__(self) -> None:
        self._chunks: List[Chunk] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None

    def build_page_embedding(self, documents: List[Dict], project_root: Path) -> None:
        """Build TF-IDF index from case documents.
        documents: rows from `documents` table
        project_root: repository root (cwd)
        """
        chunks: List[Chunk] = []
        for doc in documents:
            rel = doc.get("file_path", "").lstrip("/")
            p = (project_root / rel).resolve()
            title = doc.get("document_title")
            if not p.exists():
                continue
            try:
                for page_idx, page_layout in enumerate(extract_pages(str(p)), start=1):
                    texts: List[str] = []
                    for element in page_layout:
                        if isinstance(element, LTTextContainer):
                            texts.append(element.get_text())
                    page_text = "\n".join(texts).strip()
                    # Basic cleanup
                    page_text = re.sub(r"\s+", " ", page_text)
                    if page_text:
                        chunks.append(Chunk(text=page_text, doc_path=p, page=page_idx, title=title))
            except Exception:
                # Fall back: try to read as plain text if not a valid PDF
                try:
                    txt = p.read_text(encoding="utf-8")
                    if txt:
                        chunks.append(Chunk(text=txt, doc_path=p, page=1, title=title))
                except Exception:
                    pass
        self._chunks = chunks
        corpus = [c.text for c in chunks]
        self._vectorizer = TfidfVectorizer(stop_words="english", max_df=0.9)
        if corpus:
            self._matrix = self._vectorizer.fit_transform(corpus)
        else:
            self._matrix = None

    def _chunk_text(self, text: str, chunk_size: int = 512, overlap_pct: float = 0.1):
        overlap = int(chunk_size * overlap_pct)
        start = 0
        chunks = []
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start += chunk_size - overlap  # slide window by chunk_size - overlap
        return chunks

    def build_fixed_chunk_embedding(self, documents: List[Dict], project_root: Path) -> None:
        """Build TF-IDF index from case documents.
        documents: rows from `documents` table
        project_root: repository root (cwd)
        """
        chunks: List[Chunk] = []
        for doc in documents:
            rel = doc.get("file_path", "").lstrip("/")
            p = (project_root / rel).resolve()
            title = doc.get("document_title")
            if not p.exists():
                continue
            try:
                for page_idx, page_layout in enumerate(extract_pages(str(p)), start=1):
                    texts: List[str] = []
                    for element in page_layout:
                        if isinstance(element, LTTextContainer):
                            texts.append(element.get_text())
                    page_text = "\n".join(texts).strip()
                    # Basic cleanup
                    page_text = re.sub(r"\s+", " ", page_text)
                    if page_text:
                        for chunk_text_ in (self._chunk_text(page_text, chunk_size=512, overlap_pct=0.1)):
                            chunks.append(Chunk(text=chunk_text_, doc_path=p, page=page_idx, title=title))

            except Exception:
                # Fall back: try to read as plain text if not a valid PDF
                try:
                    txt = p.read_text(encoding="utf-8")
                    if txt:
                        chunks.append(Chunk(text=txt, doc_path=p, page=1, title=title))
                except Exception:
                    pass
        self._chunks = chunks
        corpus = [c.text for c in chunks]
        self._vectorizer = TfidfVectorizer(stop_words="english", max_df=0.9)
        if corpus:
            self._matrix = self._vectorizer.fit_transform(corpus)
        else:
            self._matrix = None

    def search(self, query: str, k: int = 5) -> List[Tuple[Chunk, float]]:
        if not self._chunks or self._vectorizer is None or self._matrix is None:
            return []
        qv = self._vectorizer.transform([query])
        sims = cosine_similarity(qv, self._matrix)[0]
        idxs = sims.argsort()[::-1][:k]
        results: List[Tuple[Chunk, float]] = []
        for i in idxs:
            results.append((self._chunks[int(i)], float(sims[int(i)])))
        return results

    def extract_amounts(self, text: str) -> List[str]:
        return re.findall(r"\$?\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b", text)


if __name__ == "__main__":
    import app.util as u
    docs_str = """[{"doc_id": 1, "case_id": "2024-PI-001", "file_path": "/sample_docs/2024-PI-001/medical_records_dr_jones.pdf", "doc_category": "medical", "upload_date": "2024-03-20", "document_title": "Medical Records - Dr. Michael Jones - Central Valley Medical Group", "metadata": {"pages": 8, "injuries": ["lumbar strain", "cervical whiplash", "shoulder contusion"], "provider": "Dr. Michael Jones", "date_range": "2024-03-16 to 2024-06-10", "total_expenses": 8950}}, {"doc_id": 2, "case_id": "2024-PI-001", "file_path": "/sample_docs/2024-PI-001/police_report_incident_789.pdf", "doc_category": "police_report", "upload_date": "2024-03-16", "document_title": "Police Report - SPD Report #789 - Traffic Collision", "metadata": {"officer": "Jennifer Martinez", "citations": ["CVC 21703", "CVC 23123"], "total_fines": 400, "report_number": "SPD-2024-789", "fault_determination": "100% defendant"}}, {"doc_id": 3, "case_id": "2024-PI-001", "file_path": "/sample_docs/2024-PI-001/wage_statements_2024.pdf", "doc_category": "financial", "upload_date": "2024-07-05", "document_title": "Wage Statements and Employment Records - Pacific Construction", "metadata": {"employer": "Pacific Construction Company", "position": "Construction Supervisor", "hourly_rate": 32.5, "time_off_weeks": 10.5, "total_wage_loss": 4940}}, {"doc_id": 4, "case_id": "2024-PI-001", "file_path": "/sample_docs/2024-PI-001/insurance_correspondence.pdf", "doc_category": "correspondence", "upload_date": "2024-06-25", "document_title": "Insurance Correspondence - ABC Insurance Communications", "metadata": {"adjuster": "Michael Rodriguez", "claim_number": "ABC-2024-789456", "settlement_range": "25000-35000", "liability_accepted": true}}]"""
    docs = u.json_loads(docs_str)

    rag = SimpleRAG()
    rag.build_fixed_chunk_embedding(docs, project_root=Path("./.."))

    out = rag.search(query="date of accident", k=4)
    print(out)
    # rag.extract_amounts(out[0])