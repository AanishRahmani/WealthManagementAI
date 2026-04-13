from __future__ import annotations

import json
from typing import Any

from app.core.sqlite_db import get_connection
from app.services.chat_service import get_latest_summary


# Helpers


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert to float.
    """

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(
    value: float,
    low: float = 0.0,
    high: float = 100.0,
) -> float:
    """
    Clamp numeric range.
    """

    return max(low, min(high, value))


def safe_json_loads(
    raw: str | None,
) -> dict[str, Any]:
    """
    Parse JSON safely.
    """

    if not raw:
        return {}

    try:
        parsed = json.loads(raw)

        if isinstance(parsed, dict):
            return parsed

        return {}

    except Exception:
        return {}


# Analysis Report Fetching


def get_latest_analysis_report(
    client_id: int,
) -> dict[str, Any]:
    """
    Return most recent analysis report payload.
    """

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT payload
            FROM analysis_reports
            WHERE client_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (client_id,),
        )

        row = cur.fetchone()

    if row is None:
        return {}

    return safe_json_loads(row["payload"])


def get_all_client_ids() -> list[int]:
    """
    Return distinct client ids from system tables.
    """

    ids: set[int] = set()

    with get_connection() as conn:
        cur = conn.cursor()

        # uploaded files
        cur.execute(
            """
            SELECT DISTINCT client_id
            FROM uploaded_files
            """
        )

        rows = cur.fetchall()

        for row in rows:
            ids.add(int(row["client_id"]))

        # assessments
        cur.execute(
            """
            SELECT DISTINCT client_id
            FROM assessment_answers
            """
        )

        rows = cur.fetchall()

        for row in rows:
            ids.add(int(row["client_id"]))

        # reports
        cur.execute(
            """
            SELECT DISTINCT client_id
            FROM analysis_reports
            """
        )

        rows = cur.fetchall()

        for row in rows:
            ids.add(int(row["client_id"]))

        # chats
        cur.execute(
            """
            SELECT DISTINCT client_id
            FROM chat_sessions
            """
        )

        rows = cur.fetchall()

        for row in rows:
            ids.add(int(row["client_id"]))

    return sorted(ids)


# Score Engines


def calculate_feasibility(
    report: dict[str, Any],
) -> float:
    """
    Higher means easier to implement.
    """

    recommendations = report.get("recommendations", {})

    actions = recommendations.get("actions", [])

    implementation_cost = safe_float(recommendations.get("implementation_cost", 0))

    portfolio = report.get("portfolio_analysis", {})

    allocation = portfolio.get("allocation", {})

    cash_pct = safe_float(allocation.get("Cash", 0))

    score = 100.0

    # more actions = harder
    score -= len(actions) * 8

    # cost drag
    score -= implementation_cost / 8

    # liquidity helps
    score += min(cash_pct, 15)

    return round(clamp(score), 2)


def calculate_impact(
    report: dict[str, Any],
) -> float:
    """
    Higher means better expected benefit.
    """

    recommendations = report.get("recommendations", {})

    risk = report.get("risk_analysis", {})

    expected_return = safe_float(
        recommendations.get(
            "expected_return_improvement",
            0,
        )
    )

    risk_score = safe_float(risk.get("overall_risk_score", 50))

    actions = recommendations.get("actions", [])

    score = 40.0

    score += expected_return * 18
    score += len(actions) * 7

    # more room for improvement if risk is weaker
    score += (100 - risk_score) * 0.20

    return round(clamp(score), 2)


def get_feasibility_label(
    score: float,
) -> str:
    if score >= 75:
        return "Green"

    if score >= 50:
        return "Amber"

    return "Red"


def get_impact_label(
    score: float,
) -> str:
    if score >= 75:
        return "Green"

    if score >= 50:
        return "Amber"

    return "Red"


def get_decision(
    feasibility: float,
    impact: float,
) -> str:
    """
    Final recommendation badge.
    """

    if feasibility >= 70 and impact >= 70:
        return "Implement"

    if impact >= 70:
        return "Strategic Review"

    if feasibility >= 70:
        return "Quick Win"

    return "Monitor"


# Portfolio Metrics


def get_three_year_projection(
    report: dict[str, Any],
) -> float:
    """
    Approximate 3Y value from 10Y base projection.
    """

    recommendations = report.get("recommendations", {})

    projection = recommendations.get("projection", {})

    current_value = safe_float(projection.get("current_value", 0))

    if current_value <= 0:
        return 0.0

    # use 8% annualized
    projected = current_value * (1.08**3)

    return round(projected, 2)


# Single Client Dashboard


def get_client_dashboard(
    client_id: int,
) -> dict[str, Any]:
    """
    Full dashboard payload for one client.
    """

    report = get_latest_analysis_report(client_id)

    if not report:
        return {
            "client_id": client_id,
            "has_analysis": False,
            "latest_chat_summary": get_latest_summary(client_id),
        }

    recommendations = report.get("recommendations", {})
    risk = report.get("risk_analysis", {})

    feasibility = calculate_feasibility(report)
    impact = calculate_impact(report)

    return {
        "client_id": client_id,
        "has_analysis": True,
        "latest_chat_summary": get_latest_summary(client_id),
        "risk_score": safe_float(risk.get("overall_risk_score", 0)),
        "feasibility_score": feasibility,
        "feasibility_label": get_feasibility_label(feasibility),
        "impact_score": impact,
        "impact_label": get_impact_label(impact),
        "decision": get_decision(feasibility, impact),
        "projected_annual_return": safe_float(
            recommendations.get(
                "expected_return_improvement",
                0,
            )
        ),
        "projected_value_3y": get_three_year_projection(report),
        "implementation_cost": safe_float(
            recommendations.get(
                "implementation_cost",
                0,
            )
        ),
        "tax_implications": safe_float(
            recommendations.get(
                "tax_efficiency_gain",
                0,
            )
        ),
        "risk_adjusted_return_improvement": round(
            safe_float(
                recommendations.get(
                    "expected_return_improvement",
                    0,
                )
            )
            * 0.75,
            2,
        ),
        "agent_findings": {
            "portfolio": report.get("portfolio_analysis", {}),
            "risk": report.get("risk_analysis", {}),
            "recommendations": recommendations,
        },
    }


# Multi Client Dashboard Table


def get_all_clients_dashboard() -> list[dict[str, Any]]:
    """
    Dashboard rows for all clients.
    """

    client_ids = get_all_client_ids()

    rows: list[dict[str, Any]] = []

    for client_id in client_ids:
        dashboard = get_client_dashboard(client_id)

        rows.append(
            {
                "client_id": client_id,
                "decision": dashboard.get(
                    "decision",
                    "N/A",
                ),
                "feasibility_score": dashboard.get(
                    "feasibility_score",
                    0,
                ),
                "impact_score": dashboard.get(
                    "impact_score",
                    0,
                ),
                "projected_annual_return": dashboard.get(
                    "projected_annual_return",
                    0,
                ),
                "implementation_cost": dashboard.get(
                    "implementation_cost",
                    0,
                ),
                "risk_score": dashboard.get(
                    "risk_score",
                    0,
                ),
                "has_analysis": dashboard.get(
                    "has_analysis",
                    False,
                ),
            }
        )

    rows.sort(
        key=lambda item: (
            item["impact_score"],
            item["feasibility_score"],
        ),
        reverse=True,
    )

    return rows


# Scatter Matrix Data


def get_matrix_points() -> list[dict[str, Any]]:
    """
    Points for feasibility-impact scatter chart.
    """

    dashboards = get_all_clients_dashboard()

    points: list[dict[str, Any]] = []

    for row in dashboards:
        points.append(
            {
                "client_id": row["client_id"],
                "x": row["feasibility_score"],
                "y": row["impact_score"],
                "decision": row["decision"],
                "label": (
                    f"Client {row['client_id']} | "
                    f"F:{row['feasibility_score']} "
                    f"I:{row['impact_score']}"
                ),
            }
        )

    return points
