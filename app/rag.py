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

    def build(self, documents: List[Dict], project_root: Path) -> None:
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
