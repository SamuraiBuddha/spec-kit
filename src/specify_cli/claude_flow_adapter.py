#!/usr/bin/env python3
"""
Claude Flow Adapter - Bridge SDD commands to claude-flow swarms

This module provides integration between Spec-Driven Development (SDD) commands
and claude-flow's swarm orchestration capabilities. It maps SDD workflow stages
to appropriate claude-flow strategies:

- /speckit.specify -> claude-flow swarm with researcher strategy
- /speckit.plan -> claude-flow swarm with architect strategy
- /speckit.tasks -> claude-flow swarm with development strategy
- /speckit.implement -> claude-flow hive-mind with parallel execution

Usage:
    specify flow specify "Feature description"
    specify flow plan
    specify flow tasks
    specify flow implement
"""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


class SwarmStrategy(Enum):
    """Claude-flow swarm strategies mapped to SDD workflow stages."""
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    DEVELOPMENT = "development"
    HIVE_MIND = "hive-mind"


class ExecutionMode(Enum):
    """Execution modes for claude-flow commands."""
    SWARM = "swarm"
    HIVE = "hive"
    SEQUENTIAL = "sequential"


@dataclass
class SDDContext:
    """Context data passed from SDD templates to claude-flow swarms."""
    feature_description: str = ""
    feature_dir: Optional[Path] = None
    spec_file: Optional[Path] = None
    plan_file: Optional[Path] = None
    tasks_file: Optional[Path] = None
    constitution_file: Optional[Path] = None
    templates_dir: Optional[Path] = None
    available_docs: list[str] = field(default_factory=list)
    branch_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for JSON serialization."""
        return {
            "feature_description": self.feature_description,
            "feature_dir": str(self.feature_dir) if self.feature_dir else None,
            "spec_file": str(self.spec_file) if self.spec_file else None,
            "plan_file": str(self.plan_file) if self.plan_file else None,
            "tasks_file": str(self.tasks_file) if self.tasks_file else None,
            "constitution_file": str(self.constitution_file) if self.constitution_file else None,
            "templates_dir": str(self.templates_dir) if self.templates_dir else None,
            "available_docs": self.available_docs,
            "branch_name": self.branch_name,
        }

    def to_json(self) -> str:
        """Serialize context to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class SwarmConfig:
    """Configuration for a claude-flow swarm execution."""
    strategy: SwarmStrategy
    mode: ExecutionMode
    prompt: str
    context: SDDContext
    parallel: bool = False
    agents: list[str] = field(default_factory=list)
    max_workers: int = 4
    timeout: int = 300  # seconds

    def to_command_args(self) -> list[str]:
        """Generate claude-flow CLI arguments."""
        args = []

        if self.mode == ExecutionMode.SWARM:
            args.extend(["swarm", "--strategy", self.strategy.value])
        elif self.mode == ExecutionMode.HIVE:
            args.extend(["hive", "--parallel"])
            if self.max_workers > 1:
                args.extend(["--workers", str(self.max_workers)])

        # Add context as environment or file
        args.extend(["--context", self.context.to_json()])

        # Add prompt
        args.extend(["--prompt", self.prompt])

        # Add timeout
        args.extend(["--timeout", str(self.timeout)])

        return args


class ClaudeFlowAdapter:
    """
    Adapter that bridges SDD commands to claude-flow swarms.

    This adapter:
    1. Checks if claude-flow CLI is available
    2. Maps SDD commands to appropriate swarm strategies
    3. Generates swarm commands with SDD template context
    4. Handles output from swarm back to SDD workflow
    """

    CLAUDE_FLOW_COMMANDS = ["claude-flow", "npx", "claude-flow"]

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the adapter.

        Args:
            project_root: Root directory of the SDD project. Defaults to cwd.
        """
        self.project_root = project_root or Path.cwd()
        self._claude_flow_path: Optional[str] = None
        self._version: Optional[str] = None

    def check_availability(self) -> tuple[bool, str]:
        """
        Check if claude-flow CLI is available on the system.

        Returns:
            Tuple of (is_available, message)
        """
        # First try direct claude-flow command
        if shutil.which("claude-flow"):
            self._claude_flow_path = "claude-flow"
            try:
                result = subprocess.run(
                    ["claude-flow", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self._version = result.stdout.strip()
                    return True, f"claude-flow found (version: {self._version})"
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            return True, "claude-flow found"

        # Try via npx
        if shutil.which("npx"):
            try:
                result = subprocess.run(
                    ["npx", "--yes", "claude-flow", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    self._claude_flow_path = "npx --yes claude-flow"
                    self._version = result.stdout.strip()
                    return True, f"claude-flow available via npx (version: {self._version})"
            except subprocess.TimeoutExpired:
                return False, "claude-flow via npx timed out"
            except Exception as e:
                return False, f"Error checking npx: {e}"

        return False, (
            "claude-flow not found. Install via:\n"
            "  npm install -g @anthropic/claude-flow\n"
            "or use npx: npx @anthropic/claude-flow"
        )

    def _get_command_base(self) -> list[str]:
        """Get the base command for claude-flow."""
        if self._claude_flow_path is None:
            self.check_availability()

        if self._claude_flow_path:
            return self._claude_flow_path.split()
        return ["claude-flow"]

    def _load_sdd_context(self, feature_description: str = "") -> SDDContext:
        """
        Load SDD context from the current project.

        Args:
            feature_description: Optional feature description from user.

        Returns:
            SDDContext with populated paths and data.
        """
        context = SDDContext(feature_description=feature_description)

        # Find common SDD paths
        memory_dir = self.project_root / "memory"
        templates_dir = self.project_root / ".specify" / "templates"
        if not templates_dir.exists():
            templates_dir = self.project_root / "templates"

        specs_dir = self.project_root / "specs"

        # Set templates directory
        if templates_dir.exists():
            context.templates_dir = templates_dir

        # Set constitution file
        constitution = memory_dir / "constitution.md"
        if constitution.exists():
            context.constitution_file = constitution

        # Try to detect current feature from git branch
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                context.branch_name = branch

                # Look for feature directory based on branch
                if specs_dir.exists() and branch:
                    feature_dir = specs_dir / branch
                    if feature_dir.exists():
                        context.feature_dir = feature_dir

                        # Check for standard SDD files
                        if (feature_dir / "spec.md").exists():
                            context.spec_file = feature_dir / "spec.md"
                            context.available_docs.append("spec.md")

                        if (feature_dir / "plan.md").exists():
                            context.plan_file = feature_dir / "plan.md"
                            context.available_docs.append("plan.md")

                        if (feature_dir / "tasks.md").exists():
                            context.tasks_file = feature_dir / "tasks.md"
                            context.available_docs.append("tasks.md")

                        # Check for other docs
                        for doc in ["research.md", "data-model.md", "quickstart.md"]:
                            if (feature_dir / doc).exists():
                                context.available_docs.append(doc)

                        # Check for contracts
                        contracts_dir = feature_dir / "contracts"
                        if contracts_dir.exists() and any(contracts_dir.iterdir()):
                            context.available_docs.append("contracts/")

        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

        return context

    def _build_prompt_for_specify(self, context: SDDContext) -> str:
        """Build the swarm prompt for the specify command."""
        prompt = f"""You are a RESEARCHER swarm working on specification creation for a Spec-Driven Development project.

## Feature Description
{context.feature_description}

## Your Task
Use the researcher strategy to:
1. Analyze the feature description and extract key requirements
2. Research similar implementations and best practices
3. Identify potential user scenarios and edge cases
4. Generate a comprehensive specification following SDD principles

## Guidelines
- Focus on WHAT users need and WHY
- Avoid implementation details (no tech stack, APIs, code structure)
- Write for business stakeholders, not developers
- Include measurable success criteria
- Identify clear acceptance criteria

## Output
Generate a specification document following the SDD spec-template structure with:
- Overview and objectives
- User scenarios and acceptance criteria
- Functional requirements
- Success criteria (measurable, technology-agnostic)
- Assumptions and dependencies
"""

        if context.constitution_file and context.constitution_file.exists():
            prompt += f"\n## Constitutional Principles\nRefer to: {context.constitution_file}\n"

        return prompt

    def _build_prompt_for_plan(self, context: SDDContext) -> str:
        """Build the swarm prompt for the plan command."""
        prompt = """You are an ARCHITECT swarm working on implementation planning for a Spec-Driven Development project.

## Your Task
Use the architect strategy to:
1. Analyze the feature specification
2. Design the technical architecture
3. Define data models and API contracts
4. Create an implementation roadmap

## Context
"""

        if context.spec_file and context.spec_file.exists():
            prompt += f"- Specification: {context.spec_file}\n"

        if context.constitution_file and context.constitution_file.exists():
            prompt += f"- Constitutional principles: {context.constitution_file}\n"

        prompt += """
## Output Artifacts
Generate the following planning documents:
1. plan.md - Technical implementation plan
2. data-model.md - Entity definitions and relationships
3. contracts/ - API specifications (OpenAPI/GraphQL)
4. research.md - Technical decisions and rationale
5. quickstart.md - Integration scenarios

## Guidelines
- Respect constitutional principles
- Design for testability and maintainability
- Document all technical decisions with rationale
- Consider scalability and performance requirements
"""

        return prompt

    def _build_prompt_for_tasks(self, context: SDDContext) -> str:
        """Build the swarm prompt for the tasks command."""
        prompt = """You are a DEVELOPMENT swarm working on task generation for a Spec-Driven Development project.

## Your Task
Use the development strategy to:
1. Break down the implementation plan into executable tasks
2. Organize tasks by user story for incremental delivery
3. Define dependencies and parallel execution opportunities
4. Create a tasks.md file ready for implementation

## Context
"""

        if context.plan_file and context.plan_file.exists():
            prompt += f"- Implementation plan: {context.plan_file}\n"

        if context.spec_file and context.spec_file.exists():
            prompt += f"- Feature specification: {context.spec_file}\n"

        for doc in context.available_docs:
            if doc not in ["spec.md", "plan.md", "tasks.md"]:
                prompt += f"- {doc}: {context.feature_dir / doc if context.feature_dir else doc}\n"

        prompt += """
## Task Format Requirements
Every task MUST follow this format:
- [ ] [TaskID] [P?] [Story?] Description with file path

Where:
- Checkbox: Always start with `- [ ]`
- Task ID: Sequential (T001, T002, T003...)
- [P] marker: Include if task is parallelizable
- [Story] label: Required for user story tasks ([US1], [US2], etc.)
- Description: Clear action with exact file path

## Phase Structure
- Phase 1: Setup (project initialization)
- Phase 2: Foundational (blocking prerequisites)
- Phase 3+: User Stories in priority order
- Final Phase: Polish & cross-cutting concerns

## Output
Generate tasks.md with complete task breakdown ready for execution.
"""

        return prompt

    def _build_prompt_for_implement(self, context: SDDContext) -> str:
        """Build the swarm prompt for the implement command."""
        prompt = """You are a HIVE-MIND swarm working on parallel implementation for a Spec-Driven Development project.

## Your Task
Execute the implementation plan using parallel processing:
1. Parse tasks.md and identify parallel execution opportunities
2. Execute tasks respecting dependencies
3. Coordinate between parallel workers
4. Report progress and handle errors

## Context
"""

        if context.tasks_file and context.tasks_file.exists():
            prompt += f"- Tasks file: {context.tasks_file}\n"

        if context.plan_file and context.plan_file.exists():
            prompt += f"- Implementation plan: {context.plan_file}\n"

        for doc in context.available_docs:
            if doc not in ["tasks.md", "plan.md"]:
                doc_path = context.feature_dir / doc if context.feature_dir else doc
                prompt += f"- {doc}: {doc_path}\n"

        prompt += """
## Execution Rules
1. Execute tasks phase-by-phase
2. Respect task dependencies (sequential before parallel)
3. Tasks marked [P] can run in parallel if they touch different files
4. Follow TDD: test tasks before implementation tasks
5. Mark completed tasks as [X] in tasks.md

## Error Handling
- Halt on sequential task failures
- Continue parallel tasks, report failed ones
- Provide clear error context for debugging

## Output
- Progress reports after each task/phase
- Updated tasks.md with completion status
- Summary of completed work and any issues
"""

        return prompt

    def map_specify(self, feature_description: str) -> SwarmConfig:
        """
        Map /speckit.specify command to claude-flow swarm with researcher strategy.

        Args:
            feature_description: Natural language feature description.

        Returns:
            SwarmConfig for the researcher swarm.
        """
        context = self._load_sdd_context(feature_description)
        prompt = self._build_prompt_for_specify(context)

        return SwarmConfig(
            strategy=SwarmStrategy.RESEARCHER,
            mode=ExecutionMode.SWARM,
            prompt=prompt,
            context=context,
            parallel=False,
            agents=["analyst", "researcher", "writer"],
            timeout=600,
        )

    def map_plan(self) -> SwarmConfig:
        """
        Map /speckit.plan command to claude-flow swarm with architect strategy.

        Returns:
            SwarmConfig for the architect swarm.
        """
        context = self._load_sdd_context()
        prompt = self._build_prompt_for_plan(context)

        return SwarmConfig(
            strategy=SwarmStrategy.ARCHITECT,
            mode=ExecutionMode.SWARM,
            prompt=prompt,
            context=context,
            parallel=False,
            agents=["architect", "designer", "researcher"],
            timeout=900,
        )

    def map_tasks(self) -> SwarmConfig:
        """
        Map /speckit.tasks command to claude-flow swarm with development strategy.

        Returns:
            SwarmConfig for the development swarm.
        """
        context = self._load_sdd_context()
        prompt = self._build_prompt_for_tasks(context)

        return SwarmConfig(
            strategy=SwarmStrategy.DEVELOPMENT,
            mode=ExecutionMode.SWARM,
            prompt=prompt,
            context=context,
            parallel=False,
            agents=["planner", "developer", "tester"],
            timeout=600,
        )

    def map_implement(self) -> SwarmConfig:
        """
        Map /speckit.implement command to claude-flow hive-mind with parallel execution.

        Returns:
            SwarmConfig for the hive-mind execution.
        """
        context = self._load_sdd_context()
        prompt = self._build_prompt_for_implement(context)

        return SwarmConfig(
            strategy=SwarmStrategy.HIVE_MIND,
            mode=ExecutionMode.HIVE,
            prompt=prompt,
            context=context,
            parallel=True,
            agents=["developer", "tester", "reviewer"],
            max_workers=4,
            timeout=1800,  # 30 minutes for implementation
        )

    def generate_command(self, config: SwarmConfig) -> list[str]:
        """
        Generate the full claude-flow command from a SwarmConfig.

        Args:
            config: SwarmConfig with all execution parameters.

        Returns:
            List of command arguments ready for subprocess.
        """
        base = self._get_command_base()
        args = config.to_command_args()
        return base + args

    def execute_swarm(
        self,
        config: SwarmConfig,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> tuple[bool, str]:
        """
        Execute a claude-flow swarm with the given configuration.

        Args:
            config: SwarmConfig specifying the swarm parameters.
            dry_run: If True, only show the command without executing.
            verbose: If True, show detailed output.

        Returns:
            Tuple of (success, output_or_error_message)
        """
        # Check availability first
        available, msg = self.check_availability()
        if not available:
            return False, msg

        command = self.generate_command(config)

        if dry_run:
            return True, f"Would execute: {' '.join(command)}"

        if verbose:
            console.print(f"[cyan]Executing:[/cyan] {' '.join(command[:3])}...")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=config.timeout,
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, f"Swarm execution failed: {error_msg}"

        except subprocess.TimeoutExpired:
            return False, f"Swarm execution timed out after {config.timeout}s"
        except Exception as e:
            return False, f"Error executing swarm: {e}"

    def handle_swarm_output(
        self,
        output: str,
        config: SwarmConfig,
    ) -> dict[str, Any]:
        """
        Process and integrate swarm output back into the SDD workflow.

        Args:
            output: Raw output from the claude-flow swarm.
            config: The SwarmConfig that was executed.

        Returns:
            Dictionary with processed results and next steps.
        """
        result = {
            "strategy": config.strategy.value,
            "mode": config.mode.value,
            "raw_output": output,
            "artifacts": [],
            "next_command": None,
        }

        # Parse output for generated artifacts
        if config.strategy == SwarmStrategy.RESEARCHER:
            result["next_command"] = "/speckit.plan"
            if config.context.feature_dir:
                spec_file = config.context.feature_dir / "spec.md"
                if spec_file.exists():
                    result["artifacts"].append(str(spec_file))

        elif config.strategy == SwarmStrategy.ARCHITECT:
            result["next_command"] = "/speckit.tasks"
            if config.context.feature_dir:
                for artifact in ["plan.md", "data-model.md", "research.md", "quickstart.md"]:
                    artifact_path = config.context.feature_dir / artifact
                    if artifact_path.exists():
                        result["artifacts"].append(str(artifact_path))
                contracts_dir = config.context.feature_dir / "contracts"
                if contracts_dir.exists():
                    result["artifacts"].append(str(contracts_dir))

        elif config.strategy == SwarmStrategy.DEVELOPMENT:
            result["next_command"] = "/speckit.implement"
            if config.context.feature_dir:
                tasks_file = config.context.feature_dir / "tasks.md"
                if tasks_file.exists():
                    result["artifacts"].append(str(tasks_file))

        elif config.strategy == SwarmStrategy.HIVE_MIND:
            result["next_command"] = None  # Implementation complete

        return result


# Typer CLI App for the flow subcommand
flow_app = typer.Typer(
    name="flow",
    help="Bridge SDD commands to claude-flow swarms for orchestrated execution",
    add_completion=False,
)


def _display_status(adapter: ClaudeFlowAdapter) -> None:
    """Display claude-flow status and configuration."""
    available, msg = adapter.check_availability()

    status_icon = "[green]Available[/green]" if available else "[red]Not Available[/red]"
    console.print(Panel(
        f"Status: {status_icon}\n{msg}",
        title="Claude Flow Integration",
        border_style="cyan" if available else "red",
    ))


def _display_command_mapping() -> None:
    """Display the SDD to claude-flow command mapping."""
    table = Table(title="SDD to Claude-Flow Mapping")
    table.add_column("SDD Command", style="cyan")
    table.add_column("Claude-Flow Strategy", style="green")
    table.add_column("Execution Mode", style="yellow")

    table.add_row("/speckit.specify", "researcher", "swarm")
    table.add_row("/speckit.plan", "architect", "swarm")
    table.add_row("/speckit.tasks", "development", "swarm")
    table.add_row("/speckit.implement", "hive-mind", "hive (parallel)")

    console.print(table)


@flow_app.command("status")
def flow_status():
    """Check claude-flow availability and show command mappings."""
    adapter = ClaudeFlowAdapter()
    _display_status(adapter)
    console.print()
    _display_command_mapping()


@flow_app.command("specify")
def flow_specify(
    feature_description: str = typer.Argument(..., help="Natural language feature description"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Execute /speckit.specify via claude-flow researcher swarm.

    Maps to claude-flow swarm with researcher strategy for:
    - Requirements analysis
    - Best practices research
    - Specification generation
    """
    adapter = ClaudeFlowAdapter()
    config = adapter.map_specify(feature_description)

    if verbose:
        console.print(Panel(
            f"Strategy: {config.strategy.value}\n"
            f"Mode: {config.mode.value}\n"
            f"Agents: {', '.join(config.agents)}\n"
            f"Timeout: {config.timeout}s",
            title="Swarm Configuration",
            border_style="cyan",
        ))

    success, output = adapter.execute_swarm(config, dry_run=dry_run, verbose=verbose)

    if success:
        console.print(f"[green]Success:[/green] {output if dry_run else 'Specification created'}")
        if not dry_run:
            result = adapter.handle_swarm_output(output, config)
            if result["artifacts"]:
                console.print(f"[cyan]Artifacts:[/cyan] {', '.join(result['artifacts'])}")
            if result["next_command"]:
                console.print(f"[yellow]Next step:[/yellow] {result['next_command']}")
    else:
        console.print(f"[red]Error:[/red] {output}")
        raise typer.Exit(1)


@flow_app.command("plan")
def flow_plan(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Execute /speckit.plan via claude-flow architect swarm.

    Maps to claude-flow swarm with architect strategy for:
    - Technical architecture design
    - Data model definition
    - API contract generation
    """
    adapter = ClaudeFlowAdapter()
    config = adapter.map_plan()

    if not config.context.spec_file:
        console.print("[red]Error:[/red] No specification found. Run '/speckit.specify' first.")
        raise typer.Exit(1)

    if verbose:
        console.print(Panel(
            f"Strategy: {config.strategy.value}\n"
            f"Mode: {config.mode.value}\n"
            f"Spec: {config.context.spec_file}\n"
            f"Agents: {', '.join(config.agents)}\n"
            f"Timeout: {config.timeout}s",
            title="Swarm Configuration",
            border_style="cyan",
        ))

    success, output = adapter.execute_swarm(config, dry_run=dry_run, verbose=verbose)

    if success:
        console.print(f"[green]Success:[/green] {output if dry_run else 'Implementation plan created'}")
        if not dry_run:
            result = adapter.handle_swarm_output(output, config)
            if result["artifacts"]:
                console.print(f"[cyan]Artifacts:[/cyan] {', '.join(result['artifacts'])}")
            if result["next_command"]:
                console.print(f"[yellow]Next step:[/yellow] {result['next_command']}")
    else:
        console.print(f"[red]Error:[/red] {output}")
        raise typer.Exit(1)


@flow_app.command("tasks")
def flow_tasks(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Execute /speckit.tasks via claude-flow development swarm.

    Maps to claude-flow swarm with development strategy for:
    - Task breakdown and organization
    - Dependency analysis
    - Parallel execution planning
    """
    adapter = ClaudeFlowAdapter()
    config = adapter.map_tasks()

    if not config.context.plan_file:
        console.print("[red]Error:[/red] No implementation plan found. Run '/speckit.plan' first.")
        raise typer.Exit(1)

    if verbose:
        console.print(Panel(
            f"Strategy: {config.strategy.value}\n"
            f"Mode: {config.mode.value}\n"
            f"Plan: {config.context.plan_file}\n"
            f"Agents: {', '.join(config.agents)}\n"
            f"Timeout: {config.timeout}s",
            title="Swarm Configuration",
            border_style="cyan",
        ))

    success, output = adapter.execute_swarm(config, dry_run=dry_run, verbose=verbose)

    if success:
        console.print(f"[green]Success:[/green] {output if dry_run else 'Task list created'}")
        if not dry_run:
            result = adapter.handle_swarm_output(output, config)
            if result["artifacts"]:
                console.print(f"[cyan]Artifacts:[/cyan] {', '.join(result['artifacts'])}")
            if result["next_command"]:
                console.print(f"[yellow]Next step:[/yellow] {result['next_command']}")
    else:
        console.print(f"[red]Error:[/red] {output}")
        raise typer.Exit(1)


@flow_app.command("implement")
def flow_implement(
    workers: int = typer.Option(4, "--workers", "-w", help="Number of parallel workers"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show command without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Execute /speckit.implement via claude-flow hive-mind with parallel execution.

    Maps to claude-flow hive mode for:
    - Parallel task execution
    - Coordinated implementation
    - Progress tracking and error handling
    """
    adapter = ClaudeFlowAdapter()
    config = adapter.map_implement()
    config.max_workers = workers

    if not config.context.tasks_file:
        console.print("[red]Error:[/red] No tasks file found. Run '/speckit.tasks' first.")
        raise typer.Exit(1)

    if verbose:
        console.print(Panel(
            f"Strategy: {config.strategy.value}\n"
            f"Mode: {config.mode.value} (parallel)\n"
            f"Tasks: {config.context.tasks_file}\n"
            f"Workers: {config.max_workers}\n"
            f"Agents: {', '.join(config.agents)}\n"
            f"Timeout: {config.timeout}s",
            title="Hive-Mind Configuration",
            border_style="cyan",
        ))

    success, output = adapter.execute_swarm(config, dry_run=dry_run, verbose=verbose)

    if success:
        console.print(f"[green]Success:[/green] {output if dry_run else 'Implementation complete'}")
        if not dry_run:
            result = adapter.handle_swarm_output(output, config)
            console.print("[green]All tasks executed. Review the implementation and run tests.[/green]")
    else:
        console.print(f"[red]Error:[/red] {output}")
        raise typer.Exit(1)


@flow_app.callback()
def flow_callback(ctx: typer.Context):
    """
    Bridge SDD commands to claude-flow swarms.

    This command group provides integration between Spec-Driven Development
    workflow commands and claude-flow's orchestration capabilities.
    """
    if ctx.invoked_subcommand is None:
        _display_status(ClaudeFlowAdapter())
        console.print()
        _display_command_mapping()
        console.print()
        console.print("[dim]Run 'specify flow --help' for available subcommands[/dim]")
