import pytest


@pytest.fixture
def config_dir(tmp_path, monkeypatch):
    """Change cwd to a temp directory so AppConfig reads a test pyproject.toml."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
