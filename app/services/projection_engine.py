from typing import Any


def future_value(
    principal: float,
    annual_rate: float,
    years: int,
) -> float:
    return principal * ((1 + annual_rate) ** years)


def generate_projection(
    portfolio: dict[str, Any],
    years: int = 10,
) -> dict[str, Any]:
    holdings = portfolio.get("holdings", [])

    principal = sum(h["value"] for h in holdings)

    low_rate = 0.04
    base_rate = 0.08
    high_rate = 0.12

    low = future_value(
        principal,
        low_rate,
        years,
    )

    base = future_value(
        principal,
        base_rate,
        years,
    )

    high = future_value(
        principal,
        high_rate,
        years,
    )

    return {
        "current_value": round(principal, 2),
        "years": years,
        "low": round(low, 2),
        "base": round(base, 2),
        "high": round(high, 2),
        "assumptions": {
            "low": "4% annualized conservative return",
            "base": "8% annualized diversified portfolio return",
            "high": "12% annualized strong market scenario",
        },
        "note": "Illustrative only. Not guaranteed returns.",
    }
