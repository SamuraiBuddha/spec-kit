# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spec Kit is a framework for Spec-Driven Development (SDD), where specifications become executable and directly generate working implementations. The project provides a CLI tool (`specify`) to bootstrap spec-driven projects and includes templates and scripts for managing the SDD workflow.

## Key Commands

### Installation and Setup
```bash
# Install the Specify CLI globally
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>

# Check system requirements
specify check

# Initialize with specific AI assistant
specify init my-project --ai claude
specify init my-project --ai gemini  
specify init my-project --ai copilot
specify init my-project --ai cursor

# Initialize in current directory
specify init --here --ai claude
```

### Development Workflow Commands

These commands are available when working within a Spec Kit project:

1. **`/specify`** - Create or update feature specifications from natural language descriptions
   - Automatically creates feature branches and numbered specs
   - Uses templates/spec-template.md structure
   - Output: specs/[branch-name]/spec.md

2. **`/plan`** - Generate implementation plans from specifications
   - Reads feature spec and constitutional requirements
   - Creates technical architecture and implementation details
   - Outputs: plan.md, data-model.md, contracts/, quickstart.md, research.md

3. **`/tasks`** - Generate actionable task lists from implementation plans
   - Analyzes plan and design documents
   - Creates dependency-ordered, parallelizable task lists
   - Output: tasks.md with numbered tasks (T001, T002, etc.)

## Code Architecture

### Directory Structure
```
spec-kit/
├── src/specify_cli/         # Python CLI implementation
│   └── __init__.py         # Main CLI app using Typer
├── scripts/                 # Workflow automation scripts
│   ├── bash/               # POSIX shell scripts
│   └── powershell/         # PowerShell scripts  
├── templates/              # Core SDD templates
│   ├── commands/           # Command definitions (/specify, /plan, /tasks)
│   ├── spec-template.md   # Feature specification template
│   ├── plan-template.md   # Implementation plan template
│   └── tasks-template.md  # Task list template
├── memory/                 # Project constitution and guidelines
│   └── constitution.md    # Core principles (customizable per project)
└── docs/                   # Documentation
```

### Key Components

**Specify CLI (`src/specify_cli/__init__.py`)**
- Built with Typer for CLI interface
- Handles template downloads from GitHub releases
- Supports multiple AI assistants (Claude, Gemini, Copilot, Cursor)
- Cross-platform script support (bash/PowerShell)
- Interactive UI with arrow-key selection

**Workflow Scripts**
- `create-new-feature.sh/ps1` - Creates feature branches and spec directories
- `setup-plan.sh/ps1` - Initializes implementation planning  
- `check-task-prerequisites.sh/ps1` - Validates requirements for task generation
- `update-agent-context.sh/ps1` - Updates CLAUDE.md with project context

**Templates System**
- Command templates define the workflow for each slash command
- Templates contain execution flows and validation gates
- Self-contained and executable with embedded logic

## Development Guidelines

### Working with Windows
- Use backslash path separators in Windows environments
- PowerShell scripts available alongside bash scripts
- Line endings should be CRLF for Windows compatibility

### Template Modifications
- Templates in `templates/` directory are copied during project initialization
- Customize `constitution.md` for project-specific principles
- Command templates in `templates/commands/` control the SDD workflow

### Adding New Features
1. Use `/specify` to create a feature specification
2. Use `/plan` to generate implementation plans
3. Use `/tasks` to create executable task lists
4. Follow the numbered task progression (T001, T002, etc.)

### Script Development
- Scripts must output JSON when called with `--json` flag
- Scripts handle cross-platform compatibility concerns
- All paths in script outputs should be absolute

## Testing Approach

The project follows Test-Driven Development principles:
- Tests are written before implementation (red-green-refactor)
- Integration tests focus on contract validation
- Each feature includes acceptance criteria and test scenarios