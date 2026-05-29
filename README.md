# cov-badge

![python-required](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Ffourtreestech%2Fcov-badge%2F%2Fmain%2Fpyproject.toml)
![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)

A CLI tool that generates a [Shields.io](https://shields.io) coverage badge and inserts it into your `README.md` automatically.

## Installation

```bash
pip install cov-badge
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add --dev cov-badge
```

## Usage

Run `cov-badge` from your project root after generating a coverage report:

```bash
# Generate coverage report (coverage.py example)
coverage run -m pytest
coverage json

# or using pytest-cov
pytest --cov=your_package --cov-report=json

# Insert or update badge in README.md
cov-badge
```

The tool will insert a badge like this into your `README.md`:

```
![coverage](https://img.shields.io/badge/coverage-95%25-green)
```

If a coverage badge already exists it will be updated in place. If not, it will be inserted after any existing badges, or directly after the main title (`###`).

### Options

| Option | Short | Description |
|---|---|---|
| `--readme-file` | | README file to update (default: `README.md`) |
| `--json-file` | | Coverage JSON file to read (default: `coverage.json`) |
| `--percent-path` | | Dot-separated path to the coverage value in the JSON file |
| `--color-thresholds` | | JSON string defining colour thresholds |
| `--quiet` | `-q` | Suppress output on success |
| `--dry-run` | `-d` | Print the badge string without writing to the README |
| `--version` | `-V` | Show version and exit |
| `--help` | | Show help and exit |

### Examples

Use a different README or JSON file:

```bash
cov-badge --readme-file MYREADME.md --json-file reports/coverage.json
```

Preview the badge without writing it:

```bash
cov-badge --dry-run
```

Use a custom path to the coverage value in the JSON:

```bash
cov-badge --percent-path meta.coverage
```

Override the colour thresholds:

```bash
cov-badge --color-thresholds '[[100, "brightgreen"], [80, "green"], [0, "red"]]'
```

## Configuration

Options can be set via the command line, environment variables, a `.env` file, or `pyproject.toml`. They are applied in that priority order — command line takes precedence over everything else.

### pyproject.toml

Add a `[tool.cov-badge]` section:

```toml
[tool.cov-badge]
readme_file = "README.md"
json_file = "coverage.json"
percent_path = ["totals", "percent_statements_covered_display"]
color_thresholds = [
    [100, "brightgreen"],
    [90, "green"],
    [70, "yellow"],
    [50, "orange"],
    [0, "red"],
]
```

### Environment variables

All options can be set via environment variables prefixed with `COV_BADGE_`:

```bash
COV_BADGE_README_FILE=README.md
COV_BADGE_JSON_FILE=coverage.json
COV_BADGE_PERCENT_PATH='["totals", "percent_statements_covered_display"]'
COV_BADGE_COLOR_THRESHOLDS='[[100, "brightgreen"], [0, "red"]]'
```

### .env file

The same variables can be set in a `.env` file in your project root:

```bash
COV_BADGE_README_FILE=README.md
COV_BADGE_JSON_FILE=coverage.json
```

## Colour thresholds

The default thresholds are:

| Coverage | Colour |
|---|---|
| 100% | `brightgreen` |
| 90–99% | `green` |
| 70–89% | `yellow` |
| 50–69% | `orange` |
| 0–49% | `red` |

Colours must be valid [Shields.io named colours](https://shields.io/docs/colors) or hex codes. Thresholds can be supplied in any order. It is recommended to always include a `0` entry as a catch-all — if no zero entry is present, a warning will be issued and the lowest defined colour will be used as a fallback.

## Custom JSON structure

By default `cov-badge` reads from the path `["totals", "percent_statements_covered_display"]` in the JSON file, which matches the output of [coverage.py](https://coverage.readthedocs.io). If your coverage tool produces a different JSON structure, you can specify a custom path.

For example, if your `coverage.json` looks like:

```json
{
    "meta": {
        "coverage": 95
    }
}
```

Set the path via `pyproject.toml`:

```toml
[tool.cov-badge]
percent_path = ["meta", "coverage"]
```

Or via the CLI:

```bash
cov-badge --percent-path meta.coverage
```

## CI usage

A typical GitHub Actions step after running your test suite:

```yaml
- name: Generate coverage report
  run: |
    coverage run -m pytest
    coverage json

- name: Update coverage badge
  run: cov-badge
```

To suppress output in CI:

```bash
cov-badge --quiet
```

## Requirements

- Python 3.12+