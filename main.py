import argparse
from pathlib import Path

from app.agent_runner import generate_demand_letter_llm


def main() -> None:
    parser = argparse.ArgumentParser(description="Legal AI Document Generator (LLM-only)")
    parser.add_argument(
        "command",
        choices=["generate-demand-llm"],
        help="Action to perform",
    )
    parser.add_argument("--case", dest="case_id", default="2024-PI-001", help="Case ID")
    parser.add_argument("--out", dest="out", default=None, help="Output file path")
    args = parser.parse_args()

    case_id = args.case_id
    default_name = f"demand_letter_{case_id}.pdf"
    out_path = Path(args.out) if args.out else Path("outputs") / default_name

    # Generate demand letter via LLM (PDF)
    out = generate_demand_letter_llm(case_id, out_path)
    print(f"Generated: {out}")


if __name__ == "__main__":
    main()
