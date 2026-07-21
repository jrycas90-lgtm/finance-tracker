"""
tracker.py

Personal Finance Tracker - CLI entry point.

Reads a bank/credit-card transaction CSV, categorizes each transaction using
keyword rules defined in config/categories.yaml, and produces:
  - A categorized CSV
  - A Markdown summary report
  - Two PNG charts (category breakdown, monthly trend)

Usage:
    python src/tracker.py --input data/sample_transactions.csv --output output/
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

import pandas as pd

# Allow running as `python src/tracker.py` from repo root
sys.path.append(str(Path(__file__).resolve().parent))

from categorizer import Categorizer
import report as reportlib


REQUIRED_COLUMNS = {"date", "description", "amount"}


def load_transactions(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Input CSV is missing required columns: {missing}. "
            f"Expected columns: {REQUIRED_COLUMNS}"
        )

    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    df["amount"] = df["amount"].astype(float)
    df["description"] = df["description"].astype(str)
    return df


def run(input_path: Path, output_dir: Path, config_path: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading transactions from {input_path} ...")
    df = load_transactions(input_path)

    print(f"Applying categorization rules from {config_path} ...")
    categorizer = Categorizer(config_path)
    df["category"] = df["description"].apply(categorizer.categorize)

    categorized_csv_path = output_dir / "categorized_transactions.csv"
    df.to_csv(categorized_csv_path, index=False)
    print(f"Saved categorized transactions -> {categorized_csv_path}")

    uncategorized_count = (df["category"] == "Uncategorized").sum()
    if uncategorized_count:
        print(f"Note: {uncategorized_count} transaction(s) fell into 'Uncategorized'. "
              f"Consider adding keywords to {config_path}.")

    category_totals = reportlib.spending_by_category(df)
    trend = reportlib.monthly_trend(df)
    merchants = reportlib.top_merchants(df, n=5)

    pie_path = output_dir / "category_breakdown.png"
    trend_path = output_dir / "monthly_trend.png"
    reportlib.make_category_pie_chart(category_totals, pie_path)
    reportlib.make_monthly_trend_chart(trend, trend_path)
    print(f"Saved charts -> {pie_path}, {trend_path}")

    report_path = output_dir / "report.md"
    reportlib.write_markdown_report(df, category_totals, trend, merchants, report_path)
    print(f"Saved report -> {report_path}")

    print("\nDone. Top spending categories:")
    print(category_totals.head(5).to_string())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Personal Finance Tracker")
    parser.add_argument(
        "--input", "-i", type=Path, default=Path("data/sample_transactions.csv"),
        help="Path to input transactions CSV (columns: date, description, amount)",
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("output"),
        help="Directory to write categorized CSV, charts, and report",
    )
    parser.add_argument(
        "--config", "-c", type=Path, default=Path("config/categories.yaml"),
        help="Path to categorization rules YAML file",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.input, args.output, args.config)
