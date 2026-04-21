"""Motivation, celebration, and encouragement."""

from datetime import datetime
from strands import tool


@tool
def hype_me_up(context: str = "") -> str:
    """Get a personalised motivational boost.

    Args:
        context: What you need hyping up for (e.g. "about to record my first
                 YouTube video", "feeling imposter syndrome", "tired but need
                 to study").

    Returns:
        Context for the agent to generate a tailored motivational message.
    """
    now = datetime.now()
    time_of_day = (
        "morning" if now.hour < 12
        else "afternoon" if now.hour < 17
        else "evening" if now.hour < 21
        else "late night"
    )

    parts = [
        f"Time of day: {time_of_day}",
        f"Day: {now.strftime('%A')}",
    ]

    if context:
        parts.append(f"Situation: {context}")
    else:
        parts.append(
            "No specific context. Give a general motivational boost "
            "reminding Itumeleng of her achievements and potential."
        )

    parts.append(
        "Key achievements to reference: 13x AWS certified, BSc student, "
        "SheBuild Mentorship Program Manager, YouTube creator, community "
        "builder. Remind her that consistency is what got her here."
    )

    return "
".join(parts)


@tool
def celebrate_win(win_description: str, category: str = "general") -> str:
    """Celebrate an achievement, big or small.

    Args:
        win_description: What you accomplished (e.g. "posted my first YouTube video",
                         "studied for 2 hours straight", "hit a 7 day coding streak").
        category: Type of win (e.g. "career", "learning", "personal", "community",
                  "health", "content").

    Returns:
        Context for the agent to generate a celebration message.
    """
    return (
        f"Win: {win_description}
"
        f"Category: {category}
"
        f"Date: {datetime.now().strftime('%Y-%m-%d')}
"
        "Celebrate this! Acknowledge the effort, connect it to the bigger "
        "journey, and encourage Itumeleng to keep going."
    )

