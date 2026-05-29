# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.1.1] - 2026-05-29

### Fixed

- Add dot_env_filtering to app config


## [0.1.0] - 2026-05-29

### Added

- Reads coverage percentage from a JSON file and inserts or updates a [Shields.io](https://shields.io) badge in a `README.md` file
- Configurable JSON path to the coverage value, defaulting to the structure produced by coverage.py and pytest-cov
- Configurable colour thresholds mapping coverage percentages to badge colours, with sensible defaults
- Configuration via `pyproject.toml`, environment variables, `.env` file, or command line options, applied in priority order
- `--quiet` flag to suppress output on success
- `--dry-run` flag to preview the badge string without writing to the README
- `--version` flag to print the version and exit
- Atomic README writes using a temporary file and `os.replace()` to prevent corruption on failure
- Validation of colour thresholds for duplicate entries and missing zero-value catch-all
