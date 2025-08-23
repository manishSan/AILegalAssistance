from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

# Try imports for different SDK layouts
try:  # Preferred
    from mcp.server import Server
    try:
        from mcp.server.stdio import stdio_server as stdio_transport  # type: ignore
    except Exception:  # older/newer variants
        from mcp.server.stdio import stdio_transport  # type: ignore
except Exception:  # Fallback to package name used on PyPI
    from modelcontextprotocol.server import Server  # type: ignore
    from modelcontextprotocol.server.stdio import stdio_transport  # type: ignore

from .mcp import MCP as MCPData


def _mcp() -> MCPData:
    # Limit to the default sample case; clients can pass other case_ids to methods
    return MCPData()


server = Server("legal-case-mcp")


@server.tool()
async def get_case_details(case_id: str) -> Dict[str, Any]:
    """Retrieve complete case information including all parties."""
    return _mcp().get_case_details(case_id)


@server.tool()
async def get_case_documents(case_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get document file paths, optionally filtered by category."""
    return _mcp().get_case_documents(case_id, category)


@server.tool()
async def get_case_timeline(case_id: str, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve chronological events for the case."""
    return _mcp().get_case_timeline(case_id, event_type)


@server.tool()
async def get_financial_summary(case_id: str) -> Dict[str, Any]:
    """Calculate total medical expenses, lost wages, and other damages."""
    return _mcp().get_financial_summary(case_id)


@server.tool()
async def search_similar_cases(case_type: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """Find precedent cases for reference (toy implementation based on summary keyword overlap)."""
    return _mcp().search_similar_cases(case_type, keywords)


@server.tool()
async def get_party_details(case_id: str, party_type: str) -> List[Dict[str, Any]]:
    """Get specific party information (plaintiff, defendant, etc.)."""
    return _mcp().get_party_details(case_id, party_type)


async def amain() -> None:
    transport = await stdio_transport()
    await server.run(transport)


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
