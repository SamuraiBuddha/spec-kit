# Spec-Kit Development Compendium

This document consolidates the development journey, architectural decisions, and key learnings from building the Spec-Kit framework and its integration with Claude-Flow.

---

## Table of Contents

1. [Project Vision](#project-vision)
2. [SDD Methodology](#sdd-methodology)
3. [Claude-Flow Integration](#claude-flow-integration)
4. [BMAD Integration Analysis](#bmad-integration-analysis)
5. [Development Environment](#development-environment)
6. [Lessons Learned](#lessons-learned)

---

## Project Vision

### What is Spec-Driven Development?

Spec-Driven Development (SDD) **flips the script** on traditional software development. Instead of treating specifications as scaffolding to be discarded once coding begins, SDD makes specifications executable and directly generative of working implementations.

### Core Philosophy

- **Intent-driven development**: Specifications define the "what" before the "how"
- **Rich specification creation**: Using guardrails and organizational principles
- **Multi-step refinement**: Rather than one-shot code generation from prompts
- **Heavy reliance on AI**: Advanced model capabilities for specification interpretation

---

## SDD Methodology

### Workflow Phases

```
1. /speckit.constitution  ─►  Establish project principles
                              ├─ Core values
                              ├─ Development guidelines
                              └─ Quality standards

2. /speckit.specify       ─►  Define WHAT and WHY
                              ├─ User stories
                              ├─ Functional requirements
                              └─ Success criteria

3. /speckit.plan          ─►  Define HOW (tech stack)
                              ├─ Architecture
                              ├─ Data models
                              ├─ API contracts
                              └─ Research notes

4. /speckit.tasks         ─►  Break down into tasks
                              ├─ Ordered by dependency
                              ├─ Parallel markers [P]
                              └─ Checkpoints

5. /speckit.implement     ─►  Execute implementation
                              ├─ TDD approach
                              ├─ Phase execution
                              └─ Progress tracking
```

### Template System

Templates drive the entire workflow:

| Template | Purpose |
|----------|---------|
| `spec-template.md` | Feature specification structure |
| `plan-template.md` | Implementation plan structure |
| `tasks-template.md` | Task breakdown format |
| `constitution.md` | Project principles |

### Task Format

Every task follows the format:
```
- [ ] [TaskID] [P?] [Story?] Description with file path
```

Where:
- `[P]` = Parallelizable
- `[Story]` = User story label (US1, US2, etc.)
- File path included for each task

---

## Claude-Flow Integration

### Integration Architecture

The integration ("Specify-Flow") maps SDD commands to Claude-Flow swarm strategies:

```python
# From claude_flow_adapter.py

class SwarmStrategy(Enum):
    RESEARCHER = "researcher"    # /speckit.specify
    ARCHITECT = "architect"      # /speckit.plan
    DEVELOPMENT = "development"  # /speckit.tasks
    HIVE_MIND = "hive-mind"      # /speckit.implement
```

### Context Passing

SDD context is automatically loaded and passed to Claude-Flow:

```python
@dataclass
class SDDContext:
    feature_description: str
    feature_dir: Optional[Path]
    spec_file: Optional[Path]
    plan_file: Optional[Path]
    tasks_file: Optional[Path]
    constitution_file: Optional[Path]
    templates_dir: Optional[Path]
    available_docs: list[str]
    branch_name: str
```

### Agent Assignments

| Phase | Agents | Focus |
|-------|--------|-------|
| Specify | analyst, researcher, writer | Requirements, patterns, documentation |
| Plan | architect, designer, researcher | Architecture, models, validation |
| Tasks | planner, developer, tester | Breakdown, dependencies, tests |
| Implement | developer, tester, reviewer | Execution, validation, review |

### Benefits Realized

1. **Specialized expertise**: Each phase gets agents optimized for that work type
2. **Parallel execution**: Hive-mind enables concurrent task implementation
3. **Memory persistence**: SQLite storage across sessions
4. **Constitutional enforcement**: Automated compliance checking

---

## BMAD Integration Analysis

### Research Findings

Analysis was conducted on integrating SDD with BMAD (Business, Market, Architect, Develop) agent infrastructure.

### Compatibility Assessment

| Aspect | SDD (Spec Kit) | BMAD Infrastructure | Compatibility |
|--------|----------------|---------------------|---------------|
| Primary Focus | Specs as executable truth | Agent-orchestrated automation | Complementary |
| Workflow Model | Linear (Specify → Plan → Tasks → Implement) | Phased (Business → Market → Architect → Develop) | Alignable |
| Automation | Template-driven with AI | Agent-driven with personas | Synergistic |
| Commands | Slash commands (/specify) | Star commands (*agent) | Combinable |

### Workflow Mapping

```
SDD Command          BMAD Agent Mapping
─────────────────────────────────────────
/specify         →   BMAD Analyst (Mary)
                     - Requirements discovery
                     - Foundational documents

/plan            →   BMAD Architect + PM
                     - Architecture design
                     - Technical specifications

/tasks           →   BMAD Developer agents
                     - Story-driven development
                     - Executable units
```

### Proposed Unified Methodology

**Specification-Driven Agent Development (SDAD)**

Combining:
- SDD's executable specifications and structured templates
- BMAD's intelligent agent orchestration and specialized workflows
- Unified command system supporting both paradigms
- Comprehensive knowledge management through Git and Neo4j

### Integration Phases (Proposed)

1. **Foundation**: Bridge configuration, command interpreter
2. **Agent Enhancement**: SDD template awareness in BMAD agents
3. **Workflow Integration**: Hybrid workflows (BMAD discovery → SDD implementation)
4. **Optimization**: Specialized agents for SDD phases, Neo4j tracking

---

## Development Environment

### DevContainer Configuration

The project includes a comprehensive dev container setup:

```json
// .devcontainer/devcontainer.json
{
  "name": "Spec Kit Development",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "postCreateCommand": ".devcontainer/post-create.sh"
}
```

### Post-Create Setup

The `post-create.sh` script installs:

**AI Agent CLIs**:
- GitHub Copilot
- Claude Code
- Codex CLI
- Gemini CLI
- Auggie CLI
- Qwen CLI
- opencode
- Amazon Q Developer
- CodeBuddy

**Development Tools**:
- UV (Python package manager)
- DocFx (documentation generation)

### Multi-Agent Support

Spec-Kit supports multiple AI coding agents:

| Agent | Status | Notes |
|-------|--------|-------|
| Claude Code | Full support | Primary development |
| GitHub Copilot | Full support | VSCode integration |
| Gemini CLI | Full support | Google's agent |
| Cursor | Full support | IDE integration |
| Qwen Code | Full support | Alibaba's agent |
| opencode | Full support | Community agent |
| Windsurf | Full support | - |
| Kilo Code | Full support | - |
| Auggie CLI | Full support | - |
| CodeBuddy CLI | Full support | - |
| Roo Code | Full support | - |
| Codex CLI | Full support | OpenAI's agent |
| Amazon Q | Partial | No custom slash command args |

---

## Lessons Learned

### Workflow Design

1. **Clarification before planning**: The `/speckit.clarify` step reduces rework downstream
2. **Constitution as foundation**: Project principles guide all subsequent decisions
3. **Template-driven consistency**: Templates ensure output structure across AI agents

### Integration Design

1. **Bidirectional benefits**: Both SDD and Claude-Flow benefit from integration
2. **Context is king**: Passing full SDD context enables intelligent swarm behavior
3. **Strategy mapping**: Each workflow phase maps naturally to a swarm strategy

### Multi-Agent Support

1. **Command consistency**: Slash commands work across agents with minor variations
2. **Script variants**: Bash and PowerShell needed for cross-platform support
3. **Agent detection**: Auto-detection simplifies user experience

### Process

1. **Tech stack later**: Focus on WHAT and WHY before HOW
2. **Constitutional principles**: Prevent scope creep and over-engineering
3. **Incremental delivery**: User stories enable partial feature delivery

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/specify_cli/__init__.py` | Main CLI implementation |
| `src/specify_cli/claude_flow_adapter.py` | Claude-Flow integration |
| `templates/commands/*.md` | Slash command templates |
| `templates/*-template.md` | Output templates |
| `memory/constitution.md` | Project principles |
| `scripts/bash/*.sh` | POSIX automation |
| `scripts/powershell/*.ps1` | Windows automation |

---

*This compendium was consolidated from development notes, integration analysis, and planning documents.*

*Last Updated: January 2026*
