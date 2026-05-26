import json
import random
from pathlib import Path

import pytest

from cov_badge import (
    DEFAULT_COLOR_THRESHOLDS,
    AppConfig,
    create_badge,
    get_color,
    get_cov_percent,
    get_value_at_path,
    load_json,
    update_badge,
)

THRESHOLDS = [(100, "green"), (80, "orange"), (0, "red")]


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
