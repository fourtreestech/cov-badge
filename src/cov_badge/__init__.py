import json
from typing import Any

import typer

app = typer.Typer()


@app.command()
def main() -> None:
    print("Loading JSON file...")
    obj = load_json()
    update_badge(get_cov_percent(obj))


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


def get_cov_percent(obj: dict[str, Any]) -> int:
    """Get percentage coverage for badge display"""
    return int(obj["totals"]["percent_statements_covered_display"])


def load_json() -> dict:
    """Load JSON file and return as a Python dict"""
    with open("coverage.json") as file:
        obj = json.load(file)
    return obj
