import json
from typing import Any

import typer

app = typer.Typer()


@app.command()
def main() -> None:
    print("Loading JSON file...")
    obj = load_json()
    print(get_cov_percent(obj))


def get_cov_percent(obj: dict[str, Any]) -> str:
    """Get percentage coverage for badge display"""
    return obj["totals"]["percent_statements_covered_display"]


def load_json() -> dict:
    """Load JSON file and return as a Python dict"""
    with open("coverage.json") as file:
        obj = json.load(file)
    return obj
