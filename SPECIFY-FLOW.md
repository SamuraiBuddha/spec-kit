# Specify-Flow: Spec-Kit + Claude-Flow Integration

## Overview

**Specify-Flow** is the integration between Spec-Kit's Specification-Driven Development (SDD) framework and Claude-Flow's AI orchestration platform. This integration enables your SDD workflow to leverage intelligent AI swarms for each development phase, bringing specialized agent expertise to specification, planning, task generation, and implementation.

## Why Specify-Flow?

Traditional SDD relies on a single AI assistant working through each phase sequentially. Specify-Flow changes this by:

1. **Specialized Swarms**: Each SDD phase uses a swarm of agents optimized for that task type
2. **Parallel Execution**: Implementation tasks can run concurrently via hive-mind orchestration
3. **Memory Persistence**: All artifacts are stored and tracked across sessions
4. **Constitutional Enforcement**: Automated compliance checking at every phase gate

## Installation

### Prerequisites

1. **Spec-Kit** (already installed if you're reading this)
2. **Claude-Flow** (install via npm):
   ```bash
   npm install -g claude-flow@alpha
   # or use npx without installing
   ```

### Verify Installation

```bash
# Check both tools are available
specify check
specify flow status
```

## Usage

### Quick Start

```bash
# Initialize a new project with SDD
specify init my-project --ai claude

# Navigate to project
cd my-project

# Create specification using Claude-Flow researcher swarm
specify flow specify "Build a photo album organizer with drag-and-drop"

# Generate implementation plan using architect swarm
specify flow plan

# Generate task breakdown using development swarm
specify flow tasks

# Execute implementation using hive-mind parallel execution
specify flow implement --workers 4
```

### Command Reference

| Command | Description | Claude-Flow Strategy |
|---------|-------------|---------------------|
| `specify flow status` | Check Claude-Flow availability | - |
| `specify flow specify "<description>"` | Generate spec from description | Researcher swarm |
| `specify flow plan` | Generate implementation plan | Architect swarm |
| `specify flow tasks` | Generate task breakdown | Development swarm |
| `specify flow implement` | Execute all tasks | Hive-mind parallel |

### Options

```bash
# Dry run - show what would execute without running
specify flow specify "Feature" --dry-run

# Verbose output - show detailed execution info
specify flow plan --verbose

# Custom worker count for implementation
specify flow implement --workers 8
```

## How It Works

### Command Mapping

The `claude_flow_adapter.py` module maps each SDD command to an appropriate Claude-Flow execution strategy:

```
/speckit.specify  ─────►  Claude-Flow Swarm (researcher strategy)
                          Agents: analyst, researcher, writer
                          Focus: Requirements, user scenarios, success criteria

/speckit.plan     ─────►  Claude-Flow Swarm (architect strategy)
                          Agents: architect, designer, researcher
                          Focus: Architecture, data models, API contracts

/speckit.tasks    ─────►  Claude-Flow Swarm (development strategy)
                          Agents: planner, developer, tester
                          Focus: Task breakdown, dependencies, parallel markers

/speckit.implement ────►  Claude-Flow Hive-Mind (parallel execution)
                          Agents: developer, tester, reviewer
                          Focus: Coordinated implementation, progress tracking
```

### Context Passing

The adapter automatically loads SDD context and passes it to Claude-Flow:

```python
SDDContext:
  - feature_description: User's natural language description
  - feature_dir: Path to feature's spec directory
  - spec_file: Path to spec.md (if exists)
  - plan_file: Path to plan.md (if exists)
  - tasks_file: Path to tasks.md (if exists)
  - constitution_file: Path to constitution.md
  - available_docs: List of other available documents
  - branch_name: Current git branch
```

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     User Command                             │
│              specify flow specify "..."                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   ClaudeFlowAdapter                          │
│  1. Load SDD context (constitution, existing docs)          │
│  2. Build swarm prompt with context                         │
│  3. Generate SwarmConfig (strategy, mode, agents)           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Claude-Flow CLI                          │
│  1. Parse swarm configuration                               │
│  2. Spawn specialized agents                                │
│  3. Coordinate via swarm/hive-mind protocol                 │
│  4. Return results                                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Output Processing                          │
│  1. Parse generated artifacts                               │
│  2. Store in SQLite memory (via SpecKitMemoryBridge)        │
│  3. Display next step recommendation                        │
└─────────────────────────────────────────────────────────────┘
```

## Agent Specializations

### Researcher Swarm (specify)

- **Analyst Agent**: Extracts requirements from description
- **Researcher Agent**: Finds best practices and similar implementations
- **Writer Agent**: Generates SDD-compliant specification

### Architect Swarm (plan)

- **Architect Agent**: Designs technical architecture
- **Designer Agent**: Creates data models and contracts
- **Researcher Agent**: Validates technical decisions

### Development Swarm (tasks)

- **Planner Agent**: Breaks down work into phases
- **Developer Agent**: Identifies implementation steps
- **Tester Agent**: Adds test tasks and validation checkpoints

### Hive-Mind (implement)

- **Queen Agent**: Coordinates overall execution
- **Developer Workers**: Execute implementation tasks
- **Tester Workers**: Run tests after implementation
- **Reviewer Workers**: Validate completed work

## Configuration

### Adapter Configuration

The adapter is located at `src/specify_cli/claude_flow_adapter.py` and includes:

```python
class SwarmConfig:
    strategy: SwarmStrategy      # researcher, architect, development, hive_mind
    mode: ExecutionMode          # swarm, hive, sequential
    prompt: str                  # Generated prompt with context
    context: SDDContext          # SDD project context
    parallel: bool               # Enable parallel execution
    agents: list[str]            # Agent types to spawn
    max_workers: int             # Worker count (for hive-mind)
    timeout: int                 # Execution timeout in seconds
```

### Timeout Settings

| Command | Default Timeout | Description |
|---------|-----------------|-------------|
| `specify` | 600s (10 min) | Specification generation |
| `plan` | 900s (15 min) | Architecture planning |
| `tasks` | 600s (10 min) | Task breakdown |
| `implement` | 1800s (30 min) | Full implementation |

## Benefits Over Standard SDD

| Aspect | Standard SDD | Specify-Flow |
|--------|-------------|--------------|
| Execution | Single AI agent | Specialized swarm teams |
| Implementation | Sequential | Parallel via hive-mind |
| Memory | Per-session | Persistent SQLite |
| Learning | None | Neural pattern recognition |
| Coordination | Manual | Automated with hooks |

## Troubleshooting

### Claude-Flow Not Found

```bash
# Check if available
specify flow status

# If not found, install globally
npm install -g claude-flow@alpha

# Or use npx (no install needed)
# The adapter will automatically detect npx availability
```

### Timeout Issues

For large features, increase timeout:
```python
# In claude_flow_adapter.py, modify SwarmConfig
config.timeout = 3600  # 1 hour for complex implementations
```

### Context Not Loading

Ensure you're on the correct git branch:
```bash
git branch --show-current
# Should match your feature branch (e.g., 001-feature-name)
```

## See Also

- [Spec-Kit README](./README.md) - Full Spec-Kit documentation
- [SDD Methodology](./spec-driven.md) - Complete SDD guide
- [Claude-Flow Repository](https://github.com/ruvnet/claude-flow) - AI orchestration platform
- [Constitutional Principles](./memory/constitution.md) - Project guidelines
