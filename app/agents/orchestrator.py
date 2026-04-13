from app.services.assessment_engine import (
    generate_profile,
)

from app.agents.portfolio_agent import (
    run_portfolio_agent,
)

from app.agents.risk_agent import (
    run_risk_agent,
)

from app.agents.recommendation_agent import (
    run_recommendation_agent,
)

from app.core.sqlite_db import client_exists


def run_full_analysis(
    client_id: int,
) -> dict:

    if not client_exists(client_id):
        raise ValueError("Client does not exist.")
    profile = generate_profile(client_id)

    portfolio = run_portfolio_agent(client_id)

    risk = run_risk_agent(
        profile,
        portfolio,
    )

    recommendation = run_recommendation_agent(
        profile,
        portfolio,
        risk,
    )

    return {
        "profile": profile,
        "portfolio_analysis": portfolio,
        "risk_analysis": risk,
        "recommendations": recommendation,
    }
