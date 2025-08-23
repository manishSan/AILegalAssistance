from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from .case_data import CaseData
from .rag import SimpleRAG


mcp = FastMCP("Legal Case MCP (SSE)")

def _mcp() -> CaseData:
    # Limit to the default sample case; clients can pass other case_ids to methods
    return CaseData()

# Simple in-memory RAG cache per case_id
_rag_cache: Dict[str, SimpleRAG] = {}

def _get_rag(case_id: str) -> SimpleRAG:
    rag = _rag_cache.get(case_id)
    if rag is None:
        rag = SimpleRAG()
        docs = _mcp().get_case_documents(case_id)
        # Build index from repository root (cwd)
        rag.build(documents=docs, project_root=Path.cwd())
        _rag_cache[case_id] = rag
    return rag

@mcp.tool()
async def get_case_details(case_id: str) -> Dict[str, Any]:
    """Retrieve complete case information including all parties."""
    return _mcp().get_case_details(case_id)


@mcp.tool()
async def get_case_documents(case_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get document file paths, optionally filtered by category."""
    return _mcp().get_case_documents(case_id, category)


@mcp.tool()
async def get_case_timeline(case_id: str, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve chronological events for the case."""
    return _mcp().get_case_timeline(case_id, event_type)


@mcp.tool()
async def get_financial_summary(case_id: str) -> Dict[str, Any]:
    """Calculate total medical expenses, lost wages, and other damages."""
    return _mcp().get_financial_summary(case_id)


@mcp.tool()
async def search_similar_cases(case_type: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """Find precedent cases for reference (toy implementation based on summary keyword overlap)."""
    return _mcp().search_similar_cases(case_type, keywords)


@mcp.tool()
async def get_party_details(case_id: str, party_type: str) -> List[Dict[str, Any]]:
    """Get specific party information (plaintiff, defendant, etc.)."""
    return _mcp().get_party_details(case_id, party_type)


@mcp.tool()
async def search_citations(case_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
    """RAG-backed search over case documents. Returns list of citation dicts with source, page, and snippet.

    query: natural language query (e.g., 'police report description of collision', 'Dr. Jones medical bills')
    k: number of top results
    """
    rag = _get_rag(case_id)
    results = rag.search(query=query, k=k)
    citations: List[Dict[str, Any]] = []
    for chunk, score in results:
        # Compose a short snippet
        snippet = chunk.text[:400].strip()
        citations.append({
            "source": chunk.cite(),
            "page": chunk.page,
            "snippet": snippet,
        })
    return citations

if __name__ == "__main__":
    mcp.run(transport="stdio")