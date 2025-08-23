import argparse
from pathlib import Path

from app.mcp import MCP
from app.rag import SimpleRAG
from app.generator import render_demand_letter, render_demand_letter_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Legal AI Document Generator")
    parser.add_argument("command", choices=["generate-demand", "generate-demand-pdf"], help="Action to perform")
    parser.add_argument("--case", dest="case_id", default="2024-PI-001", help="Case ID")
    parser.add_argument("--out", dest="out", default=None, help="Output file path")
    args = parser.parse_args()

    case_id = args.case_id
    default_name = (
        f"demand_letter_{case_id}.pdf" if args.command == "generate-demand-pdf" else f"demand_letter_{case_id}.txt"
    )
    out_path = Path(args.out) if args.out else Path("outputs") / default_name

    # Initialize MCP (reads from database_setup_sample.sql)
    mcp = MCP(case_filter=case_id)

    # Build RAG index from case documents
    docs = mcp.get_case_documents(case_id)
    rag = SimpleRAG()
    rag.build(docs, project_root=Path.cwd())

    # Generate demand letter
    if args.command == "generate-demand-pdf":
        out = render_demand_letter_pdf(case_id, mcp, rag, out_path)
    else:
        out = render_demand_letter(case_id, mcp, rag, out_path)
    print(f"Generated: {out}")


if __name__ == "__main__":
    main()
