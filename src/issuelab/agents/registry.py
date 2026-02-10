"""Agent registry and rules (single source of truth).

This module centralizes:
1) Built-in agent canonical names
2) User agent registry loading from agents/<user>/agent.yml
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Built-in agent names (canonical only)
AGENT_NAMES: dict[str, str] = {
    "moderator": "moderator",
    "reviewer_a": "reviewer_a",
    "reviewer_b": "reviewer_b",
    "summarizer": "summarizer",
    "observer": "observer",
    "arxiv_observer": "arxiv_observer",
    "pubmed_observer": "pubmed_observer",
    "video_manim": "video_manim",
}

BUILTIN_AGENTS: set[str] = {
    "moderator",
    "reviewer_a",
    "reviewer_b",
    "summarizer",
    "observer",
    "arxiv_observer",
    "pubmed_observer",
    "video_manim",
}

AGENT_TYPE_SYSTEM = "system"
AGENT_TYPE_USER = "user"


def normalize_agent_name(name: str) -> str:
    """Normalize agent name using canonical mapping."""
    if not name:
        return name
    return AGENT_NAMES.get(name.lower(), name)


def _normalize_agent_type(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {AGENT_TYPE_SYSTEM, AGENT_TYPE_USER}:
            return cleaned
    return None


def load_registry(agents_dir: Path, include_disabled: bool = False) -> dict[str, dict[str, Any]]:
    """
    Load agent registry from agents/<user>/agent.yml.

    Args:
        agents_dir: agents directory path
        include_disabled: whether to include disabled agents

    Returns:
        username -> config dict
    """
    registry: dict[str, dict[str, Any]] = {}

    if not agents_dir.exists():
        logger.warning("Agents directory not found: %s", agents_dir)
        return registry

    for user_dir in agents_dir.iterdir():
        if not user_dir.is_dir():
            continue
        if user_dir.name.startswith("_"):
            continue

        agent_yml = user_dir / "agent.yml"
        if not agent_yml.exists():
            continue

        try:
            with open(agent_yml, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                logger.warning("Empty config in %s", agent_yml)
                continue

            # Use owner or username as key
            username = config.get("owner") or config.get("username")
            if not username:
                logger.warning("%s missing 'owner' or 'username'", agent_yml)
                continue

            # Skip disabled unless requested
            if not include_disabled and not config.get("enabled", True):
                logger.info("%s is disabled, skipping", username)
                continue

            registry[username] = config

        except yaml.YAMLError as e:
            logger.error("Error parsing %s: %s", agent_yml.name, e)
        except Exception as e:
            logger.error("Error loading %s: %s", agent_yml.name, e)

    return registry


def get_agent_config(
    agent_name: str, agents_dir: Path | None = None, include_disabled: bool = False
) -> dict[str, Any] | None:
    """Get a single agent config by name."""
    if not agent_name:
        return None
    root = agents_dir or Path("agents")
    registry = load_registry(root, include_disabled=include_disabled)
    normalized = agent_name.lower()
    for name, config in registry.items():
        if str(name).lower() == normalized:
            return config
    return None


def is_system_agent(
    agent_name: str, agents_dir: Path | None = None, include_disabled: bool = True
) -> tuple[bool, dict[str, Any] | None]:
    """Determine whether an agent is a system agent.

    Primary source of truth: agent.yml field `agent_type: system|user`.
    Compatibility fallback: BUILTIN_AGENTS set when agent_type is absent.
    """
    config = get_agent_config(agent_name, agents_dir=agents_dir, include_disabled=include_disabled)
    if config:
        parsed = _normalize_agent_type(config.get("agent_type"))
        if parsed is not None:
            return parsed == AGENT_TYPE_SYSTEM, config

    # Compatibility fallback for legacy configs without `agent_type`.
    return agent_name.lower() in BUILTIN_AGENTS, config


def is_registered_agent(
    agent_name: str, agents_dir: Path | None = None, include_disabled: bool = False
) -> tuple[bool, dict[str, Any] | None]:
    """Check if an agent is registered."""
    config = get_agent_config(agent_name, agents_dir=agents_dir, include_disabled=include_disabled)
    return (config is not None), config
