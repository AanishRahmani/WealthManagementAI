from typing import Any


def clamp(
    value: float,
    low: float = 0,
    high: float = 100,
) -> float:
    return max(low, min(high, value))


# Risk Score


def calculate_risk_score(
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    score = 100.0
    drivers: list[str] = []

    allocation = portfolio.get("allocation", {})
    sector = portfolio.get("sector_exposure", {})
    holdings = portfolio.get("holdings", [])

    # Sector concentration
    max_sector = max(sector.values()) if sector else 0

    if max_sector > 25:
        score -= 20
        drivers.append("Sector concentration above 25%")

    # Single holding concentration
    total = sum(h["value"] for h in holdings) or 1

    max_holding = max(
        ((h["value"] / total) * 100 for h in holdings),
        default=0,
    )

    if max_holding > 10:
        score -= 15
        drivers.append("Single holding above 10%")

    # Equity overweight
    equity = allocation.get("Equity", 0)

    if equity > 80:
        score -= 10
        drivers.append("Equity exposure above 80%")

    # Cash reserve
    cash = allocation.get("Cash", 0)

    if cash >= 10:
        score += 5
        drivers.append("Healthy liquidity buffer")

    # Limited diversification
    if len(holdings) < 8:
        score -= 10
        drivers.append("Limited number of holdings")

    score = clamp(score)

    return {
        "risk_score": round(score, 2),
        "drivers": drivers,
    }


# Diversification Score


def calculate_diversification_score(
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    score = 0.0
    drivers: list[str] = []

    holdings = portfolio.get("holdings", [])
    sectors = portfolio.get("sector_exposure", {})
    allocation = portfolio.get("allocation", {})

    # Holdings count
    n = len(holdings)
    score += min(n * 4, 30)

    if n >= 8:
        drivers.append("Good holding count")

    # Sector spread
    sector_count = len(sectors)
    score += min(sector_count * 5, 30)

    if sector_count >= 5:
        drivers.append("Broad sector exposure")

    # Asset classes
    classes = len(allocation)
    score += min(classes * 10, 30)

    if classes >= 3:
        drivers.append("Multiple asset classes")

    # Cash reserve
    if allocation.get("Cash", 0) >= 5:
        score += 10
        drivers.append("Cash reserve present")

    score = clamp(score)

    return {
        "diversification_score": round(score, 2),
        "drivers": drivers,
    }


# Confidence Score


def risk_confidence(
    portfolio: dict[str, Any],
) -> float:
    score = 0.50

    if len(portfolio.get("holdings", [])) >= 8:
        score += 0.20

    if len(portfolio.get("sector_exposure", {})) >= 5:
        score += 0.15

    if portfolio.get("documents_analyzed", 0) >= 1:
        score += 0.10

    if portfolio.get("asset_classes_detected", 0) >= 3:
        score += 0.05

    return round(min(score, 0.93), 2)
