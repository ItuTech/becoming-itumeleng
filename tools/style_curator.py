"""Outfit and personal style recommendations."""

import os
import yaml
from strands import tool
from exceptions import WardrobeEmptyError, DataFileError


def _load_wardrobe() -> dict:
    """Load the wardrobe inventory from file."""
    wardrobe_path = os.environ.get("WARDROBE_FILE", "data/wardrobe.yaml")
    try:
        with open(wardrobe_path, "r") as f:
            wardrobe = yaml.safe_load(f)
        if not wardrobe:
            raise WardrobeEmptyError("Wardrobe inventory is empty.")
        return wardrobe
    except FileNotFoundError:
        raise DataFileError(
            f"Could not find wardrobe file at {wardrobe_path}. "
            "Create one or point WARDROBE_FILE to the right location."
        )


@tool
def style_curator(
    occasion: str,
    weather: str = "",
    mood: str = "",
    constraints: str = "",
) -> str:
    """Recommend outfits and styling choices for a given occasion.

    Args:
        occasion: What you're dressing for (e.g. "tech workshop", "YouTube recording",
                  "networking dinner", "study session at the library").
        weather: What the weather is like (e.g. "warm and sunny", "cold and rainy").
        mood: How you want to feel (e.g. "confident", "cozy", "powerful", "minimal").
        constraints: Anything to keep in mind (e.g. "no heels", "casual only",
                     "must include blazer").

    Returns:
        Contextual information for the agent to generate a personalised recommendation.
    """
    try:
        wardrobe = _load_wardrobe()
    except (WardrobeEmptyError, DataFileError):
        wardrobe = None

    parts = [f"Occasion: {occasion}"]
    if weather:
        parts.append(f"Weather: {weather}")
    if mood:
        parts.append(f"Desired vibe: {mood}")
    if constraints:
        parts.append(f"Constraints: {constraints}")

    if wardrobe:
        parts.append(f"Available wardrobe:
{yaml.dump(wardrobe, default_flow_style=False)}")
    else:
        parts.append(
            "No wardrobe file loaded. Give general style recommendations "
            "based on the occasion and preferences provided."
        )

    return "
".join(parts)

