# Default: list available tasks
default:
    @just --list

# Lint and type-check
check:
    @echo "\nRunning ruff..."
    uvx ruff check . --fix && uvx ruff format .
    @echo "\nRunning ty..."
    uvx ty check .
    @echo "\nCheck complete.\n"

# Merge dev into main and push
sync:
    @echo "\nSyncing dev to main..."
    git switch main
    git pull origin main
    git merge --ff-only dev
    git push -u origin main
    git switch dev
    @echo "\nSync complete.\n"
