from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .mcp import MCP
from .rag import SimpleRAG, Chunk
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem


@dataclass
class Citation:
    source: str
    snippet: str


def _pick_best(rag: SimpleRAG, prompt: str, k: int = 3) -> List[Citation]:
    hits = rag.search(prompt, k=k)
    cits: List[Citation] = []
    for ch, _score in hits:
        snippet = ch.text
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        cits.append(Citation(source=ch.cite(), snippet=snippet))
    return cits


def render_demand_letter(case_id: str, mcp: MCP, rag: SimpleRAG, out_path: Path) -> Path:
    case_details = mcp.get_case_details(case_id)
    case = case_details.get("case", {})
    parties = case_details.get("parties", [])
    plaintiff = next((p for p in parties if p.get("party_type") == "plaintiff"), None)
    defendant_ic = next((p for p in parties if p.get("party_type") == "insurance_company"), None)
    defendant = next((p for p in parties if p.get("party_type") == "defendant"), None)

    fin = mcp.get_financial_summary(case_id)
    timeline = mcp.get_case_timeline(case_id)

    # RAG lookups
    med_citations = _pick_best(rag, "medical treatment expenses diagnosis Dr. Jones", k=3)
    wage_citations = _pick_best(rag, "wage statements income loss weeks off work", k=2)
    liability_citations = _pick_best(rag, "police report fault determination citations accident details", k=2)
    pain_suffering_citations = _pick_best(rag, "pain suffering impairment permanent partial impairment", k=2)

    env = Environment(
        loader=FileSystemLoader(str(Path("templates"))),
        autoescape=select_autoescape()
    )
    tmpl = env.get_template("demand_letter.j2")

    content = tmpl.render(
        case=case,
        plaintiff=plaintiff,
        defendant=defendant,
        defendant_ic=defendant_ic,
        financials=fin,
        timeline=timeline,
        med_citations=med_citations,
        wage_citations=wage_citations,
        liability_citations=liability_citations,
        pain_suffering_citations=pain_suffering_citations,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return out_path


def render_demand_letter_pdf(case_id: str, mcp: MCP, rag: SimpleRAG, out_path: Path) -> Path:
    case_details = mcp.get_case_details(case_id)
    case = case_details.get("case", {})
    parties = case_details.get("parties", [])
    plaintiff = next((p for p in parties if p.get("party_type") == "plaintiff"), None)
    defendant_ic = next((p for p in parties if p.get("party_type") == "insurance_company"), None)
    defendant = next((p for p in parties if p.get("party_type") == "defendant"), None)

    fin = mcp.get_financial_summary(case_id)
    timeline = mcp.get_case_timeline(case_id)

    med_citations = _pick_best(rag, "medical treatment expenses diagnosis Dr. Jones", k=3)
    wage_citations = _pick_best(rag, "wage statements income loss weeks off work", k=2)
    liability_citations = _pick_best(rag, "police report fault determination citations accident details", k=2)
    pain_suffering_citations = _pick_best(rag, "pain suffering impairment permanent partial impairment", k=2)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="Title",
        parent=styles["Heading1"],
        alignment=1,
        spaceAfter=12,
        fontSize=16,
        leading=20,
    )
    section_style = ParagraphStyle(
        name="Section",
        parent=styles["Heading2"],
        spaceBefore=12,
        spaceAfter=6,
        fontSize=12,
    )
    normal_style = styles["BodyText"]
    small_style = ParagraphStyle(name="Small", parent=normal_style, fontSize=9, leading=11)

    doc = SimpleDocTemplate(str(out_path), pagesize=LETTER, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    story: List = []

    # Header
    story.append(Paragraph("DEMAND LETTER", title_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(f"Date: {case.get('date_filed', '')}", normal_style))
    to_line = defendant_ic.get('name') if defendant_ic else (defendant.get('name') if defendant else 'Claims Department')
    story.append(Paragraph(f"To: {to_line}", normal_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(f"Re: Claim for Damages – Case {case.get('case_id', '')} ({case.get('case_type', '')})", normal_style))
    story.append(Spacer(1, 0.2 * inch))

    lead = (
        f"Please accept this demand letter on behalf of our client, {plaintiff.get('name') if plaintiff else 'the Plaintiff'}, "
        f"arising from the motor vehicle collision that occurred on {timeline[0]['event_date'] if timeline else 'the accident date'}. "
        "Liability is clear based on the police report and admissions by the defendant."
    )
    story.append(Paragraph(lead, normal_style))

    # Sections
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Facts and Liability", section_style))
    story.append(Paragraph("According to the police report and witness statements, liability rests with the defendant.", normal_style))
    story.append(Spacer(1, 0.1 * inch))

    li_items = []
    for c in liability_citations:
        li_items.append(ListItem(Paragraph(f"<b>{c.source}</b>: {c.snippet}", small_style)))
    if li_items:
        story.append(ListFlowable(li_items, bulletType='bullet'))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Injuries and Medical Treatment", section_style))
    story.append(Paragraph("Our client suffered injuries including those diagnosed and treated by Dr. Jones. Medical expenses and treatment chronology are summarized below.", normal_style))
    story.append(Spacer(1, 0.1 * inch))
    med_items = [ListItem(Paragraph(f"<b>{c.source}</b>: {c.snippet}", small_style)) for c in med_citations]
    if med_items:
        story.append(ListFlowable(med_items, bulletType='bullet'))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Wage Loss", section_style))
    story.append(Paragraph("Our client missed time from work and incurred lost wages.", normal_style))
    wage_items = [ListItem(Paragraph(f"<b>{c.source}</b>: {c.snippet}", small_style)) for c in wage_citations]
    if wage_items:
        story.append(ListFlowable(wage_items, bulletType='bullet'))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Pain and Suffering", section_style))
    story.append(Paragraph("Our client experienced pain, limitations in activities of daily living, and ongoing symptoms.", normal_style))
    pain_items = [ListItem(Paragraph(f"<b>{c.source}</b>: {c.snippet}", small_style)) for c in pain_suffering_citations]
    if pain_items:
        story.append(ListFlowable(pain_items, bulletType='bullet'))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Damages Summary", section_style))
    data = [
        ["Medical expenses (known)", f"${fin['total_medical']:.2f}"],
        ["Lost wages (known)", f"${fin['lost_wages']:.2f}"],
        ["Total economic damages (known)", f"${fin['total_known']:.2f}"],
    ]
    tbl = Table(data, colWidths=[3.5 * inch, 2.0 * inch])
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ]))
    story.append(tbl)

    story.append(Spacer(1, 0.2 * inch))
    demand_amount = fin["total_known"] * 3 if fin.get("total_known") else 35000
    story.append(Paragraph("Demand", section_style))
    story.append(Paragraph(
        f"In light of the clear liability and the documented damages, we hereby demand a settlement in the amount of ${demand_amount:.2f}. "
        "This figure reflects medical expenses, lost wages, and a reasonable sum for pain and suffering given the injuries and impairment.",
        normal_style,
    ))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "Please respond within 15 days from the date of this letter. If we do not receive a timely response, we will proceed accordingly, including filing a lawsuit to protect our client’s rights.",
        normal_style,
    ))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Sincerely,", normal_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Attorney for Plaintiff", normal_style))

    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("Citations Index", section_style))
    for title, coll in (
        ("Liability", liability_citations),
        ("Medical", med_citations),
        ("Wage", wage_citations),
        ("Pain & Suffering", pain_suffering_citations),
    ):
        story.append(Paragraph(title, ParagraphStyle(name="Sub", parent=normal_style, spaceBefore=6, spaceAfter=3, fontName="Helvetica-Bold")))
        items = [ListItem(Paragraph(f"<b>{c.source}</b>", small_style)) for c in coll]
        if items:
            story.append(ListFlowable(items, bulletType='bullet'))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)
    return out_path
