# Default: list available tasks
default:
    @just --list

# Lint and type-check
check:
    uvx ruff check . --fix && uvx ruff format .
    uvx ty check .

# Merge dev into main and push
sync:
    git switch main
    git pull origin main
    git merge --ff-only dev
    git push -u origin main
    git switch dev

# Run tests with coverage
test:
    uv run pytest --cov --cov-report term-missing --cov-report json
    uv run cov-badge

