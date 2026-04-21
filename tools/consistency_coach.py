"""Habit tracking, streaks, and routine management."""

import os
import yaml
from datetime import datetime
from strands import tool
from exceptions import HabitNotFoundError


def _load_habits() -> dict:
    """Load habits from file."""
    habits_path = os.path.join("data", "habits.yaml")
    try:
        with open(habits_path, "r") as f:
            habits = yaml.safe_load(f)
        return habits if habits else {"habits": []}
    except FileNotFoundError:
        return {"habits": []}


def _save_habits(habits: dict) -> None:
    """Persist habits back to file."""
    habits_path = os.path.join("data", "habits.yaml")
    os.makedirs(os.path.dirname(habits_path), exist_ok=True)
    with open(habits_path, "w") as f:
        yaml.dump(habits, f, default_flow_style=False)


def _calculate_streak(history: list[str]) -> int:
    """Work out the current consecutive day streak from logged dates."""
    if not history:
        return 0

    dates = sorted(
        [datetime.fromisoformat(d).date() for d in history], reverse=True
    )
    streak = 1
    for i in range(len(dates) - 1):
        if (dates[i] - dates[i + 1]).days == 1:
            streak += 1
        else:
            break
    return streak


@tool
def check_habits() -> str:
    """See all tracked habits and their current streaks.

    Returns:
        A summary of every habit with streak counts and last logged dates.
    """
    habits = _load_habits()

    if not habits.get("habits"):
        return (
            "No habits being tracked yet. What do you want to build into your "
            "routine? Some ideas: morning study session, daily coding, journaling, "
            "exercise, content creation, reading."
        )

    lines = ["Your habits:
"]
    for habit in habits["habits"]:
        streak = _calculate_streak(habit.get("history", []))
        last_logged = habit.get("last_logged", "Never")
        icon = "🔥" if streak >= 7 else "✨" if streak >= 3 else "🌱"

        lines.append(
            f"{icon} {habit['name']} ({habit.get('frequency', 'daily')})
"
            f"   Streak: {streak} days
"
            f"   Last logged: {last_logged}
"
        )

    return "
".join(lines)


@tool
def log_habit(habit_name: str, note: str = "") -> str:
    """Log that you completed a habit today.

    Args:
        habit_name: Which habit you completed.
        note: Optional note about today's session.

    Returns:
        Confirmation with your updated streak.
    """
    habits = _load_habits()
    today = datetime.now().isoformat()

    for habit in habits.get("habits", []):
        if habit["name"].lower() == habit_name.lower():
            if "history" not in habit:
                habit["history"] = []
            habit["history"].append(today)
            habit["last_logged"] = today
            streak = _calculate_streak(habit["history"])
            _save_habits(habits)

            if streak >= 7:
                msg = f"🔥 {streak} day streak on {habit['name']}! You're on fire!"
            elif streak >= 3:
                msg = f"✨ {streak} day streak on {habit['name']}! Momentum is building!"
            else:
                msg = f"🌱 {habit['name']} logged! Streak: {streak}. Every day counts!"

            if note:
                msg += f"
Note: {note}"
            return msg

    raise HabitNotFoundError(
        f"Could not find a habit called '{habit_name}'. Add it first or check the name."
    )

