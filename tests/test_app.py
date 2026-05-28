import json
import random
import warnings
from pathlib import Path

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from typer.testing import CliRunner

from cov_badge import (
    DEFAULT_COLOR_THRESHOLDS,
    AppConfig,
    app,
    create_badge,
    get_color,
    get_cov_percent,
    get_value_at_path,
    load_json,
    update_badge,
)

THRESHOLDS = [(100, "green"), (80, "orange"), (0, "red")]

runner = CliRunner()


def make_readme(tmp_path: Path, lines: list[str]) -> Path:
    readme = tmp_path / "README.md"
    readme.write_text("\n".join(lines) + "\n")
    return readme


def make_json(tmp_path: Path, obj: dict) -> Path:
    json_file = tmp_path / "coverage.json"
    with open(json_file, mode="w") as file:
        json.dump(obj, file)
    return json_file


def write_toml(config_dir: Path, content: str) -> None:
    (config_dir / "pyproject.toml").write_text(content)


class TestLoadJSON:
    def test_returns_object(self, tmp_path):
        coverage = random.randint(0, 100)
        obj = {"totals": {"percent_statements_covered_display": coverage}}
        json_file = make_json(tmp_path, obj)
        new_obj = load_json(str(json_file))
        assert new_obj["totals"]["percent_statements_covered_display"] == coverage


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

    def test_dry_run_doesnt_write_to_readme(self, tmp_path):
        readme = make_readme(
            tmp_path,
            [
                "### My Project",
                "Some description.",
            ],
        )
        coverage = random.randint(0, 100)
        update_badge(coverage, THRESHOLDS, str(readme), dry_run=True)
        lines = readme.read_text().splitlines()
        assert lines[1] == "Some description."


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


class TestTOMLSettings:
    def test_default_values_when_no_toml_section(self, config_dir):
        write_toml(config_dir, "[tool.other]\nfoo = 'bar'\n")
        config = AppConfig()
        assert config.readme_file == "README.md"
        assert config.json_file == "coverage.json"
        assert config.color_thresholds == DEFAULT_COLOR_THRESHOLDS

    def test_overrides_readme_file(self, config_dir):
        write_toml(
            config_dir,
            """
    [tool.cov-badge]
    readme_file = "MYREADME.md"
    """,
        )
        config = AppConfig()
        assert config.readme_file == "MYREADME.md"

    def test_overrides_json_file(self, config_dir):
        write_toml(
            config_dir,
            """
    [tool.cov-badge]
    json_file = "my_coverage.json"
    """,
        )
        config = AppConfig()
        assert config.json_file == "my_coverage.json"

    def test_overrides_color_thresholds(self, config_dir):
        write_toml(
            config_dir,
            """
    [tool.cov-badge]
    color_thresholds = [[100, "blue"], [0, "red"]]
    """,
        )
        config = AppConfig()
        assert config.color_thresholds == [(100, "blue"), (0, "red")]

    def test_overrides_percent_path(self, config_dir):
        write_toml(
            config_dir,
            """
    [tool.cov-badge]
    percent_path = ["totals", "custom_key"]
    """,
        )
        config = AppConfig()
        assert config.percent_path == ["totals", "custom_key"]

    def test_missing_pyproject_toml_uses_defaults(self, config_dir):
        # No pyproject.toml written at all
        config = AppConfig()
        assert config.readme_file == "README.md"


class TestEnvSettings:
    def test_env_overrides_readme_file(self, monkeypatch):
        monkeypatch.setenv("COV_BADGE_README_FILE", "OTHER.md")
        assert AppConfig().readme_file == "OTHER.md"

    def test_env_takes_priority_over_toml(self, config_dir, monkeypatch):
        write_toml(
            config_dir,
            """
    [tool.cov-badge]
    readme_file = "TOML.md"
    """,
        )
        monkeypatch.setenv("COV_BADGE_README_FILE", "ENV.md")
        assert AppConfig().readme_file == "ENV.md"

    def test_env_json_list_field(self, monkeypatch):
        monkeypatch.setenv("COV_BADGE_PERCENT_PATH", '["meta", "coverage"]')
        assert AppConfig().percent_path == ["meta", "coverage"]


class TestDotEnvSettings:
    def test_dotenv_overrides_readme_file(self, config_dir):
        (config_dir / ".env").write_text("COV_BADGE_README_FILE=DOTENV.md\n")
        assert AppConfig().readme_file == "DOTENV.md"

    def test_env_var_takes_priority_over_dotenv(self, config_dir, monkeypatch):
        (config_dir / ".env").write_text("COV_BADGE_README_FILE=DOTENV.md\n")
        monkeypatch.setenv("COV_BADGE_README_FILE", "ENV.md")
        assert AppConfig().readme_file == "ENV.md"

    def test_dotenv_takes_priority_over_toml(self, config_dir):
        write_toml(
            config_dir,
            """
    [tool.cov-badge]
    readme_file = "TOML.md"
    """,
        )
        (config_dir / ".env").write_text("COV_BADGE_README_FILE=DOTENV.md\n")
        assert AppConfig().readme_file == "DOTENV.md"


class TestCLISettings:
    def test_cli_overrides_readme_file(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        result = runner.invoke(
            app,
            ["--readme-file", str(readme), "--json-file", str(json_file)],
        )
        assert result.exit_code == 0
        assert "![coverage]" in readme.read_text()

    def test_cli_overrides_json_file(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        result = runner.invoke(
            app,
            ["--readme-file", str(readme), "--json-file", str(json_file)],
        )
        assert result.exit_code == 0

    def test_cli_overrides_percent_path(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(tmp_path, {"meta": {"coverage": "72"}})
        result = runner.invoke(
            app,
            [
                "--readme-file",
                str(readme),
                "--json-file",
                str(json_file),
                "--percent-path",
                "meta.coverage",
            ],
        )
        assert result.exit_code == 0
        assert "72" in readme.read_text()

    def test_cli_overrides_color_thresholds(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "100"}}
        )
        result = runner.invoke(
            app,
            [
                "--readme-file",
                str(readme),
                "--json-file",
                str(json_file),
                "--color-thresholds",
                '[[100, "blue"], [0, "red"]]',
            ],
        )
        assert result.exit_code == 0
        assert "blue" in readme.read_text()

    def test_cli_takes_priority_over_toml(self, config_dir, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        write_toml(
            config_dir,
            """
[tool.cov-badge]
readme_file = "TOML.md"
json_file = "toml_coverage.json"
""",
        )
        result = runner.invoke(
            app,
            ["--readme-file", str(readme), "--json-file", str(json_file)],
        )
        assert result.exit_code == 0
        assert "![coverage]" in readme.read_text()

    def test_cli_takes_priority_over_env(self, tmp_path, monkeypatch):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        monkeypatch.setenv("COV_BADGE_README_FILE", "ENV.md")
        monkeypatch.setenv("COV_BADGE_JSON_FILE", "env_coverage.json")
        result = runner.invoke(
            app,
            ["--readme-file", str(readme), "--json-file", str(json_file)],
        )
        assert result.exit_code == 0
        assert "![coverage]" in readme.read_text()

    def test_cli_error_on_invalid_json_file(self, tmp_path):
        result = runner.invoke(
            app,
            ["--json-file", str(tmp_path / "nonexistent.json")],
        )
        assert result.exit_code != 0

    def test_cli_error_on_invalid_percent_path(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        result = runner.invoke(
            app,
            [
                "--readme-file",
                str(readme),
                "--json-file",
                str(json_file),
                "--percent-path",
                "wrong.path",
            ],
        )
        assert result.exit_code != 0


class TestApp:
    def test_invalid_key_causes_error(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        result = runner.invoke(
            app,
            [
                "--readme-file",
                str(readme),
                "--json-file",
                str(json_file),
                "--percent-path",
                "total",
            ],
        )
        assert result.exit_code == 1
        assert "Key 'total' not found" in result.output

    def test_invalid_path_causes_error(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        result = runner.invoke(
            app,
            [
                "--readme-file",
                str(readme),
                "--json-file",
                str(json_file),
                "--percent-path",
                "totals.percent_statements_covered_display.cov",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid path" in result.output

    def test_invalid_json_causes_error(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        result = runner.invoke(
            app,
            [
                "--readme-file",
                str(readme),
                "--json-file",
                str(json_file),
                "--color-thresholds",
                "abcde",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid JSON" in result.output

    def test_prints_outcome(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        result = runner.invoke(
            app,
            [
                "--readme-file",
                str(readme),
                "--json-file",
                str(json_file),
            ],
        )
        assert "Coverage badge updated" in result.output

    def test_no_output_in_quiet_mode(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        result = runner.invoke(
            app,
            ["--readme-file", str(readme), "--json-file", str(json_file), "--quiet"],
        )
        assert not result.output

    def test_version(self, tmp_path):
        readme = make_readme(tmp_path, ["### My Project"])
        json_file = make_json(
            tmp_path, {"totals": {"percent_statements_covered_display": "95"}}
        )
        result = runner.invoke(
            app,
            [
                "--readme-file",
                str(readme),
                "--json-file",
                str(json_file),
                "--version",
            ],
        )
        assert "cov-badge" in result.output


class TestAppConfig:
    def test_warns_when_no_zero_threshold(self):
        with pytest.warns(UserWarning, match="no zero-value entry"):
            AppConfig(color_thresholds=[(100, "green"), (50, "orange")])

    def test_no_warning_when_zero_threshold_present(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            AppConfig(color_thresholds=[(100, "green"), (0, "red")])  # should not warn

    def test_error_with_duplicate_color_threshold_values(self):
        with pytest.raises(ValueError):
            AppConfig(color_thresholds=[(100, "green"), (100, "orange")])


# Strategy for a single threshold: (int 1-100, non-empty string)
threshold_entry = st.tuples(
    st.integers(min_value=1, max_value=100), st.text(min_size=1)
)

# Strategy for a valid thresholds list: at least one entry, ending with a zero entry
valid_thresholds = st.lists(threshold_entry, min_size=1).map(
    lambda ts: ts + [(0, "red")]
)


class TestHypothesis:
    # --- get_color ---

    @given(value=st.integers(min_value=0, max_value=100), thresholds=valid_thresholds)
    def test_get_color_always_returns_a_string(self, value, thresholds):
        result = get_color(value, thresholds)
        assert isinstance(result, str)

    @given(value=st.integers(min_value=0, max_value=100), thresholds=valid_thresholds)
    def test_get_color_returns_a_color_from_thresholds(self, value, thresholds):
        valid_colors = {color for _, color in thresholds}
        assert get_color(value, thresholds) in valid_colors

    @given(thresholds=valid_thresholds)
    def test_get_color_is_stable_for_same_input(self, thresholds):
        """Same inputs always produce the same output."""
        assert get_color(50, thresholds) == get_color(50, thresholds)

    @given(value=st.integers(min_value=0, max_value=100), thresholds=valid_thresholds)
    def test_get_color_handles_unsorted_thresholds(self, value, thresholds):
        """Result should be the same regardless of threshold order."""
        assume(len({min_value for min_value, _ in thresholds}) == len(thresholds))
        shuffled = thresholds.copy()
        shuffled.reverse()
        assert get_color(value, thresholds) == get_color(value, shuffled)

    # --- get_value_at_path ---

    @given(value=st.integers())
    def test_get_value_at_path_single_key(self, value):
        obj = {"key": value}
        assert get_value_at_path(obj, ["key"]) == value

    @given(value=st.integers(), depth=st.integers(min_value=1, max_value=5))
    def test_get_value_at_path_nested(self, value, depth):
        """Navigates arbitrarily deep nested dicts."""
        keys = [f"level{i}" for i in range(depth)]
        # Build nested dict from the inside out
        obj = value
        for key in reversed(keys):
            obj = {key: obj}
        assert get_value_at_path(obj, keys) == value

    @given(
        keys=st.lists(st.text(min_size=1), min_size=1, max_size=5),
        value=st.integers(),
    )
    def test_get_value_at_path_raises_key_error_on_wrong_key(self, keys, value):
        """A path with a bad final key always raises KeyError."""
        obj = value
        for key in reversed(keys):
            obj = {key: obj}
        bad_key = "this_key_does_not_exist"
        assume(bad_key not in keys)
        with pytest.raises(KeyError):
            get_value_at_path(obj, keys + [bad_key])

    @given(value=st.integers(), key=st.text(min_size=1))
    def test_get_value_at_path_raises_type_error_on_non_dict(self, value, key):
        """Attempting to traverse a non-dict node always raises TypeError."""
        obj = {key: value}  # value is an int, not a dict
        with pytest.raises(TypeError):
            get_value_at_path(obj, [key, "another_key"])
