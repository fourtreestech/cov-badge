import json
from operator import itemgetter
from typing import Any

import typer
from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)
from rich.console import Console

DEFAULT_COLOR_THRESHOLDS = [
    (100, "brightgreen"),
    (90, "green"),
    (70, "yellow"),
    (50, "orange"),
    (0, "red"),
]


class AppConfig(BaseSettings):
    """Config for the app.

    Populates config info in priority order (highest priority first):
        - command line options
        - environment variables
        - .env
        - pyproject.toml
        - app default values
    """

    percent_path: list[str] = ["totals", "percent_statements_covered_display"]
    color_thresholds: list[tuple[int, str]] = DEFAULT_COLOR_THRESHOLDS
    readme_file: str = "README.md"
    json_file: str = "coverage.json"

    model_config = SettingsConfigDict(
        pyproject_toml_table_header=("tool", "cov-badge"),
        env_prefix="COV_BADGE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Define sources and their order for loading config values."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            PyprojectTomlConfigSettingsSource(settings_cls),
        )

    @field_validator("color_thresholds", mode="before")
    @classmethod
    def coerce_thresholds(cls, v):
        """Coerce color thresholds from TOML source to list[tuple[int, str]]."""
        return [tuple(item) for item in v]


app = typer.Typer()
console = Console(highlight=False)


@app.command()
def main(
    readme_file: str | None = typer.Option(None, help="README file to update."),
    json_file: str | None = typer.Option(None, help="Coverage JSON file to read."),
    percent_path: str | None = typer.Option(
        None,
        help='JSON path to coverage value, as dot-separated string e.g. "totals.percent_covered".',
    ),
    color_thresholds: str | None = typer.Option(
        None,
        help='Color thresholds as JSON string e.g. "[[100, \\"brightgreen\\"], [0, \\"red\\"]]".',
    ),
) -> None:
    """Main app entry point."""
    # Build overrides dict from any CLI args that were actually passed
    overrides: dict[str, Any] = {}
    if readme_file is not None:
        overrides["readme_file"] = readme_file
    if json_file is not None:
        overrides["json_file"] = json_file
    if percent_path is not None:
        overrides["percent_path"] = percent_path.split(".")
    if color_thresholds is not None:
        overrides["color_thresholds"] = json.loads(color_thresholds)

    # Set up config
    config = AppConfig(**overrides)

    # Load JSON file
    console.print("Loading JSON file...")
    obj = load_json(config.json_file)

    # Create badge
    coverage = get_cov_percent(obj, config.percent_path)
    console.print(f"Creating coverage badge ({coverage}%)...")
    update_badge(
        coverage,
        config.color_thresholds,
        config.readme_file,
    )

    # Sign off
    console.print("[bold green]Badge created.[/]\n")


def update_badge(
    coverage: int, color_thresholds: list[tuple[int, str]], readme_file: str
):
    """Update the badge in the README file.

    `coverage` is the total test coverage percentage.

    `color_thresholds` is a list of `[int, str]` tuples,
    where the first element is a minimum value and the second
    is the `Shields.io` color that will be applied from that value.
    Thresholds should be supplied in descending order, and the
    first element of the final tuple should be 0.

    `readme_file` should be the name of a file in the current working directory
    (usually the project root).

    If there is already a coverage badge in the README it will be updated
    with the value of `coverage` and its corresponding color.

    If README doesn't contain a badge one will be added, either directly following
    the last (other) badge already in the README, or if there are no badges,
    directly after the main title (marked with '###'). If there is no main title
    and no badges, the coverage badge will be inserted immediately after the first line.

    Args:
        coverage: Coverage value (0-100).
        color_thresholds: List of thresholds defining a colour for any given value.
        readme_file: Name of the README file to update.
    """
    # Open README file
    with open(readme_file) as file:
        readme_lines = file.readlines()

    # Find the coverage line if there is one
    index = 0
    title = 0
    last_badge = 0
    for i, line in enumerate(readme_lines):
        if line.startswith("![coverage]"):
            index = i
            break
        elif line.startswith("###"):
            title = i
        elif line.startswith("!["):
            last_badge = i

    # If there isn't a coverage line already, insert one -
    # after other badges if there are any, or just after the main title
    else:
        insert_after = last_badge if last_badge else title
        index = insert_after + 1
        readme_lines.insert(index, "")

    # Update badge
    readme_lines[index] = create_badge(coverage, color_thresholds)

    # Write README file
    with open(readme_file, mode="w") as file:
        file.writelines(readme_lines)


def create_badge(coverage: int, color_thresholds: list[tuple[int, str]]) -> str:
    """Create the badge script.

    `color_thresholds` is a list of `[int, str]` tuples,
    where the first element is a minimum value and the second
    is the `Shields.io` color that will be applied from that value.
    Thresholds should be supplied in descending order, and the
    first element of the final tuple should be 0.

    The badge script returned can be pasted directly into your `README.md` file
    and will show a coverage badge with the appropriate color and value.

    Args:
        coverage: Coverage value (0-100).
        color_thresholds: List of thresholds defining a colour for any given value.

    Returns:
        `Shields.io` badge script.
    """
    color = get_color(coverage, color_thresholds)
    return f"![coverage](https://img.shields.io/badge/coverage-{coverage}%25-{color})\n"


def get_color(value: int, color_thresholds: list[tuple[int, str]]) -> str:
    """Get the color corresponding to the given value.

    `color_thresholds` is a list of `[int, str]` tuples,
    where the first element is a minimum value and the second
    is the color that will be applied from that value.
    Thresholds should be supplied in descending order, and the
    first element of the final tuple should be 0.

    Examples:
        >>> thresholds = [(100, "green"), (80, "orange"), (0, "red")]
        >>> get_color(100, thresholds)
        'green'
        >>> get_color(99, thresholds)
        'orange'
        >>> get_color(79, thresholds)
        'red'

    Args:
        value: Coverage value.
        color_thresholds: List of thresholds defining a colour for any given value.

    Returns:
        Color corresponding to the given value.
    """
    # Manage unsorted data
    sorted_thresholds = sorted(color_thresholds, key=itemgetter(0), reverse=True)
    for min_value, color in sorted_thresholds:
        if value >= min_value:
            return color

    # No zero value: return the lowest value color
    return sorted_thresholds[-1][1]


def get_value_at_path(obj: dict[str, Any], path: list[str]) -> Any:
    """Navigate a nested dict using a list of keys.

    Examples:
        >>> obj = { "level1": { "level2": "value" } }
        >>> get_value_at_path(obj, ["level1", "level2"])
        'value'

    Args:
        obj: `dict` to navigate.
        path: Hierarchy of keys to navigate to access the value.

    Returns:
        The value found at the end of the path.

    Raises:
        TypeError: If attempting to traverse anything other than a `dict`.
        KeyError: If an invalid key is provided.
    """
    current = obj
    for key in path:
        if not isinstance(current, dict):
            raise TypeError(
                f"Expected a dict but got {type(current).__name__} at key '{key}'"
            )
        if key not in current:
            raise KeyError(f"Key '{key}' not found")
        current = current[key]
    return current


def get_cov_percent(obj: dict[str, Any], path: list[str]) -> int:
    """Get percentage coverage for badge display.

    Examples:
        >>> obj = {"totals": {"percent_statements_covered_display": "100"}}
        >>> path = ["totals", "percent_statements_covered_display"]
        >>> get_cov_percent(obj, path)
        100

    Args:
        obj: `dict` containing the coverage percentage value.
        path: Keys to navigate to get to the value.

    Returns:
        The value at `path`, coerced to an int
    """
    return int(get_value_at_path(obj, path))


def load_json(json_file: str) -> dict:
    """Load JSON file and return as a Python dict.

    Args:
        json_file: Name of the JSON file to open.

    Returns:
        Content of the JSON file converted into a `dict`.
    """
    with open(json_file) as file:
        obj = json.load(file)
    return obj
