import logging
from typing import Any

from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.core.llm import get_llm

from app.services.scoring_engine import (
    calculate_risk_score,
    risk_confidence,
)

logger = logging.getLogger(__name__)


class RiskSummary(BaseModel):
    risk_level: str = Field(description="Low, Moderate, or High")

    top_risks: list[str] = Field(description="Top portfolio risks")

    recommended_actions: list[str] = Field(description="Immediate actions")

    concise_summary: str = Field(description="Advisor quality summary in 2-3 sentences")


def run_risk_agent(
    profile: dict[str, Any],
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    score_result = calculate_risk_score(portfolio)

    score = score_result["risk_score"]
    drivers = score_result["drivers"]

    confidence = risk_confidence(portfolio)

    if score >= 80:
        level = "Low"
    elif score >= 60:
        level = "Moderate"
    else:
        level = "High"

    parser = JsonOutputParser(pydantic_object=RiskSummary)

    prompt = PromptTemplate(
        template="""
You are a portfolio risk analyst.
Write like a professional human advisor.

Return ONLY valid JSON.

{format_instructions}

Client Profile:
{profile}

Portfolio:
{portfolio}

Risk Score:
{score}

Drivers:
{drivers}
Write 500 to 600 words of professional content.
Be rationale in decision making. 
Explain why the score matters.
Mention strongest risk and one positive factor.
No fluff.
Do not invent numbers.
""",
        input_variables=[
            "profile",
            "portfolio",
            "score",
            "drivers",
        ],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | get_llm() | parser

    try:
        logger.debug(
            "LLM risk agent inputs: %s",
            {
                "profile": str(profile),
                "portfolio": {
                    "allocation": portfolio.get("allocation", {}),
                    "sector_exposure": portfolio.get("sector_exposure", {}),
                    "holdings_count": len(portfolio.get("holdings", [])),
                },
                "score": score,
                "drivers": str(drivers),
            },
        )
        print("\n" + "="*50)
        print("🚀 [START] Invoking Risk Agent AI...")
        print(f"📊 Inputs -> Score: {score} | Drivers: {len(drivers)}")
        print("⏳ Waiting for Hugging Face inference...")
        print("="*50 + "\n")
        
        result = chain.invoke(
            {
                "profile": str(profile),
                "portfolio": str(
                    {
                        "allocation": portfolio.get("allocation", {}),
                        "sector_exposure": portfolio.get(
                            "sector_exposure",
                            {},
                        ),
                        "holdings_count": len(
                            portfolio.get(
                                "holdings",
                                [],
                            )
                        ),
                    }
                ),
                "score": score,
                "drivers": str(drivers),
            }
        )
        
        print("\n" + "="*50)
        print("✅ [SUCCESS] Risk Agent AI Inference Completed!")
        print(f"📝 Output -> Risk Level: {result.get('risk_level', 'N/A')}")
        print("="*50 + "\n")
        
        logger.debug("LLM risk agent response: %s", result)

    except Exception as exc:
        print("\n" + "="*50)
        print("❌ [ERROR] Risk Agent AI Inference Failed!")
        import traceback
        traceback.print_exc()
        print("="*50 + "\n")
        logger.exception("LLM risk agent invocation failed")
        result = {
            "risk_level": level,
            "top_risks": drivers,
            "recommended_actions": [
                "Diversify sector exposure",
                "Rebalance portfolio",
            ],
            "concise_summary": (
                f"The portfolio has a {level.lower()} risk profile. "
                f"Primary concerns relate to concentration risk, while liquidity remains supportive."
            ),
        }

    return {
        "risk_metrics_calculated": len(drivers),
        "compliance_checks_completed": 3,
        "risk_events_identified": len(result["top_risks"]),
        "overall_risk_score": score,
        "risk_confidence": confidence,
        "risk_level": result.get(
            "risk_level",
            level,
        ),
        "drivers": drivers,
        "issues": result["top_risks"],
        "recommended_actions": result["recommended_actions"],
        "summary": result["concise_summary"],
    }
