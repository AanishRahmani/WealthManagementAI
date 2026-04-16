from typing import Any

from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

import logging

from app.core.llm import get_llm
from app.services.projection_engine import (
    generate_projection,
)



logger = logging.getLogger(__name__)



class RecommendationSummary(BaseModel):
    strategy_focus: str = Field(description="Primary strategy focus")

    top_actions: list[str] = Field(description="Prioritized recommendations")

    concise_summary: str = Field(description="Advisor quality recommendation summary")


def build_ranked_actions(
    portfolio: dict[str, Any],
    risk: dict[str, Any],
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []

    sector = portfolio.get(
        "sector_exposure",
        {},
    )

    allocation = portfolio.get(
        "allocation",
        {},
    )

    tech = sector.get(
        "Technology",
        0,
    )

    bond = allocation.get(
        "Bond",
        0,
    )

    cash = allocation.get(
        "Cash",
        0,
    )

    diversification = portfolio.get(
        "diversification_score",
        50,
    )

    risk_score = risk.get(
        "overall_risk_score",
        50,
    )

    if tech > 40:
        ranked.append(
            {
                "priority": 1,
                "action": "Reduce technology concentration",
                "reason": (
                    f"Technology exposure is {tech:.2f}% "
                    "which increases sector concentration risk."
                ),
            }
        )

    if bond < 10:
        ranked.append(
            {
                "priority": 2,
                "action": "Increase bond allocation",
                "reason": (
                    f"Bond allocation is {bond:.2f}% "
                    "which may weaken downside protection."
                ),
            }
        )

    if cash < 5:
        ranked.append(
            {
                "priority": 3,
                "action": "Increase liquidity reserve",
                "reason": (
                    f"Cash allocation is {cash:.2f}% "
                    "which may reduce short-term flexibility."
                ),
            }
        )

    if diversification < 70:
        ranked.append(
            {
                "priority": 4,
                "action": "Broaden diversification",
                "reason": (
                    f"Diversification score is {diversification:.0f}, "
                    "indicating room for broader exposure."
                ),
            }
        )

    if risk_score <= 70:
        ranked.append(
            {
                "priority": 5,
                "action": "Rebalance portfolio quarterly",
                "reason": (
                    f"Risk score is {risk_score:.0f}; "
                    "regular rebalancing can maintain target risk levels."
                ),
            }
        )

    if not ranked:
        ranked.append(
            {
                "priority": 1,
                "action": "Maintain current allocation",
                "reason": (
                    "Current allocation appears aligned with "
                    "risk and diversification objectives."
                ),
            }
        )

    ranked.sort(key=lambda x: x["priority"])

    for i, item in enumerate(
        ranked,
        start=1,
    ):
        item["priority"] = i

    return ranked


def run_recommendation_agent(
    profile: dict[str, Any],
    portfolio: dict[str, Any],
    risk: dict[str, Any],
) -> dict[str, Any]:
    ranked_actions = build_ranked_actions(
        portfolio,
        risk,
    )

    action_text = [item["action"] for item in ranked_actions]

    projection = generate_projection(
        portfolio,
        years=10,
    )

    allocation = portfolio.get(
        "allocation",
        {},
    )

    equity = allocation.get(
        "Equity",
        0,
    )

    bond = allocation.get(
        "Bond",
        0,
    )

    risk_score = risk.get(
        "overall_risk_score",
        50,
    )

    imbalance_penalty = abs(equity - 60) + abs(bond - 25)
    expected_return_improvement = round(
        max(
            0.2,
            min(
                3.5,
                imbalance_penalty * 0.03,
            ),
        ),
        2,
    )

    tax_base = (
        0.8
        if profile.get(
            "tax_sensitive",
            False,
        )
        else 0.3
    )

    turnover_penalty = len(ranked_actions) * 0.08

    tax_efficiency_gain = round(
        max(
            0.1,
            min(
                2.0,
                tax_base + turnover_penalty,
            ),
        ),
        2,
    )

    complexity = len(portfolio.get("holdings", [])) * 4

    implementation_cost = round(
        20 + (len(ranked_actions) * 18) + complexity,
        2,
    )

    recommendation_confidence = round(
        min(
            0.95,
            0.55
            + (portfolio.get("documents_analyzed", 0) * 0.08)
            + (len(portfolio.get("holdings", [])) * 0.015)
            + (0.10 if risk_score >= 65 else 0),
        ),
        2,
    )

    parser = JsonOutputParser(pydantic_object=RecommendationSummary)

    prompt = PromptTemplate(
        template="""
You are a professional investment advisor.
Write like a human advisor.

Return ONLY valid JSON.

{format_instructions}

Client Profile:
{profile}

Portfolio:
{portfolio}

Risk:
{risk}

Projection:
{projection}

Actions:
{actions}

Write 2-3 practical advisory sentences.
Explain strategic rationale.
Mention likely improvement areas.
Do not invent unsupported claims.
""",
        input_variables=[
            "profile",
            "portfolio",
            "risk",
            "projection",
            "actions",
        ],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | get_llm() | parser

    try:
        logger.debug(
            "LLM recommendation agent inputs: %s",
            {
                "profile": str(profile),
                "portfolio": {
                    "allocation": allocation,
                    "sector_exposure": portfolio.get("sector_exposure", {}),
                    "diversification_score": portfolio.get(
                        "diversification_score",
                        0,
                    ),
                },
                "risk": {
                    "risk_level": risk.get("risk_level", "Moderate"),
                    "risk_score": risk_score,
                },
                "projection": str(projection),
                "actions": str(action_text),
            },
        )
        result = chain.invoke(
            {
                "profile": str(profile),
                "portfolio": str(
                    {
                        "allocation": allocation,
                        "sector_exposure": portfolio.get(
                            "sector_exposure",
                            {},
                        ),
                        "diversification_score": portfolio.get(
                            "diversification_score",
                            0,
                        ),
                    }
                ),
                "risk": str(
                    {
                        "risk_level": risk.get(
                            "risk_level",
                            "Moderate",
                        ),
                        "risk_score": risk_score,
                    }
                ),
                "projection": str(projection),
                "actions": str(action_text),
            }
        )
        logger.debug("LLM recommendation agent response: %s", result)

    except Exception as exc:
        logger.exception("LLM recommendation agent invocation failed")
        result = {
            "strategy_focus": "Balanced long-term growth",
            "top_actions": action_text,
            "concise_summary": (
                "The portfolio would benefit from improved balance, "
                "lower concentration risk, and disciplined rebalancing."
            ),
        }

    return {
        "recommendations_generated": len(ranked_actions),
        "expected_return_improvement": expected_return_improvement,
        "tax_efficiency_gain": tax_efficiency_gain,
        "implementation_cost": implementation_cost,
        "recommendation_confidence": recommendation_confidence,
        "strategy_focus": result["strategy_focus"],
        "actions": ranked_actions,
        "projection": projection,
        "summary": result["concise_summary"],
    }
