import random
from pathlib import Path

import pytest

from cov_badge import (
    create_badge,
    get_color,
    get_cov_percent,
    get_value_at_path,
    update_badge,
)

THRESHOLDS = [(100, "green"), (80, "orange"), (0, "red")]


def make_readme(tmp_path: Path, lines: list[str]) -> Path:
    readme = tmp_path / "README.md"
    readme.write_text("\n".join(lines) + "\n")
    return readme


class TestUpdateBadge:
    def test_updates_existing_badge(self, tmp_path):
        readme = make_readme(
            tmp_path,
            [
                "### cov-badge",
                "![coverage](https://img.shields.io/badge/coverage-80%25-green)",
            ],
        )
        coverage = random.randint(0, 100)
        update_badge(coverage, THRESHOLDS, str(readme))
        lines = readme.read_text().splitlines()
        assert lines[1].startswith("![coverage]")
        assert str(coverage) in lines[1]

    def test_inserts_after_last_badge(self, tmp_path):
        readme = make_readme(
            tmp_path,
            [
                "### cov-badge",
                "![build](https://img.shields.io/badge/build-passing-blue)",
                "Some description.",
            ],
        )
        coverage = random.randint(0, 100)
        update_badge(coverage, THRESHOLDS, str(readme))
        lines = readme.read_text().splitlines()
        assert lines[2].startswith("![coverage]")
        assert str(coverage) in lines[2]

    def test_inserts_after_title(self, tmp_path):
        readme = make_readme(
            tmp_path,
            [
                "### My Project",
                "Some description.",
            ],
        )
        coverage = random.randint(0, 100)
        update_badge(coverage, THRESHOLDS, str(readme))
        lines = readme.read_text().splitlines()
        assert lines[1].startswith("![coverage]")
        assert str(coverage) in lines[1]

    def test_handles_empty_file(self, tmp_path):
        readme = make_readme(tmp_path, [])
        coverage = random.randint(0, 100)
        update_badge(coverage, THRESHOLDS, str(readme))
        lines = readme.read_text().splitlines()
        assert lines[1].startswith("![coverage]")
        assert str(coverage) in lines[1]


class TestGetCovPercent:
    def test_returns_correct_value(self):
        coverage = random.randint(0, 100)
        obj = {"totals": {"percent_statements_covered_display": str(coverage)}}
        assert (
            get_cov_percent(obj, ["totals", "percent_statements_covered_display"])
            == coverage
        )


class TestGetValueAtPath:
    def test_returns_value(self):
        coverage = random.randint(0, 100)
        obj = {"totals": {"percent_statements_covered_display": str(coverage)}}
        assert get_value_at_path(
            obj, ["totals", "percent_statements_covered_display"]
        ) == str(coverage)

    def test_raises_key_error(self):
        coverage = random.randint(0, 100)
        obj = {"totals": {"percent_statements_covered_display": str(coverage)}}
        with pytest.raises(KeyError):
            get_value_at_path(obj, ["totals", "not_a_key"])

    def test_raises_type_error(self):
        coverage = random.randint(0, 100)
        obj = {"totals": str(coverage)}
        with pytest.raises(TypeError):
            get_value_at_path(obj, ["totals", "percent_statements_covered_display"])


class TestGetColor:
    def test_returns_color(self):
        thresholds = [(100, "green"), (80, "orange"), (0, "red")]
        assert get_color(80, thresholds) == "orange"

    def test_handles_unsorted_thresholds(self):
        thresholds = [(0, "red"), (80, "orange"), (100, "green")]
        assert get_color(80, thresholds) == "orange"

    def test_handles_no_zero(self):
        thresholds = [(50, "red"), (80, "orange"), (100, "green")]
        assert get_color(0, thresholds) == "red"


class TestCreateBadge:
    def test_returns_coverage_value(self):
        coverage = random.randint(0, 100)
        badge = create_badge(coverage, THRESHOLDS)
        assert str(coverage) in badge

    def test_returns_color(self):
        badge = create_badge(100, THRESHOLDS)
        assert "green" in badge
