from collections import defaultdict


def total_value(holdings: list[dict]) -> float:
    return sum(h["value"] for h in holdings) or 1


def asset_allocation(
    holdings: list[dict],
) -> dict:
    total = total_value(holdings)

    result = defaultdict(float)

    for h in holdings:
        result[h["asset_class"]] += h["value"]

    return {k: round(v / total * 100, 2) for k, v in result.items()}


def sector_exposure(
    holdings: list[dict],
) -> dict:
    total = total_value(holdings)

    result = defaultdict(float)

    for h in holdings:
        result[h["sector"]] += h["value"]

    return {k: round(v / total * 100, 2) for k, v in result.items()}


def diversification_score(
    holdings: list[dict],
) -> int:
    score = 100

    largest = max(h["value"] for h in holdings)
    total = total_value(holdings)

    if (largest / total) * 100 > 20:
        score -= 25

    if len(holdings) < 5:
        score -= 20

    return max(score, 0)
