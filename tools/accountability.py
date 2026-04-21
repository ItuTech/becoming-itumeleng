"""Personal brand consistency and messaging guidance."""

import os
import yaml
from strands import tool

BRAND_DEFAULTS = {
    "name": "Itumeleng Mokgako",
    "channel_name": "Chronicles of a Curious Techie",
    "slogan": "Learning is the lifestyle.",
    "greeting": "Hi techies!",
    "handles": {
        "youtube": "@itushares",
        "medium": "@ituwrites",
        "linkedin": "linkedin.com/in/itumeleng-mokgako-a23b5a317",
    },
    "credentials": [
        "BSc student",
        "13x AWS certified",
        "AWS SheBuild Mentorship Program Manager 2026, EMEA",
    ],
    "tone": [
        "Warm and conversational",
        "Honest and transparent",
        "Encouraging but real",
        "Never corporate or stiff",
        "No dashes in written content",
    ],
    "topics": [
        "AWS certifications and exam experiences",
        "Tech banter and building in public",
        "Event vlogs and tech community content",
        "Navigating corporate life",
        "Motivational talks on consistency and growth",
        "Free will vlogs: life beyond the screen",
    ],
    "color_palette": {
        "navy": "#1B2A4A",
        "lavender": "#9B8FBB",
        "gold": "#D4A843",
        "white": "#FFFFFF",
    },
}


def _load_brand() -> dict:
    """Load brand guidelines, falling back to defaults if no file exists."""
    brand_path = os.environ.get("BRAND_FILE", "data/brand.yaml")
    try:
        with open(brand_path, "r") as f:
            brand = yaml.safe_load(f)
        if brand:
            return {**BRAND_DEFAULTS, **brand}
    except FileNotFoundError:
        pass
    return BRAND_DEFAULTS


@tool
def brand_guide(
    platform: str,
    content_type: str,
    topic: str = "",
    audience: str = "",
) -> str:
    """Get brand guidance for creating content on a specific platform.

    Args:
        platform: Where the content will live (e.g. "linkedin", "youtube", "medium").
        content_type: What kind of content (e.g. "post", "bio", "video_script",
                      "blog", "comment", "introduction").
        topic: What the content is about.
        audience: Who it's for (e.g. "tech professionals", "students",
                  "mixed tech and non-tech").

    Returns:
        Brand context for the agent to generate on-brand content guidance.
    """
    brand = _load_brand()

    parts = [
        f"Platform: {platform}",
        f"Content type: {content_type}",
        f"Brand guidelines:
{yaml.dump(brand, default_flow_style=False)}",
    ]
    if topic:
        parts.append(f"Topic: {topic}")
    if audience:
        parts.append(f"Target audience: {audience}")

    return "
".join(parts)

