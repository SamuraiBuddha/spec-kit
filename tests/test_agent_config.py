"""
Tests for agent configuration validation.

This module tests the AGENT_CONFIG structure to ensure all agents
have required fields and valid configurations.
"""

import sys
from pathlib import Path

import pytest


# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from specify_cli import AGENT_CONFIG, SCRIPT_TYPE_CHOICES


class TestAgentConfigStructure:
    """Tests for AGENT_CONFIG structure validation."""

    REQUIRED_FIELDS = {"name", "folder", "install_url", "requires_cli"}

    def test_agent_config_is_dict(self):
        """Test that AGENT_CONFIG is a dictionary."""
        assert isinstance(AGENT_CONFIG, dict)

    def test_agent_config_not_empty(self):
        """Test that AGENT_CONFIG contains at least one agent."""
        assert len(AGENT_CONFIG) > 0

    def test_all_agents_have_required_fields(self):
        """Test that each agent has all required fields."""
        for agent_key, agent_config in AGENT_CONFIG.items():
            for field in self.REQUIRED_FIELDS:
                assert field in agent_config, f"Agent '{agent_key}' missing field '{field}'"

    def test_agent_names_are_strings(self):
        """Test that all agent names are non-empty strings."""
        for agent_key, agent_config in AGENT_CONFIG.items():
            name = agent_config["name"]
            assert isinstance(name, str), f"Agent '{agent_key}' name is not a string"
            assert len(name) > 0, f"Agent '{agent_key}' has empty name"

    def test_agent_folders_end_with_slash(self):
        """Test that all agent folders end with /."""
        for agent_key, agent_config in AGENT_CONFIG.items():
            folder = agent_config["folder"]
            assert isinstance(folder, str), f"Agent '{agent_key}' folder is not a string"
            assert folder.endswith("/"), f"Agent '{agent_key}' folder '{folder}' should end with /"

    def test_agent_folders_start_with_dot(self):
        """Test that all agent folders start with . (hidden directories)."""
        for agent_key, agent_config in AGENT_CONFIG.items():
            folder = agent_config["folder"]
            assert folder.startswith("."), f"Agent '{agent_key}' folder '{folder}' should start with ."

    def test_agent_requires_cli_is_boolean(self):
        """Test that requires_cli field is a boolean."""
        for agent_key, agent_config in AGENT_CONFIG.items():
            requires_cli = agent_config["requires_cli"]
            assert isinstance(requires_cli, bool), f"Agent '{agent_key}' requires_cli is not a boolean"

    def test_cli_agents_have_install_url(self):
        """Test that agents requiring CLI have an install URL."""
        for agent_key, agent_config in AGENT_CONFIG.items():
            if agent_config["requires_cli"]:
                install_url = agent_config["install_url"]
                assert install_url is not None, f"CLI agent '{agent_key}' missing install_url"
                assert isinstance(install_url, str), f"Agent '{agent_key}' install_url is not a string"
                assert install_url.startswith("http"), f"Agent '{agent_key}' install_url should be a URL"

    def test_ide_agents_may_have_null_install_url(self):
        """Test that IDE-based agents can have null install_url."""
        for agent_key, agent_config in AGENT_CONFIG.items():
            if not agent_config["requires_cli"]:
                # Install URL can be None for IDE-based agents
                install_url = agent_config["install_url"]
                assert install_url is None or isinstance(install_url, str)


class TestKnownAgents:
    """Tests for specific known agents in the configuration."""

    EXPECTED_AGENTS = [
        "copilot",
        "claude",
        "gemini",
        "cursor-agent",
        "qwen",
        "opencode",
        "codex",
        "windsurf",
        "kilocode",
        "auggie",
        "codebuddy",
        "roo",
        "q",
    ]

    def test_expected_agents_present(self):
        """Test that all expected agents are present."""
        for agent in self.EXPECTED_AGENTS:
            assert agent in AGENT_CONFIG, f"Expected agent '{agent}' not in AGENT_CONFIG"

    def test_copilot_config(self):
        """Test GitHub Copilot configuration."""
        config = AGENT_CONFIG["copilot"]
        assert config["name"] == "GitHub Copilot"
        assert config["folder"] == ".github/"
        assert config["requires_cli"] is False
        assert config["install_url"] is None

    def test_claude_config(self):
        """Test Claude Code configuration."""
        config = AGENT_CONFIG["claude"]
        assert config["name"] == "Claude Code"
        assert config["folder"] == ".claude/"
        assert config["requires_cli"] is True
        assert "anthropic" in config["install_url"].lower()

    def test_gemini_config(self):
        """Test Gemini CLI configuration."""
        config = AGENT_CONFIG["gemini"]
        assert config["name"] == "Gemini CLI"
        assert config["folder"] == ".gemini/"
        assert config["requires_cli"] is True

    def test_cursor_config(self):
        """Test Cursor configuration."""
        config = AGENT_CONFIG["cursor-agent"]
        assert config["name"] == "Cursor"
        assert config["folder"] == ".cursor/"
        assert config["requires_cli"] is False

    def test_codex_config(self):
        """Test Codex CLI configuration."""
        config = AGENT_CONFIG["codex"]
        assert config["name"] == "Codex CLI"
        assert config["folder"] == ".codex/"
        assert config["requires_cli"] is True

    def test_q_developer_config(self):
        """Test Amazon Q Developer CLI configuration."""
        config = AGENT_CONFIG["q"]
        assert config["name"] == "Amazon Q Developer CLI"
        assert config["folder"] == ".amazonq/"
        assert config["requires_cli"] is True


class TestAgentCategories:
    """Tests for agent categorization (CLI vs IDE-based)."""

    def test_cli_agents(self):
        """Test that expected CLI agents require CLI."""
        cli_agents = ["claude", "gemini", "qwen", "opencode", "codex", "auggie", "codebuddy", "q"]
        for agent in cli_agents:
            if agent in AGENT_CONFIG:
                assert AGENT_CONFIG[agent]["requires_cli"] is True, \
                    f"Agent '{agent}' should require CLI"

    def test_ide_agents(self):
        """Test that expected IDE agents don't require CLI."""
        ide_agents = ["copilot", "cursor-agent", "windsurf", "kilocode", "roo"]
        for agent in ide_agents:
            if agent in AGENT_CONFIG:
                assert AGENT_CONFIG[agent]["requires_cli"] is False, \
                    f"Agent '{agent}' should be IDE-based"


class TestScriptTypeChoices:
    """Tests for script type configuration."""

    def test_script_type_choices_is_dict(self):
        """Test that SCRIPT_TYPE_CHOICES is a dictionary."""
        assert isinstance(SCRIPT_TYPE_CHOICES, dict)

    def test_sh_script_type_present(self):
        """Test that 'sh' script type is present."""
        assert "sh" in SCRIPT_TYPE_CHOICES

    def test_ps_script_type_present(self):
        """Test that 'ps' script type is present."""
        assert "ps" in SCRIPT_TYPE_CHOICES

    def test_script_type_descriptions_are_strings(self):
        """Test that all script type descriptions are strings."""
        for key, description in SCRIPT_TYPE_CHOICES.items():
            assert isinstance(description, str)
            assert len(description) > 0


class TestAgentConfigConsistency:
    """Tests for AGENT_CONFIG consistency and uniqueness."""

    def test_unique_agent_names(self):
        """Test that all agent names are unique."""
        names = [config["name"] for config in AGENT_CONFIG.values()]
        assert len(names) == len(set(names)), "Duplicate agent names found"

    def test_unique_agent_folders(self):
        """Test that all agent folders are unique."""
        folders = [config["folder"] for config in AGENT_CONFIG.values()]
        assert len(folders) == len(set(folders)), "Duplicate agent folders found"

    def test_agent_key_lowercase(self):
        """Test that all agent keys are lowercase."""
        for agent_key in AGENT_CONFIG.keys():
            assert agent_key == agent_key.lower(), f"Agent key '{agent_key}' should be lowercase"

    def test_no_trailing_spaces_in_names(self):
        """Test that agent names have no trailing/leading spaces."""
        for agent_key, config in AGENT_CONFIG.items():
            name = config["name"]
            assert name == name.strip(), f"Agent '{agent_key}' name has trailing/leading spaces"

    def test_install_urls_are_https(self):
        """Test that install URLs use HTTPS."""
        for agent_key, config in AGENT_CONFIG.items():
            install_url = config["install_url"]
            if install_url is not None:
                assert install_url.startswith("https://"), \
                    f"Agent '{agent_key}' install_url should use HTTPS"
