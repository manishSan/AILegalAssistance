from __future__ import annotations

import asyncio
import os
import json
from pathlib import Path
from typing import Optional

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.model_settings import ModelSettings
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from .schemas import DemandLetter


SYSTEM_PROMPT = (
    "You are a legal assistant that drafts clear, persuasive, and professional personal injury demand letters. "
    "Always ground facts, injuries, treatment, damages, parties, and timeline using the provided MCP tools. "
    "Use the `search_citations` tool to retrieve supporting sources/snippets from case documents and populate the `citations` field. "
    "Return STRICT JSON ONLY that conforms exactly to the provided JSON Schema. No prose outside JSON. "
)


async def _run_agent(case_id: str, out_path: Path, model: Optional[str]) -> Path:
    # Launch MCP server over stdio via uv, importing as a module to preserve package context
    async with MCPServerStdio(
        name="Legal MCP Stdio",
        params={"command": "uv", "args": ["run", "-m", "app.mcp_server"]},
    ) as mcp_server:
        agent = Agent(
            name="Demand Letter Agent",
            instructions=SYSTEM_PROMPT,
            mcp_servers=[mcp_server],
            model_settings=ModelSettings(
                model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.2,
                tool_choice="required",
            ),
            output_type=DemandLetter
        )

        # Provide JSON Schema for strict structured output
        # schema = DemandLetter.model_json_schema()
        example = DemandLetter.md_example()
        prompt = (
            f"Draft a comprehensive demand letter for case {case_id}. "
            "Use MCP tools to retrieve accurate details: parties (get_case_details), documents (get_case_documents), timeline (get_case_timeline), financials (get_financial_summary). "
            "Call `search_citations` with focused queries (e.g., 'police report collision description', 'Dr. Jones medical records', 'wage loss documentation') to gather sources/snippets and populate the `citations` array. "
            "Output MUST be valid JSON conforming to the DemandLetter schema. Do not include any text before or after the JSON."
        )

        prompt += f"Here is an example of DemandLetter - {example}"

        try:
            result = await Runner.run(starting_agent=agent, input=prompt)
            letter = result.final_output
        except Exception as e:
            raise RuntimeError(f"Agent failed to produce output: {e}")
        
        # Extract JSON block
        # try:
        #     start = raw.index("{")
        #     end = raw.rindex("}") + 1
        #     data = json.loads(raw[start:end])
        # except Exception as e:
        #     raise RuntimeError(f"Failed to parse JSON from model output: {e}\nOutput:\n{raw[:2000]}")

        # # Validate against Pydantic model (strict)
        # try:
        #     letter = DemandLetter.model_validate(data)
        # except Exception as e:
        #     raise RuntimeError(f"Model output failed schema validation: {e}")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Render a PDF matching the Sample Demand Letter.md style
        doc = SimpleDocTemplate(
            str(out_path), pagesize=LETTER, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72
        )
        styles = getSampleStyleSheet()
        h1 = ParagraphStyle(name="FirmTitle", parent=styles["Heading1"], alignment=1, fontSize=16, leading=20, spaceAfter=6)
        h2 = ParagraphStyle(name="FirmSub", parent=styles["Heading2"], alignment=1, fontSize=12, leading=14, spaceAfter=2)
        addr = ParagraphStyle(name="Addr", parent=styles["Normal"], alignment=1, fontSize=10, leading=12, spaceAfter=2)
        date_style = ParagraphStyle(name="Date", parent=styles["Normal"], spaceBefore=6, spaceAfter=12)
        section_style = ParagraphStyle(name="Section", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6, fontSize=12)
        normal_style = styles["BodyText"]
        small_style = ParagraphStyle(name="Small", parent=normal_style, fontSize=9, leading=11)
        bold_style = ParagraphStyle(name="Bold", parent=normal_style)

        story = []

        # Firm header (sample style)
        story.append(Paragraph("MARTINEZ & ASSOCIATES, LLP", h1))
        story.append(Paragraph("Personal Injury Attorneys", h2))
        story.append(Paragraph("1247 Broadway, Suite 800", addr))
        story.append(Paragraph("New York, NY 10001", addr))
        story.append(Paragraph("Tel: (212) 555-", addr))
        story.append(Spacer(1, 0.2 * inch))

        # Date
        story.append(Paragraph(f"<b>{letter.header.date}</b>", date_style))

        # Recipient block (allow multi-line in header.to via \n)
        for line in (letter.header.to.split("\n") if letter.header.to else []):
            story.append(Paragraph(line, normal_style))
        story.append(Spacer(1, 0.1 * inch))

        # Reference lines (map from available schema)
        story.append(Paragraph(f"<b>Re:</b> Claim for Damages – Case {letter.header.case_id}", normal_style))
        story.append(Paragraph(f"<b>Case Type:</b> {letter.header.case_type}", normal_style))
        story.append(Spacer(1, 0.15 * inch))

        # Greeting and opening sentence
        story.append(Paragraph("Dear Claims Adjuster:", normal_style))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph(
            "This letter constitutes a demand for settlement in the above-referenced matter.", normal_style
        ))

        # Statement of Facts (from introduction)
        story.append(Paragraph("Statement of Facts", section_style))
        story.append(Paragraph(letter.introduction.body, normal_style))

        # Injuries Sustained (from injuries_treatment)
        story.append(Paragraph("Injuries Sustained", section_style))
        story.append(Paragraph(letter.injuries_treatment.body, normal_style))

        # Damages Claimed (compose numbered items similar to sample)
        story.append(Paragraph("Damages Claimed", section_style))
        med = letter.economic_damages.medical_expenses
        wages = letter.economic_damages.lost_wages
        total_econ = letter.economic_damages.total_economic
        story.append(Paragraph(f"1. <b>Medical Expenses (Known):</b> ${med:,.2f}.", normal_style))
        story.append(Paragraph(f"2. <b>Lost Wages (Known):</b> ${wages:,.2f}.", normal_style))
        story.append(Paragraph(
            f"3. <b>Pain and Suffering / Non-Economic Damages:</b> {letter.non_economic_damages.body}",
            normal_style,
        ))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph(f"<b>Total Economic Damages (Known):</b> ${total_econ:,.2f}.", normal_style))

        # Settlement Demand
        story.append(Paragraph("Settlement Demand", section_style))
        story.append(
            Paragraph(
                f"Based on the clear liability and the documented damages, we demand the sum of <b>${letter.demand.amount:,.2f}</b> to settle this matter in full.",
                normal_style,
            )
        )
        story.append(Paragraph(letter.demand.rationale, normal_style))

        # Liability Analysis
        story.append(Paragraph("Liability Analysis", section_style))
        story.append(Paragraph(letter.liability.body, normal_style))

        # Supporting Documentation (from citations; show sources list)
        if letter.citations:
            story.append(Paragraph("Supporting Documentation", section_style))
            for c in letter.citations:
                src = f"{c.source}{' p.' + str(c.page) if c.page is not None else ''}"
                story.append(Paragraph(f"• {src}", small_style))

        # Time Limit for Response
        story.append(Paragraph("Time Limit for Response", section_style))
        story.append(
            Paragraph(
                "Please respond with a settlement offer within <b>30 days</b> of receipt. If we do not receive a reasonable offer, we will pursue all appropriate legal remedies.",
                normal_style,
            )
        )

        # Closing Statement
        story.append(Paragraph("Closing Statement", section_style))
        story.append(
            Paragraph(
                "We believe this matter can be resolved amicably through reasonable negotiations. Our client deserves fair compensation for the injuries and losses sustained.",
                normal_style,
            )
        )

        # Signature block (sample style)
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Sincerely,", normal_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Robert Martinez, Esq.", normal_style))
        story.append(Paragraph("Senior Partner", normal_style))
        story.append(Paragraph("Martinez & Associates, LLP", normal_style))
        story.append(Paragraph("New York Bar #", normal_style))

        # Enclosures
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("<b>Enclosures:</b> Medical records, police report, witness statements, photographs, employment records, expert reports", small_style))

        doc.build(story)
        return out_path


def generate_demand_letter_llm(case_id: str, out_path: Path, model: Optional[str] = None) -> Path:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")
    return asyncio.run(_run_agent(case_id, out_path, model))
