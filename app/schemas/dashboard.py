from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict


# Common / Nested Schemas


class AgentFindings(BaseModel):
    """
    Raw findings returned by stage-3 agents.
    """

    model_config = ConfigDict(extra="forbid")

    portfolio: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] = Field(default_factory=dict)
    recommendations: dict[str, Any] = Field(default_factory=dict)


class MatrixPoint(BaseModel):
    """
    Scatter chart point.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int = Field(..., gt=0)
    x: float = Field(..., ge=0, le=100)
    y: float = Field(..., ge=0, le=100)
    decision: str
    label: str


# Client Dashboard


class ClientDashboardResponse(BaseModel):
    """
    Full dashboard payload for one client.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int = Field(..., gt=0)
    has_analysis: bool

    latest_chat_summary: str = ""

    risk_score: float = Field(default=0, ge=0, le=100)

    feasibility_score: float = Field(default=0, ge=0, le=100)
    feasibility_label: str = ""

    impact_score: float = Field(default=0, ge=0, le=100)
    impact_label: str = ""

    decision: str = ""

    projected_annual_return: float = 0
    projected_value_3y: float = 0
    implementation_cost: float = 0
    tax_implications: float = 0
    risk_adjusted_return_improvement: float = 0

    agent_findings: AgentFindings = Field(default_factory=AgentFindings)


# Multi Client Table Row


class DashboardRowResponse(BaseModel):
    """
    Table row for dashboard listing.
    """

    model_config = ConfigDict(extra="forbid")

    client_id: int = Field(..., gt=0)
    decision: str

    feasibility_score: float = Field(
        default=0,
        ge=0,
        le=100,
    )

    impact_score: float = Field(
        default=0,
        ge=0,
        le=100,
    )

    projected_annual_return: float = 0
    implementation_cost: float = 0
    risk_score: float = 0

    has_analysis: bool
