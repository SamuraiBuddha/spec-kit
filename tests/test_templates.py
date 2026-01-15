"""
Tests for template validation and YAML header parsing.

This module tests template file handling, YAML front matter parsing,
and StepTracker class functionality.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestYamlHeaderParsing:
    """Tests for YAML front matter parsing in templates."""

    def test_yaml_header_structure(self, sample_yaml_header):
        """Test that sample YAML header has expected structure."""
        assert sample_yaml_header.startswith("---")
        assert "---" in sample_yaml_header[3:]  # Has closing delimiter

    def test_extract_yaml_header(self, sample_yaml_header):
        """Test extracting YAML front matter from document."""
        lines = sample_yaml_header.split("\n")

        # Find the header boundaries
        assert lines[0] == "---"
        end_index = None
        for i, line in enumerate(lines[1:], 1):
            if line == "---":
                end_index = i
                break

        assert end_index is not None
        yaml_content = "\n".join(lines[1:end_index])
        assert "title:" in yaml_content
        assert "version:" in yaml_content

    def test_yaml_header_fields(self, sample_yaml_header):
        """Test that expected fields are present in YAML header."""
        expected_fields = ["title", "version", "author", "date", "tags"]
        for field in expected_fields:
            assert f"{field}:" in sample_yaml_header


class TestStepTracker:
    """Tests for the StepTracker class."""

    def test_step_tracker_initialization(self, mock_step_tracker):
        """Test StepTracker initialization."""
        assert mock_step_tracker.title == "Test Operation"
        assert mock_step_tracker.steps == []
        assert mock_step_tracker._refresh_cb is None

    def test_step_tracker_add_step(self, mock_step_tracker):
        """Test adding a step to the tracker."""
        mock_step_tracker.add("step1", "Step One")

        assert len(mock_step_tracker.steps) == 1
        assert mock_step_tracker.steps[0]["key"] == "step1"
        assert mock_step_tracker.steps[0]["label"] == "Step One"
        assert mock_step_tracker.steps[0]["status"] == "pending"

    def test_step_tracker_add_duplicate_key(self, mock_step_tracker):
        """Test that duplicate keys are not added."""
        mock_step_tracker.add("step1", "Step One")
        mock_step_tracker.add("step1", "Step One Again")

        assert len(mock_step_tracker.steps) == 1

    def test_step_tracker_start(self, mock_step_tracker):
        """Test starting a step."""
        mock_step_tracker.add("step1", "Step One")
        mock_step_tracker.start("step1", "Processing...")

        assert mock_step_tracker.steps[0]["status"] == "running"
        assert mock_step_tracker.steps[0]["detail"] == "Processing..."

    def test_step_tracker_complete(self, mock_step_tracker):
        """Test completing a step."""
        mock_step_tracker.add("step1", "Step One")
        mock_step_tracker.start("step1")
        mock_step_tracker.complete("step1", "Done successfully")

        assert mock_step_tracker.steps[0]["status"] == "done"
        assert mock_step_tracker.steps[0]["detail"] == "Done successfully"

    def test_step_tracker_error(self, mock_step_tracker):
        """Test marking a step as error."""
        mock_step_tracker.add("step1", "Step One")
        mock_step_tracker.error("step1", "Failed!")

        assert mock_step_tracker.steps[0]["status"] == "error"
        assert mock_step_tracker.steps[0]["detail"] == "Failed!"

    def test_step_tracker_skip(self, mock_step_tracker):
        """Test skipping a step."""
        mock_step_tracker.add("step1", "Step One")
        mock_step_tracker.skip("step1", "Not needed")

        assert mock_step_tracker.steps[0]["status"] == "skipped"
        assert mock_step_tracker.steps[0]["detail"] == "Not needed"

    def test_step_tracker_status_order(self, mock_step_tracker):
        """Test that status order mapping is correct."""
        expected_order = {
            "pending": 0,
            "running": 1,
            "done": 2,
            "error": 3,
            "skipped": 4,
        }
        assert mock_step_tracker.status_order == expected_order

    def test_step_tracker_attach_refresh(self, mock_step_tracker):
        """Test attaching a refresh callback."""
        callback = MagicMock()
        mock_step_tracker.attach_refresh(callback)

        assert mock_step_tracker._refresh_cb == callback

    def test_step_tracker_refresh_callback_called(self, mock_step_tracker):
        """Test that refresh callback is called on updates."""
        callback = MagicMock()
        mock_step_tracker.attach_refresh(callback)

        mock_step_tracker.add("step1", "Step One")
        callback.assert_called()

    def test_step_tracker_render(self, mock_step_tracker):
        """Test that render returns a Rich Tree."""
        from rich.tree import Tree

        mock_step_tracker.add("step1", "Step One")
        mock_step_tracker.add("step2", "Step Two")
        mock_step_tracker.complete("step1")

        result = mock_step_tracker.render()
        assert isinstance(result, Tree)

    def test_step_tracker_update_nonexistent_creates_step(self, mock_step_tracker):
        """Test that updating a non-existent step creates it."""
        mock_step_tracker.complete("new_step", "Created on complete")

        assert len(mock_step_tracker.steps) == 1
        assert mock_step_tracker.steps[0]["key"] == "new_step"
        assert mock_step_tracker.steps[0]["status"] == "done"


class TestStepTrackerRendering:
    """Tests for StepTracker rendering output."""

    def test_render_pending_step(self, mock_step_tracker):
        """Test rendering of pending step."""
        mock_step_tracker.add("step1", "Step One")
        tree = mock_step_tracker.render()

        # Tree should contain the step
        assert tree is not None

    def test_render_done_step(self, mock_step_tracker):
        """Test rendering of completed step."""
        mock_step_tracker.add("step1", "Step One")
        mock_step_tracker.complete("step1", "Success")
        tree = mock_step_tracker.render()

        assert tree is not None

    def test_render_error_step(self, mock_step_tracker):
        """Test rendering of error step."""
        mock_step_tracker.add("step1", "Step One")
        mock_step_tracker.error("step1", "Failed")
        tree = mock_step_tracker.render()

        assert tree is not None

    def test_render_multiple_steps(self, mock_step_tracker):
        """Test rendering multiple steps in different states."""
        mock_step_tracker.add("step1", "Step One")
        mock_step_tracker.add("step2", "Step Two")
        mock_step_tracker.add("step3", "Step Three")

        mock_step_tracker.complete("step1")
        mock_step_tracker.start("step2")
        # step3 stays pending

        tree = mock_step_tracker.render()
        assert tree is not None


class TestCrossPlatformPaths:
    """Tests for cross-platform path handling."""

    def test_path_normalization_unix(self, cross_platform_paths):
        """Test Unix path normalization."""
        path = Path(cross_platform_paths["unix_absolute"])
        assert path.is_absolute() or str(path).startswith("/")

    def test_path_normalization_relative(self, cross_platform_paths):
        """Test relative path handling."""
        path = Path(cross_platform_paths["unix_relative"])
        assert not path.is_absolute()

    def test_pathlib_handles_separators(self):
        """Test that pathlib handles different separators."""
        # Pathlib should normalize separators on the current platform
        path1 = Path("project/src/file.py")
        path2 = Path("project") / "src" / "file.py"

        assert path1 == path2

    def test_path_resolve_makes_absolute(self, temp_dir):
        """Test that resolve() creates absolute paths."""
        relative = Path("subdir/file.txt")
        absolute = (temp_dir / relative).resolve()

        assert absolute.is_absolute()

    def test_home_path_expansion(self):
        """Test that home directory is properly expanded."""
        home = Path.home()
        assert home.is_absolute()
        assert home.exists()


class TestTemplateConstants:
    """Tests for template-related constants."""

    def test_banner_constant_exists(self):
        """Test that BANNER constant exists."""
        from specify_cli import BANNER
        assert isinstance(BANNER, str)
        assert len(BANNER) > 0

    def test_tagline_constant_exists(self):
        """Test that TAGLINE constant exists."""
        from specify_cli import TAGLINE
        assert isinstance(TAGLINE, str)
        assert "Spec" in TAGLINE

    def test_claude_local_path_constant(self):
        """Test that CLAUDE_LOCAL_PATH is correctly defined."""
        from specify_cli import CLAUDE_LOCAL_PATH
        assert isinstance(CLAUDE_LOCAL_PATH, Path)
        assert ".claude" in str(CLAUDE_LOCAL_PATH)
        assert "local" in str(CLAUDE_LOCAL_PATH)


class TestEnsureExecutableScripts:
    """Tests for the ensure_executable_scripts function."""

    def test_ensure_executable_scripts_windows_noop(self, temp_project_dir):
        """Test that ensure_executable_scripts is a no-op on Windows."""
        from specify_cli import ensure_executable_scripts

        with patch("os.name", "nt"):
            # Should return without doing anything on Windows
            ensure_executable_scripts(temp_project_dir)

    def test_ensure_executable_scripts_no_scripts_dir(self, temp_project_dir):
        """Test handling when scripts directory doesn't exist."""
        from specify_cli import ensure_executable_scripts

        with patch("os.name", "posix"):
            # Should handle missing directory gracefully
            ensure_executable_scripts(temp_project_dir)

    def test_ensure_executable_scripts_with_scripts(self, temp_project_dir):
        """Test making scripts executable."""
        from specify_cli import ensure_executable_scripts

        # Create scripts directory structure
        scripts_dir = temp_project_dir / ".specify" / "scripts"
        scripts_dir.mkdir(parents=True)

        # Create a shell script
        script = scripts_dir / "test.sh"
        script.write_text("#!/bin/bash\necho hello\n")

        # Remove execute permission
        if os.name != "nt":
            os.chmod(script, 0o644)

            ensure_executable_scripts(temp_project_dir)

            # Check that execute permission was added
            mode = os.stat(script).st_mode
            assert mode & 0o100  # Owner execute bit


class TestSelectWithArrows:
    """Tests for the select_with_arrows function."""

    def test_select_with_arrows_returns_key(self):
        """Test that select_with_arrows returns the selected key."""
        from specify_cli import select_with_arrows

        options = {"option1": "First Option", "option2": "Second Option"}

        with patch("specify_cli.get_key") as mock_get_key, \
             patch("specify_cli.Live") as mock_live, \
             patch("specify_cli.console"):
            # Simulate pressing Enter immediately
            mock_get_key.return_value = "enter"
            mock_live.return_value.__enter__ = MagicMock()
            mock_live.return_value.__exit__ = MagicMock()

            result = select_with_arrows(options, "Select:", "option1")
            assert result == "option1"

    def test_select_with_arrows_default_key(self):
        """Test that default_key sets initial selection."""
        from specify_cli import select_with_arrows

        options = {"a": "Alpha", "b": "Beta", "c": "Charlie"}

        with patch("specify_cli.get_key") as mock_get_key, \
             patch("specify_cli.Live") as mock_live, \
             patch("specify_cli.console"):
            mock_get_key.return_value = "enter"
            mock_live.return_value.__enter__ = MagicMock()
            mock_live.return_value.__exit__ = MagicMock()

            result = select_with_arrows(options, "Select:", "b")
            assert result == "b"


class TestGetKey:
    """Tests for the get_key function."""

    def test_get_key_returns_up(self):
        """Test get_key returns 'up' for up arrow."""
        from specify_cli import get_key
        import readchar

        with patch.object(readchar, "readkey", return_value=readchar.key.UP):
            result = get_key()
            assert result == "up"

    def test_get_key_returns_down(self):
        """Test get_key returns 'down' for down arrow."""
        from specify_cli import get_key
        import readchar

        with patch.object(readchar, "readkey", return_value=readchar.key.DOWN):
            result = get_key()
            assert result == "down"

    def test_get_key_returns_enter(self):
        """Test get_key returns 'enter' for enter key."""
        from specify_cli import get_key
        import readchar

        with patch.object(readchar, "readkey", return_value=readchar.key.ENTER):
            result = get_key()
            assert result == "enter"

    def test_get_key_returns_escape(self):
        """Test get_key returns 'escape' for escape key."""
        from specify_cli import get_key
        import readchar

        with patch.object(readchar, "readkey", return_value=readchar.key.ESC):
            result = get_key()
            assert result == "escape"

    def test_get_key_ctrl_c_raises(self):
        """Test get_key raises KeyboardInterrupt for Ctrl+C."""
        from specify_cli import get_key
        import readchar

        with patch.object(readchar, "readkey", return_value=readchar.key.CTRL_C):
            with pytest.raises(KeyboardInterrupt):
                get_key()
