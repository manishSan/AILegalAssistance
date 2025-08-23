from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(..., description="Document name or source title")
    page: Optional[int] = Field(None, description="Page number in the source, if applicable")
    snippet: str = Field(..., description="Short supporting quote or reference text")


class Header(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str = Field(..., description="ISO or human-readable date string")
    to: str = Field(..., description="Recipient line (e.g., insurance company or claims department)")
    case_id: str = Field(..., description="Case identifier")
    case_type: str = Field(..., description="Case type, e.g., Personal Injury")


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str
    citations: List[Citation] = Field(default_factory=list)


class Damages(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medical_expenses: float = Field(..., ge=0)
    lost_wages: float = Field(..., ge=0)
    total_economic: float = Field(..., ge=0)


class DemandInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: float = Field(..., ge=0)
    rationale: str


class DemandLetter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    header: Header
    introduction: Section
    liability: Section
    injuries_treatment: Section
    economic_damages: Damages
    non_economic_damages: Section
    demand: DemandInfo
    citations: List[Citation] = Field(default_factory=list)
