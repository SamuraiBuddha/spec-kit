#!/usr/bin/env python3
"""
Checkpoint management for Specify implementation tasks.

This module provides functionality to save, load, and manage checkpoints
during the implementation process, enabling resume capability for long-running
implementation tasks.

Checkpoint file format:
    Location: .specify/checkpoints/{feature}.json
    Structure: {
        "feature": "feature-name",
        "tasks": [...],
        "current_task": "T003",
        "completed": ["T001", "T002"],
        "last_updated": "ISO timestamp"
    }
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TypedDict


class CheckpointTask(TypedDict, total=False):
    """Structure for a task in a checkpoint."""
    task_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    description: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    context: Optional[dict]


class CheckpointData(TypedDict, total=False):
    """Structure for checkpoint data."""
    feature: str
    tasks: list[CheckpointTask]
    current_task: Optional[str]
    completed: list[str]
    failed: list[str]
    last_updated: str
    started_at: str
    context: Optional[dict]


def get_checkpoints_dir(base_path: Optional[Path] = None) -> Path:
    """
    Get the checkpoints directory path.

    Args:
        base_path: Base project path. Defaults to current working directory.

    Returns:
        Path to the checkpoints directory.
    """
    if base_path is None:
        base_path = Path.cwd()
    return base_path / ".specify" / "checkpoints"


def get_checkpoint_file(feature: str, base_path: Optional[Path] = None) -> Path:
    """
    Get the checkpoint file path for a feature.

    Args:
        feature: Feature name (used as filename).
        base_path: Base project path. Defaults to current working directory.

    Returns:
        Path to the checkpoint file.
    """
    checkpoints_dir = get_checkpoints_dir(base_path)
    # Sanitize feature name for filename
    safe_feature = "".join(c if c.isalnum() or c in "-_" else "_" for c in feature)
    return checkpoints_dir / f"{safe_feature}.json"


def save_checkpoint(
    feature: str,
    task_id: str,
    status: str,
    context: Optional[dict] = None,
    base_path: Optional[Path] = None,
    tasks: Optional[list[CheckpointTask]] = None,
) -> Path:
    """
    Save a checkpoint for a feature implementation.

    Args:
        feature: Feature name being implemented.
        task_id: Current task ID (e.g., "T003").
        status: Task status ("pending", "in_progress", "completed", "failed").
        context: Optional context data to save with the checkpoint.
        base_path: Base project path. Defaults to current working directory.
        tasks: Optional full task list to save.

    Returns:
        Path to the saved checkpoint file.
    """
    checkpoint_file = get_checkpoint_file(feature, base_path)

    # Ensure directory exists
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing checkpoint or create new one
    checkpoint = load_checkpoint(feature, base_path) or CheckpointData(
        feature=feature,
        tasks=[],
        current_task=None,
        completed=[],
        failed=[],
        started_at=datetime.now(timezone.utc).isoformat(),
        context={},
    )

    # Update checkpoint
    now = datetime.now(timezone.utc).isoformat()
    checkpoint["last_updated"] = now
    checkpoint["current_task"] = task_id

    # Update tasks list if provided
    if tasks is not None:
        checkpoint["tasks"] = tasks

    # Update task status in the tasks list
    task_found = False
    for task in checkpoint.get("tasks", []):
        if task.get("task_id") == task_id:
            task["status"] = status
            if status == "in_progress":
                task["started_at"] = now
            elif status == "completed":
                task["completed_at"] = now
                if task_id not in checkpoint.get("completed", []):
                    checkpoint.setdefault("completed", []).append(task_id)
            elif status == "failed":
                if task_id not in checkpoint.get("failed", []):
                    checkpoint.setdefault("failed", []).append(task_id)
            task_found = True
            break

    # If task not found in list, add it
    if not task_found:
        new_task: CheckpointTask = {
            "task_id": task_id,
            "status": status,
            "description": "",
        }
        if status == "in_progress":
            new_task["started_at"] = now
        elif status == "completed":
            new_task["completed_at"] = now
            checkpoint.setdefault("completed", []).append(task_id)
        elif status == "failed":
            checkpoint.setdefault("failed", []).append(task_id)
        checkpoint.setdefault("tasks", []).append(new_task)

    # Update context if provided
    if context is not None:
        checkpoint["context"] = {**checkpoint.get("context", {}), **context}

    # Write checkpoint file
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
        f.write("\n")

    return checkpoint_file


def load_checkpoint(feature: str, base_path: Optional[Path] = None) -> Optional[CheckpointData]:
    """
    Load a checkpoint for a feature.

    Args:
        feature: Feature name to load checkpoint for.
        base_path: Base project path. Defaults to current working directory.

    Returns:
        Checkpoint data if found, None otherwise.
    """
    checkpoint_file = get_checkpoint_file(feature, base_path)

    if not checkpoint_file.exists():
        return None

    try:
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return CheckpointData(**data)
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        # Invalid checkpoint file, return None
        return None


def clear_checkpoints(feature: str, base_path: Optional[Path] = None) -> bool:
    """
    Clear (delete) the checkpoint for a feature.

    Args:
        feature: Feature name to clear checkpoint for.
        base_path: Base project path. Defaults to current working directory.

    Returns:
        True if checkpoint was deleted, False if it didn't exist.
    """
    checkpoint_file = get_checkpoint_file(feature, base_path)

    if checkpoint_file.exists():
        checkpoint_file.unlink()
        return True
    return False


def list_checkpoints(base_path: Optional[Path] = None) -> list[dict]:
    """
    List all available checkpoints.

    Args:
        base_path: Base project path. Defaults to current working directory.

    Returns:
        List of checkpoint summaries with feature name, status, and progress.
    """
    checkpoints_dir = get_checkpoints_dir(base_path)

    if not checkpoints_dir.exists():
        return []

    checkpoints = []
    for checkpoint_file in checkpoints_dir.glob("*.json"):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            total_tasks = len(data.get("tasks", []))
            completed_tasks = len(data.get("completed", []))
            failed_tasks = len(data.get("failed", []))

            checkpoints.append({
                "feature": data.get("feature", checkpoint_file.stem),
                "current_task": data.get("current_task"),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "progress_percent": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "last_updated": data.get("last_updated"),
                "file_path": str(checkpoint_file),
            })
        except (json.JSONDecodeError, TypeError, KeyError):
            # Skip invalid checkpoint files
            continue

    # Sort by last_updated descending
    checkpoints.sort(key=lambda x: x.get("last_updated", ""), reverse=True)

    return checkpoints


def get_next_pending_task(feature: str, base_path: Optional[Path] = None) -> Optional[str]:
    """
    Get the next pending task ID from a checkpoint.

    Args:
        feature: Feature name to check.
        base_path: Base project path. Defaults to current working directory.

    Returns:
        Next pending task ID, or None if no pending tasks.
    """
    checkpoint = load_checkpoint(feature, base_path)
    if checkpoint is None:
        return None

    completed = set(checkpoint.get("completed", []))
    failed = set(checkpoint.get("failed", []))

    for task in checkpoint.get("tasks", []):
        task_id = task.get("task_id")
        if task_id and task_id not in completed and task_id not in failed:
            return task_id

    return None


def get_checkpoint_summary(feature: str, base_path: Optional[Path] = None) -> Optional[dict]:
    """
    Get a summary of a checkpoint for display.

    Args:
        feature: Feature name to summarize.
        base_path: Base project path. Defaults to current working directory.

    Returns:
        Summary dict with progress information, or None if no checkpoint exists.
    """
    checkpoint = load_checkpoint(feature, base_path)
    if checkpoint is None:
        return None

    total_tasks = len(checkpoint.get("tasks", []))
    completed = checkpoint.get("completed", [])
    failed = checkpoint.get("failed", [])

    return {
        "feature": checkpoint.get("feature"),
        "current_task": checkpoint.get("current_task"),
        "total_tasks": total_tasks,
        "completed_count": len(completed),
        "failed_count": len(failed),
        "pending_count": total_tasks - len(completed) - len(failed),
        "progress_percent": (len(completed) / total_tasks * 100) if total_tasks > 0 else 0,
        "completed_tasks": completed,
        "failed_tasks": failed,
        "started_at": checkpoint.get("started_at"),
        "last_updated": checkpoint.get("last_updated"),
    }


def update_task_in_checkpoint(
    feature: str,
    task_id: str,
    status: str,
    error: Optional[str] = None,
    base_path: Optional[Path] = None,
) -> bool:
    """
    Update a specific task's status in a checkpoint.

    Args:
        feature: Feature name.
        task_id: Task ID to update.
        status: New status for the task.
        error: Optional error message if task failed.
        base_path: Base project path.

    Returns:
        True if update succeeded, False if checkpoint or task not found.
    """
    checkpoint = load_checkpoint(feature, base_path)
    if checkpoint is None:
        return False

    now = datetime.now(timezone.utc).isoformat()
    task_found = False

    for task in checkpoint.get("tasks", []):
        if task.get("task_id") == task_id:
            task["status"] = status
            if status == "completed":
                task["completed_at"] = now
                if task_id not in checkpoint.get("completed", []):
                    checkpoint.setdefault("completed", []).append(task_id)
            elif status == "failed":
                if error:
                    task["error"] = error
                if task_id not in checkpoint.get("failed", []):
                    checkpoint.setdefault("failed", []).append(task_id)
            task_found = True
            break

    if not task_found:
        return False

    checkpoint["last_updated"] = now

    checkpoint_file = get_checkpoint_file(feature, base_path)
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
        f.write("\n")

    return True


def initialize_checkpoint_from_tasks(
    feature: str,
    tasks: list[dict],
    base_path: Optional[Path] = None,
) -> Path:
    """
    Initialize a new checkpoint from a list of tasks parsed from tasks.md.

    Args:
        feature: Feature name.
        tasks: List of task dicts with at least 'task_id' and 'description'.
        base_path: Base project path.

    Returns:
        Path to the created checkpoint file.
    """
    checkpoint_tasks: list[CheckpointTask] = []
    for task in tasks:
        checkpoint_task: CheckpointTask = {
            "task_id": task.get("task_id", ""),
            "status": "pending",
            "description": task.get("description", ""),
        }
        if task.get("context"):
            checkpoint_task["context"] = task["context"]
        checkpoint_tasks.append(checkpoint_task)

    checkpoint: CheckpointData = {
        "feature": feature,
        "tasks": checkpoint_tasks,
        "current_task": checkpoint_tasks[0]["task_id"] if checkpoint_tasks else None,
        "completed": [],
        "failed": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "context": {},
    }

    checkpoint_file = get_checkpoint_file(feature, base_path)
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
        f.write("\n")

    return checkpoint_file
