"""Goal tracking, progress check-ins, and accountability."""

import os
import yaml
from datetime import datetime
from strands import tool
from exceptions import GoalNotFoundError


def _load_goals() -> dict:
    """Load goals from file."""
    goals_path = os.environ.get("GOALS_FILE", "data/goals.yaml")
    try:
        with open(goals_path, "r") as f:
            goals = yaml.safe_load(f)
        return goals if goals else {"goals": []}
    except FileNotFoundError:
        return {"goals": []}


def _save_goals(goals: dict) -> None:
    """Persist goals back to file."""
    goals_path = os.environ.get("GOALS_FILE", "data/goals.yaml")
    os.makedirs(os.path.dirname(goals_path), exist_ok=True)
    with open(goals_path, "w") as f:
        yaml.dump(goals, f, default_flow_style=False)


@tool
def check_goals() -> str:
    """Review all current goals and see where things stand.

    Returns:
        A summary of every goal with its status and any progress notes.
    """
    goals = _load_goals()

    if not goals.get("goals"):
        return "No goals set yet. What are you working towards? Let's map it out."

    lines = ["Here's where your goals stand:
"]
    for i, goal in enumerate(goals["goals"], 1):
        status_icon = {
            "in_progress": "🔄",
            "completed": "✅",
            "paused": "⏸️",
        }.get(goal.get("status", "in_progress"), "❓")

        lines.append(
            f"{i}. {status_icon} {goal['name']}
"
            f"   What: {goal.get('description', 'No description')}
"
            f"   Status: {goal.get('status', 'in_progress')}
"
            f"   Due: {goal.get('target_date', 'No deadline set')}
"
            f"   Notes: {goal.get('progress_notes', [])}
"
        )

    return "
".join(lines)


@tool
def update_goal(goal_name: str, status: str = "", progress_note: str = "") -> str:
    """Update a goal's status or add a progress note.

    Args:
        goal_name: Which goal to update.
        status: New status if changing (e.g. "in_progress", "completed", "paused").
        progress_note: A note on what progress was made.

    Returns:
        Confirmation of the update.
    """
    goals = _load_goals()

    for goal in goals.get("goals", []):
        if goal["name"].lower() == goal_name.lower():
            if status:
                goal["status"] = status
            if progress_note:
                if "progress_notes" not in goal:
                    goal["progress_notes"] = []
                goal["progress_notes"].append(
                    f"[{datetime.now().strftime('%Y-%m-%d')}] {progress_note}"
                )
            _save_goals(goals)
            return f"Updated: {goal['name']}. Status: {goal.get('status')}. Keep going! 💪"

    raise GoalNotFoundError(f"Could not find a goal called '{goal_name}'. Double check the name.")


@tool
def add_goal(name: str, description: str, target_date: str = "") -> str:
    """Set a new goal to track.

    Args:
        name: What to call this goal.
        description: What you want to achieve.
        target_date: When you want to achieve it by (YYYY-MM-DD).

    Returns:
        Confirmation that the goal has been added.
    """
    goals = _load_goals()

    new_goal = {
        "name": name,
        "description": description,
        "status": "in_progress",
        "progress_notes": [],
        "created_at": datetime.now().isoformat(),
    }
    if target_date:
        new_goal["target_date"] = target_date

    goals.setdefault("goals", []).append(new_goal)
    _save_goals(goals)

    return f"Goal added: {name}. Let's make it happen! 🚀"

