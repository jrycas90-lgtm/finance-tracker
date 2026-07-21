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


def make_category_pie_chart(category_totals: pd.Series, output_path: Path) -> None:
    plt.figure(figsize=(7, 7))
    plt.pie(category_totals.values, labels=category_totals.index, autopct="%1.1f%%", startangle=90)
    plt.title("Spending by Category")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
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
