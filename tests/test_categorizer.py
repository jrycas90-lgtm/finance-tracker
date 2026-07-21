"""
Unit tests for the Categorizer class.

Run with: pytest tests/
"""

import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from categorizer import Categorizer

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "categories.yaml"


@pytest.fixture
def categorizer():
    return Categorizer(CONFIG_PATH)


def test_matches_groceries(categorizer):
    assert categorizer.categorize("WALMART SUPERCENTER #1234") == "Groceries"


def test_matches_subscriptions_case_insensitive(categorizer):
    assert categorizer.categorize("netflix.com") == "Subscriptions"


def test_matches_dining(categorizer):
    assert categorizer.categorize("DOORDASH*CHIPOTLE") == "Dining Out"


def test_unmatched_falls_back_to_default(categorizer):
    assert categorizer.categorize("SOME RANDOM MERCHANT XYZ") == "Uncategorized"


def test_income_category(categorizer):
    assert categorizer.categorize("Direct Deposit PAYROLL") == "Income"


def test_missing_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Categorizer(tmp_path / "does_not_exist.yaml")
