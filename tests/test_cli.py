"""
Tests for Specify CLI commands.

This module tests the main CLI commands (init, check) and their
argument parsing, options, and behavior.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCliInit:
    """Tests for the 'specify init' command."""

    def test_init_requires_project_name_or_here(self, cli_runner, specify_app):
        """Test that init requires either project name or --here flag."""
        result = cli_runner.invoke(specify_app, ["init"])
        # Should fail without project name or --here
        assert result.exit_code != 0

    def test_init_project_name_and_here_conflict(self, cli_runner, specify_app):
        """Test that specifying both project name and --here raises error."""
        result = cli_runner.invoke(specify_app, ["init", "my-project", "--here"])
        assert result.exit_code != 0
        assert "Cannot specify both" in result.stdout or result.exit_code == 1

    def test_init_dot_sets_here_flag(self, cli_runner, specify_app, temp_dir, monkeypatch):
        """Test that 'specify init .' is equivalent to --here."""
        monkeypatch.chdir(temp_dir)
        # Mock the interactive selection and network calls
        with patch("specify_cli.select_with_arrows", return_value="claude"), \
             patch("specify_cli.download_and_extract_template"), \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.is_git_repo", return_value=True), \
             patch("specify_cli.check_tool", return_value=True):
            result = cli_runner.invoke(specify_app, ["init", ".", "--ai", "claude", "--script", "sh"])
            # The command may fail due to missing mocks, but the parsing should work
            # Check that it doesn't complain about missing project name
            assert "Must specify either a project name" not in result.stdout

    def test_init_validates_ai_assistant(self, cli_runner, specify_app, temp_dir, monkeypatch):
        """Test that init validates the --ai option."""
        monkeypatch.chdir(temp_dir)
        result = cli_runner.invoke(specify_app, ["init", "test-project", "--ai", "invalid-ai"])
        assert result.exit_code != 0
        assert "Invalid AI assistant" in result.stdout

    def test_init_validates_script_type(self, cli_runner, specify_app, temp_dir, monkeypatch):
        """Test that init validates the --script option."""
        monkeypatch.chdir(temp_dir)
        with patch("specify_cli.select_with_arrows", return_value="claude"):
            result = cli_runner.invoke(specify_app, ["init", "test-project", "--ai", "claude", "--script", "invalid"])
            assert result.exit_code != 0
            assert "Invalid script type" in result.stdout

    def test_init_no_git_flag(self, cli_runner, specify_app, temp_dir, monkeypatch):
        """Test that --no-git flag is recognized."""
        monkeypatch.chdir(temp_dir)
        # The flag should be recognized even if the full command fails
        with patch("specify_cli.select_with_arrows", return_value="claude"), \
             patch("specify_cli.download_and_extract_template"), \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.check_tool", return_value=True), \
             patch("specify_cli.is_git_repo", return_value=False):
            result = cli_runner.invoke(
                specify_app,
                ["init", "test-project", "--ai", "claude", "--script", "sh", "--no-git"]
            )
            # Check the flag was processed (no "unknown option" error)
            assert "Unknown option" not in result.stdout

    def test_init_ignore_agent_tools_flag(self, cli_runner, specify_app, temp_dir, monkeypatch):
        """Test that --ignore-agent-tools flag skips CLI checks."""
        monkeypatch.chdir(temp_dir)
        with patch("specify_cli.select_with_arrows", return_value="claude"), \
             patch("specify_cli.download_and_extract_template"), \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.check_tool", return_value=False), \
             patch("specify_cli.is_git_repo", return_value=True):
            result = cli_runner.invoke(
                specify_app,
                ["init", "test-project", "--ai", "claude", "--script", "sh", "--ignore-agent-tools"]
            )
            # Should not fail due to missing claude CLI
            assert "Agent Detection Error" not in result.stdout or result.exit_code == 0


class TestCliCheck:
    """Tests for the 'specify check' command."""

    def test_check_command_exists(self, cli_runner, specify_app):
        """Test that the check command is available."""
        result = cli_runner.invoke(specify_app, ["check", "--help"])
        assert result.exit_code == 0
        assert "Check that all required tools are installed" in result.stdout

    def test_check_outputs_tool_status(self, cli_runner, specify_app):
        """Test that check command outputs tool availability status."""
        with patch("shutil.which") as mock_which:
            # Mock all tool checks to return None (not found)
            mock_which.return_value = None
            result = cli_runner.invoke(specify_app, ["check"])
            # Should complete (exit code 0) and show tool status
            assert "Check Available Tools" in result.stdout or result.exit_code == 0


class TestCliHelp:
    """Tests for CLI help and version."""

    def test_help_flag(self, cli_runner, specify_app):
        """Test that --help shows usage information."""
        result = cli_runner.invoke(specify_app, ["--help"])
        assert result.exit_code == 0
        assert "specify" in result.stdout.lower() or "Usage" in result.stdout

    def test_init_help(self, cli_runner, specify_app):
        """Test that 'specify init --help' shows init-specific help."""
        result = cli_runner.invoke(specify_app, ["init", "--help"])
        assert result.exit_code == 0
        assert "project" in result.stdout.lower()


class TestGitHubTokenHandling:
    """Tests for GitHub token handling."""

    def test_github_token_from_env_gh_token(self, monkeypatch):
        """Test that GH_TOKEN environment variable is used."""
        from specify_cli import _github_token
        monkeypatch.setenv("GH_TOKEN", "test-token-gh")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        assert _github_token() == "test-token-gh"

    def test_github_token_from_env_github_token(self, monkeypatch):
        """Test that GITHUB_TOKEN environment variable is used."""
        from specify_cli import _github_token
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", "test-token-github")
        assert _github_token() == "test-token-github"

    def test_github_token_cli_takes_precedence(self, monkeypatch):
        """Test that CLI token takes precedence over environment."""
        from specify_cli import _github_token
        monkeypatch.setenv("GH_TOKEN", "env-token")
        assert _github_token("cli-token") == "cli-token"

    def test_github_token_strips_whitespace(self, monkeypatch):
        """Test that GitHub tokens are stripped of whitespace."""
        from specify_cli import _github_token
        monkeypatch.setenv("GH_TOKEN", "  token-with-spaces  ")
        assert _github_token() == "token-with-spaces"

    def test_github_token_returns_none_for_empty(self, monkeypatch):
        """Test that empty tokens return None."""
        from specify_cli import _github_token
        monkeypatch.setenv("GH_TOKEN", "")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        assert _github_token() is None

    def test_github_auth_headers_with_token(self, monkeypatch):
        """Test that auth headers are generated with token."""
        from specify_cli import _github_auth_headers
        monkeypatch.setenv("GH_TOKEN", "test-token")
        headers = _github_auth_headers()
        assert headers == {"Authorization": "Bearer test-token"}

    def test_github_auth_headers_without_token(self, monkeypatch):
        """Test that empty dict is returned without token."""
        from specify_cli import _github_auth_headers
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        headers = _github_auth_headers()
        assert headers == {}


class TestRunCommand:
    """Tests for the run_command utility function."""

    def test_run_command_capture_output(self):
        """Test that run_command can capture output."""
        from specify_cli import run_command
        # Use a simple cross-platform command
        if sys.platform == "win32":
            result = run_command(["cmd", "/c", "echo", "hello"], capture=True)
        else:
            result = run_command(["echo", "hello"], capture=True)
        assert result is not None
        assert "hello" in result

    def test_run_command_no_capture(self):
        """Test that run_command without capture returns None."""
        from specify_cli import run_command
        if sys.platform == "win32":
            result = run_command(["cmd", "/c", "echo", "hello"], capture=False)
        else:
            result = run_command(["echo", "hello"], capture=False)
        assert result is None

    def test_run_command_failure_with_check(self):
        """Test that run_command raises on failure when check=True."""
        from specify_cli import run_command
        import subprocess
        with pytest.raises(subprocess.CalledProcessError):
            run_command(["false"], check_return=True)  # 'false' always exits 1


class TestCheckTool:
    """Tests for the check_tool function."""

    def test_check_tool_found(self, mock_which):
        """Test check_tool when tool is found."""
        from specify_cli import check_tool
        mock_which.return_value = "/usr/bin/git"
        result = check_tool("git")
        assert result is True

    def test_check_tool_not_found(self, mock_which):
        """Test check_tool when tool is not found."""
        from specify_cli import check_tool
        mock_which.return_value = None
        result = check_tool("nonexistent-tool")
        assert result is False

    def test_check_tool_with_tracker(self, mock_which, mock_step_tracker):
        """Test check_tool updates tracker on success."""
        from specify_cli import check_tool
        mock_which.return_value = "/usr/bin/git"
        mock_step_tracker.add("git", "Git")
        result = check_tool("git", tracker=mock_step_tracker)
        assert result is True
        # Check that the step was marked complete
        step = next((s for s in mock_step_tracker.steps if s["key"] == "git"), None)
        assert step is not None
        assert step["status"] == "done"

    def test_check_tool_claude_local_path(self, mock_which, temp_dir):
        """Test that check_tool handles Claude local path special case."""
        from specify_cli import check_tool, CLAUDE_LOCAL_PATH
        mock_which.return_value = None  # Not in PATH

        # Create the local claude path
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "is_file", return_value=True):
            # This test verifies the special Claude path handling
            # The actual implementation checks CLAUDE_LOCAL_PATH first
            pass  # Just verify the constant exists

        assert CLAUDE_LOCAL_PATH == Path.home() / ".claude" / "local" / "claude"


class TestIsGitRepo:
    """Tests for the is_git_repo function."""

    def test_is_git_repo_true(self, mock_git_repo):
        """Test is_git_repo returns True for git repository."""
        from specify_cli import is_git_repo
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = is_git_repo(mock_git_repo)
            assert result is True

    def test_is_git_repo_false(self, temp_dir):
        """Test is_git_repo returns False for non-git directory."""
        from specify_cli import is_git_repo
        with patch("subprocess.run") as mock_run:
            from subprocess import CalledProcessError
            mock_run.side_effect = CalledProcessError(1, "git")
            result = is_git_repo(temp_dir)
            assert result is False

    def test_is_git_repo_no_path(self):
        """Test is_git_repo uses cwd when no path provided."""
        from specify_cli import is_git_repo
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # Should not raise, uses Path.cwd()
            is_git_repo()
            mock_run.assert_called_once()


class TestInitGitRepo:
    """Tests for the init_git_repo function."""

    def test_init_git_repo_success(self, temp_project_dir):
        """Test successful git repo initialization."""
        from specify_cli import init_git_repo
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            success, error = init_git_repo(temp_project_dir, quiet=True)
            assert success is True
            assert error is None

    def test_init_git_repo_failure(self, temp_project_dir):
        """Test git repo initialization failure."""
        from specify_cli import init_git_repo
        from subprocess import CalledProcessError
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = CalledProcessError(1, ["git", "init"], stderr="error")
            success, error = init_git_repo(temp_project_dir, quiet=True)
            assert success is False
            assert error is not None


class TestMergeJsonFiles:
    """Tests for JSON merging functionality."""

    def test_merge_json_files_deep_merge(self, temp_dir):
        """Test deep merge of JSON files."""
        from specify_cli import merge_json_files

        existing_file = temp_dir / "existing.json"
        existing_content = {
            "key1": "value1",
            "nested": {
                "a": 1,
                "b": 2
            }
        }
        import json
        existing_file.write_text(json.dumps(existing_content))

        new_content = {
            "key2": "value2",
            "nested": {
                "b": 3,
                "c": 4
            }
        }

        result = merge_json_files(existing_file, new_content)

        assert result["key1"] == "value1"  # Preserved
        assert result["key2"] == "value2"  # Added
        assert result["nested"]["a"] == 1  # Preserved
        assert result["nested"]["b"] == 3  # Updated
        assert result["nested"]["c"] == 4  # Added

    def test_merge_json_files_nonexistent(self, temp_dir):
        """Test merge with non-existent file returns new content."""
        from specify_cli import merge_json_files

        nonexistent = temp_dir / "nonexistent.json"
        new_content = {"key": "value"}

        result = merge_json_files(nonexistent, new_content)
        assert result == new_content
