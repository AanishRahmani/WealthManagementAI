from pathlib import Path
import re
from typing import Any

from app.core.sqlite_db import (
    get_uploaded_files_by_client,
)

from app.core.chroma_db import (
    get_documents_by_file,
)

from app.services.file_parser import (
    parse_portfolio_csv,
    parse_portfolio_excel,
)

from app.services.analytics import (
    asset_allocation,
    sector_exposure,
    diversification_score,
)


def extract_holdings_from_text(
    docs: list[str],
) -> list[dict[str, Any]]:
    holdings = []

    pattern = re.compile(
        r"([A-Z]{2,5}).*?(\d+(?:\.\d+)?)",
        re.I,
    )

    for doc in docs:
        lines = doc.splitlines()

        for line in lines:
            match = pattern.search(line)

            if not match:
                continue

            ticker = match.group(1).upper()
            value = float(match.group(2))

            holdings.append(
                {
                    "ticker": ticker,
                    "value": value,
                    "sector": "Unknown",
                    "asset_class": "Stocks",
                }
            )

    return holdings


def load_client_holdings(
    client_id: int,
) -> tuple[list[dict[str, Any]], int]:
    files = get_uploaded_files_by_client(client_id)

    holdings: list[dict[str, Any]] = []
    documents_analyzed = 0

    for file in files:
        filepath = file["filepath"]
        ext = Path(filepath).suffix.lower()

        try:
            if ext == ".csv":
                rows = parse_portfolio_csv(filepath)

                holdings.extend(rows)
                documents_analyzed += 1

            elif ext in {
                ".xlsx",
                ".xls",
            }:
                rows = parse_portfolio_excel(filepath)

                holdings.extend(rows)
                documents_analyzed += 1

            else:
                result = get_documents_by_file(file["id"])

                docs = result.get(
                    "documents",
                    [],
                )

                parsed = extract_holdings_from_text(docs)

                holdings.extend(parsed)
                documents_analyzed += len(docs)

        except Exception:
            continue

    return holdings, documents_analyzed


def run_portfolio_agent(
    client_id: int,
) -> dict[str, Any]:
    holdings, docs_count = load_client_holdings(client_id)

    if not holdings:
        holdings = [
            {
                "ticker": "CASH",
                "value": 10000.0,
                "sector": "Cash",
                "asset_class": "Cash",
            }
        ]

    asset_classes = {h["asset_class"] for h in holdings}

    return {
        "documents_analyzed": docs_count,
        "holdings_identified": len(holdings),
        "asset_classes_detected": len(asset_classes),
        "allocation": asset_allocation(holdings),
        "sector_exposure": sector_exposure(holdings),
        "diversification_score": diversification_score(holdings),
        "holdings": holdings,
    }
