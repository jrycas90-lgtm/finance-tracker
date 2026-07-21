"""
report.py

Builds summary tables and charts from a categorized transactions DataFrame,
and writes a Markdown report to disk.
"""

from __future__ import annotations
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless-safe backend for scripts/CI
import matplotlib.pyplot as plt
from pathlib import Path


def add_month_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    return df


def spending_by_category(df: pd.DataFrame) -> pd.Series:
    """Total spend (positive numbers) by category, expenses only, sorted descending."""
    expenses = df[df["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()
    return expenses.groupby("category")["amount"].sum().sort_values(ascending=False)


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly income, expenses, and net cash flow."""
    df = add_month_column(df)
    income = df[df["amount"] > 0].groupby("month")["amount"].sum()
    expenses = df[df["amount"] < 0].groupby("month")["amount"].sum().abs()
    trend = pd.DataFrame({"income": income, "expenses": expenses}).fillna(0)
    trend["net"] = trend["income"] - trend["expenses"]
    return trend


def top_merchants(df: pd.DataFrame, n: int = 5) -> pd.Series:
    expenses = df[df["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()
    return expenses.groupby("description")["amount"].sum().sort_values(ascending=False).head(n)


def make_category_pie_chart(category_totals: pd.Series, output_path: Path, min_share: float = 0.03) -> None:
    """Pie chart of spending by category.

    Categories below `min_share` of total spend (default 3%) are grouped into
    an "Other" slice so tiny slivers don't produce overlapping labels.
    Uses a legend rather than on-slice labels to stay readable regardless
    of how many categories there are.
    """
    total = category_totals.sum()
    shares = category_totals / total

    large = category_totals[shares >= min_share]
    small = category_totals[shares < min_share]

    if not small.empty:
        large = pd.concat([large, pd.Series({"Other": small.sum()})])

    fig, ax = plt.subplots(figsize=(8, 7))
    wedges, _, autotexts = ax.pie(
        large.values,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.8,
        textprops={"fontsize": 9},
    )
    ax.set_title("Spending by Category")
    ax.legend(
        wedges,
        [f"{name} (${amount:,.0f})" for name, amount in large.items()],
        title="Category",
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        fontsize=9,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def make_monthly_trend_chart(trend: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(9, 5))
    plt.plot(trend.index, trend["income"], marker="o", label="Income")
    plt.plot(trend.index, trend["expenses"], marker="o", label="Expenses")
    plt.plot(trend.index, trend["net"], marker="o", label="Net", linestyle="--")
    plt.xlabel("Month")
    plt.ylabel("Amount ($)")
    plt.title("Monthly Cash Flow")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def write_markdown_report(
    df: pd.DataFrame,
    category_totals: pd.Series,
    trend: pd.DataFrame,
    merchants: pd.Series,
    output_path: Path,
) -> None:
    total_income = df[df["amount"] > 0]["amount"].sum()
    total_expenses = df[df["amount"] < 0]["amount"].abs().sum()
    net = total_income - total_expenses

    lines = []
    lines.append("# Personal Finance Report\n")
    lines.append(f"**Period:** {df['date'].min()} to {df['date'].max()}\n")
    lines.append("## Summary\n")
    lines.append(f"- Total Income: ${total_income:,.2f}")
    lines.append(f"- Total Expenses: ${total_expenses:,.2f}")
    lines.append(f"- Net Cash Flow: ${net:,.2f}\n")

    lines.append("## Spending by Category\n")
    lines.append("| Category | Total Spent |")
    lines.append("|---|---|")
    for category, amount in category_totals.items():
        lines.append(f"| {category} | ${amount:,.2f} |")
    lines.append("")

    lines.append("## Top 5 Merchants by Spend\n")
    lines.append("| Merchant | Total Spent |")
    lines.append("|---|---|")
    for merchant, amount in merchants.items():
        lines.append(f"| {merchant} | ${amount:,.2f} |")
    lines.append("")

    lines.append("## Monthly Trend\n")
    lines.append("| Month | Income | Expenses | Net |")
    lines.append("|---|---|---|---|")
    for month, row in trend.iterrows():
        lines.append(f"| {month} | ${row['income']:,.2f} | ${row['expenses']:,.2f} | ${row['net']:,.2f} |")
    lines.append("")

    lines.append("![Spending by Category](category_breakdown.png)\n")
    lines.append("![Monthly Trend](monthly_trend.png)\n")

    output_path.write_text("\n".join(lines))
