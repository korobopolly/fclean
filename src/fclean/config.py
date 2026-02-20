"""YAML configuration loader for cleanup rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class RuleConfig:
    """A single cleanup rule."""

    name: str = ""
    paths: list[str] = field(default_factory=list)
    older_than: str | None = None
    larger_than: str | None = None
    smaller_than: str | None = None
    patterns: list[str] = field(default_factory=list)
    extensions: list[str] = field(default_factory=list)
    skip_hidden: bool = False


@dataclass
class CleanConfig:
    """Top-level configuration."""

    rules: list[RuleConfig] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> CleanConfig:
        """Load configuration from a YAML file."""
        try:
            with open(path) as fh:
                data = yaml.safe_load(fh)
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {path}: {e}")

        if not data or "rules" not in data:
            return cls()

        raw_rules = data["rules"]
        if not isinstance(raw_rules, list):
            raise ConfigError(f"'rules' must be a list in {path}")

        rules = []
        for raw in raw_rules:
            if not isinstance(raw, dict):
                continue
            rules.append(
                RuleConfig(
                    name=raw.get("name", ""),
                    paths=raw.get("paths", []),
                    older_than=raw.get("older_than"),
                    larger_than=raw.get("larger_than"),
                    smaller_than=raw.get("smaller_than"),
                    patterns=raw.get("patterns", []),
                    extensions=raw.get("extensions", []),
                    skip_hidden=raw.get("skip_hidden", False),
                )
            )
        return cls(rules=rules)


class ConfigError(Exception):
    """Raised when config file is invalid or missing."""
