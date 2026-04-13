from pathlib import Path
from typing import Any

from pypdf import PdfReader
import pandas as pd
import docx


# Basic Text Parsers


def parse_txt(
    path: Path,
) -> str:
    return path.read_text(
        encoding="utf-8",
        errors="ignore",
    )


def parse_pdf(
    path: Path,
) -> str:
    reader = PdfReader(str(path))

    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""

        text = text.strip()

        if text:
            pages.append(text)

    return "\n".join(pages)


def parse_docx(
    path: Path,
) -> str:
    document = docx.Document(str(path))

    lines: list[str] = []

    for para in document.paragraphs:
        text = para.text.strip()

        if text:
            lines.append(text)

    return "\n".join(lines)


# Generic DataFrame -> Semantic Text
# Used for embeddings into Chroma


def dataframe_to_rows(
    df: pd.DataFrame,
) -> str:
    rows: list[str] = []

    for _, row in df.iterrows():
        parts: list[str] = []

        for col in df.columns:
            value = row[col]

            if pd.notna(value):
                parts.append(f"{col}: {value}")

        if parts:
            rows.append(", ".join(parts))

    return "\n".join(rows)


# Generic CSV / Excel Text Parsers
# Used during upload embeddings


def parse_csv(
    path: Path,
) -> str:
    df = pd.read_csv(path)

    df = df.dropna(how="all").dropna(
        axis=1,
        how="all",
    )

    return dataframe_to_rows(df)


def parse_excel(
    path: Path,
) -> str:
    df = pd.read_excel(
        path,
        sheet_name=0,
    )

    df = df.dropna(how="all").dropna(
        axis=1,
        how="all",
    )

    return dataframe_to_rows(df)


# Structured Portfolio Parsers
# Used by Portfolio Agent directly


def parse_portfolio_csv(
    file_path: str,
) -> list[dict[str, Any]]:
    path = Path(file_path)

    df = pd.read_csv(path)

    return portfolio_dataframe_to_rows(df)


def parse_portfolio_excel(
    file_path: str,
) -> list[dict[str, Any]]:
    path = Path(file_path)

    df = pd.read_excel(
        path,
        sheet_name=0,
    )

    return portfolio_dataframe_to_rows(df)


def portfolio_dataframe_to_rows(
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    df.columns = [str(col).strip() for col in df.columns]

    rows: list[dict[str, Any]] = []

    for _, row in df.iterrows():
        ticker = str(
            row.get(
                "Ticker",
                "",
            )
        ).strip()

        if not ticker or ticker == "nan":
            continue

        rows.append(
            {
                "ticker": ticker.upper(),
                "sector": str(
                    row.get(
                        "Sector",
                        "Unknown",
                    )
                ).strip(),
                "asset_class": str(
                    row.get(
                        "Asset_Class",
                        "Unknown",
                    )
                ).strip(),
                "value": safe_float(
                    row.get(
                        "Market_Value",
                        0,
                    )
                ),
            }
        )

    return rows


# Utility


def safe_float(
    value: Any,
) -> float:
    try:
        if pd.isna(value):
            return 0.0

        return float(value)

    except Exception:
        return 0.0


# Main Upload Extractor
# Used by upload endpoint


def extract_text(
    file_path: str,
) -> str:
    path = Path(file_path)

    suffix = path.suffix.lower()

    if suffix == ".txt":
        return parse_txt(path)

    elif suffix == ".pdf":
        return parse_pdf(path)

    elif suffix == ".docx":
        return parse_docx(path)

    elif suffix == ".csv":
        return parse_csv(path)

    elif suffix in {
        ".xlsx",
        ".xls",
    }:
        return parse_excel(path)

    raise ValueError(f"Unsupported file type: {suffix}")
