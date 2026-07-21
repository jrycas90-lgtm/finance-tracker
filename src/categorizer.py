"""
categorizer.py

Loads keyword-based categorization rules from a YAML config file and
assigns a category to each transaction based on its description.
"""

from __future__ import annotations
import yaml
from pathlib import Path
from typing import Dict, List


class Categorizer:
    """Categorizes transaction descriptions using keyword matching rules."""

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self._rules: Dict[str, List[str]] = {}
        self._default_category = "Uncategorized"
        self._load_rules()

    def _load_rules(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Category config not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)

        if not data or "categories" not in data:
            raise ValueError("Config file must contain a top-level 'categories' key")

        self._rules = {
            category: [kw.lower() for kw in keywords]
            for category, keywords in data["categories"].items()
        }
        self._default_category = data.get("default_category", "Uncategorized")

    def categorize(self, description: str) -> str:
        """Return the matched category for a transaction description.

        Matching is case-insensitive substring search. The first category
        (in config file order) with a matching keyword wins.
        """
        text = description.lower()
        for category, keywords in self._rules.items():
            if any(keyword in text for keyword in keywords):
                return category
        return self._default_category

    @property
    def known_categories(self) -> List[str]:
        return list(self._rules.keys()) + [self._default_category]
