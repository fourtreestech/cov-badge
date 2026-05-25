import random

import pytest

from cov_badge import create_badge, get_color, get_cov_percent, get_value_at_path


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
        thresholds = [(100, "green"), (80, "orange"), (0, "red")]
        coverage = random.randint(0, 100)
        badge = create_badge(coverage, thresholds)
        assert str(coverage) in badge

    def test_returns_color(self):
        thresholds = [(100, "green"), (80, "orange"), (0, "red")]
        badge = create_badge(100, thresholds)
        assert "green" in badge
