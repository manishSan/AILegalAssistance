from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from .case_data import CaseData
from .rag import SimpleRAG
import logging

mcp = FastMCP("Legal Case MCP (SSE)")
logger = logging.getLogger("app.mcp_server")

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
        # rag.build_page_embedding(documents=docs, project_root=Path.cwd())
        rag.build_fixed_chunk_embedding(documents=docs, project_root=Path.cwd())
        _rag_cache[case_id] = rag
    return rag

@mcp.tool(description="get case details given a case id")
async def get_case_details(case_id: str) -> Dict[str, Any]:
    """Retrieve complete case information including all parties."""
    logger.info(f"Retrieving case details for case {case_id}")
    return _mcp().get_case_details(case_id)


@mcp.tool(description="Get case documents given a case id")
async def get_case_documents(case_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get document file paths, optionally filtered by category."""
    logger.info(f"Retrieving case documents for case {case_id}")
    return _mcp().get_case_documents(case_id, category)


@mcp.tool(description="Returns the case timeline given a case_id")
async def get_case_timeline(case_id: str, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve chronological events for the case."""
    logger.info(f"Retrieving case timeline for case {case_id}")
    return _mcp().get_case_timeline(case_id, event_type)

# @mcp.tool()
# async def search_similar_cases(case_type: str, keywords: List[str]) -> List[Dict[str, Any]]:
#     """Find precedent cases for reference (toy implementation based on summary keyword overlap)."""
#     logger.info(f"Searching similar cases for {case_type}")
#     return _mcp().search_similar_cases(case_type, keywords)


@mcp.tool(description="Get detail about the parties involved based on case id. Accepted values for party_type are ['plaintiff', 'defendant', 'witness', 'insurance_company']")
async def get_party_details(case_id: str, party_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get specific party information (plaintiff, defendant)."""
    logger.info(f"Retrieving party information for case {case_id}")
    return _mcp().get_parties_data(case_id, party_type)


@mcp.tool(description="""RAG-backed search over case documents. Returns list of citation dicts with source, page, and snippet.
    Here are some examples 
    - police report description of collision
    - Dr. Jones medical bills
    - wage loss documentation
    - pain and suffering description
    - Employment records
    - Expert medical reports  
""")
async def search_citations(case_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
    """RAG-backed search over case documents. Returns list of citation dicts with source, page, and snippet.

    query: natural language query (e.g., 'police report description of collision', 'Dr. Jones medical bills')
    k: number of top results
    """
    logger.info(f"Searching citations for case {case_id}")
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