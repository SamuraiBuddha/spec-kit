"""
Pytest fixtures for Specify CLI tests.

This module provides shared fixtures for testing the Specify CLI,
including mock environments, temporary directories, and helper utilities.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


# Add src directory to path so we can import specify_cli
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_project_dir(temp_dir: Path) -> Path:
    """Create a temporary project directory structure."""
    project_dir = temp_dir / "test-project"
    project_dir.mkdir(parents=True)
    return project_dir


@pytest.fixture
def mock_git_repo(temp_project_dir: Path) -> Path:
    """Create a mock git repository structure."""
    git_dir = temp_project_dir / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
    (git_dir / "config").write_text("[core]\n\trepositoryformatversion = 0\n")
    return temp_project_dir


@pytest.fixture
def sample_agent_config() -> dict:
    """Return a sample agent configuration for testing."""
    return {
        "claude": {
            "name": "Claude Code",
            "folder": ".claude/",
            "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
            "requires_cli": True,
        },
        "copilot": {
            "name": "GitHub Copilot",
            "folder": ".github/",
            "install_url": None,
            "requires_cli": False,
        },
    }


@pytest.fixture
def mock_console() -> MagicMock:
    """Create a mock Rich console for testing output."""
    console = MagicMock()
    console.print = MagicMock()
    return console


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Create a mock httpx client for testing network operations."""
    client = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "tag_name": "v1.0.0",
        "assets": [
            {
                "name": "spec-kit-template-claude-sh.zip",
                "browser_download_url": "https://example.com/template.zip",
                "size": 1024,
            }
        ],
    }
    client.get.return_value = response
    return client


@pytest.fixture
def mock_environment(monkeypatch) -> None:
    """Set up a clean mock environment for testing."""
    # Clear any existing GitHub tokens
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


@pytest.fixture
def sample_yaml_header() -> str:
    """Return a sample YAML header for template testing."""
    return """---
title: Feature Specification
version: 1.0.0
author: Test User
date: 2024-01-01
tags:
  - feature
  - spec
---

# Feature Title

Feature content goes here.
"""


@pytest.fixture
def mock_step_tracker():
    """Create a mock StepTracker for testing."""
    from specify_cli import StepTracker
    tracker = StepTracker("Test Operation")
    return tracker


@pytest.fixture
def cli_runner():
    """Create a Typer CLI test runner."""
    from typer.testing import CliRunner
    return CliRunner()


@pytest.fixture
def specify_app():
    """Import and return the Specify CLI app."""
    from specify_cli import app
    return app


@pytest.fixture
def isolate_cwd(temp_dir: Path):
    """Fixture to isolate working directory changes during tests."""
    original_cwd = Path.cwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)


@pytest.fixture
def mock_which():
    """Mock shutil.which for tool checking tests."""
    with patch("shutil.which") as mock:
        yield mock


@pytest.fixture
def cross_platform_paths() -> dict:
    """Return test paths for cross-platform path handling tests."""
    return {
        "unix_absolute": "/home/user/project",
        "unix_relative": "./project/src",
        "windows_absolute": "C:\\Users\\User\\project",
        "windows_relative": ".\\project\\src",
        "mixed_separators": "project/src\\file.py",
    }
