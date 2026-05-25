import random

import pytest

from cov_badge import get_cov_percent, get_value_at_path


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
