import json
from operator import itemgetter
from typing import Any

import typer
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    percent_path: list[str] = ["totals", "percent_statements_covered_display"]


app = typer.Typer()


@app.command()
def main() -> None:
    config = AppConfig()
    print("Loading JSON file...")
    obj = load_json()
    print("Creating coverage badge...")
    update_badge(get_cov_percent(obj, config.percent_path))


def update_badge(coverage: int):
    """Update the badge in the README"""
    # Open README file
    with open("README.md") as file:
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
    readme_lines[index] = create_badge(coverage)

    # Write README file
    with open("README.md", mode="w") as file:
        file.writelines(readme_lines)


def create_badge(coverage: int) -> str:
    """Create the badge script"""
    return f"![coverage](https://img.shields.io/badge/coverage-{coverage}%25-green)\n"


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


def load_json() -> dict:
    """Load JSON file and return as a Python dict"""
    with open("coverage.json") as file:
        obj = json.load(file)
    return obj
