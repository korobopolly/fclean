"""Tests for config.py - YAML configuration loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from fclean.config import CleanConfig, RuleConfig


class TestRuleConfig:
    def test_default_values(self):
        rule = RuleConfig()
        assert rule.name == ""
        assert rule.paths == []
        assert rule.older_than is None
        assert rule.larger_than is None
        assert rule.smaller_than is None
        assert rule.patterns == []
        assert rule.extensions == []
        assert rule.skip_hidden is False

    def test_custom_values(self):
        rule = RuleConfig(
            name="old logs",
            paths=["/var/log"],
            older_than="30d",
            larger_than="1MB",
            smaller_than="1GB",
            patterns=["*.log"],
            extensions=[".bak"],
            skip_hidden=True,
        )
        assert rule.name == "old logs"
        assert rule.paths == ["/var/log"]
        assert rule.older_than == "30d"
        assert rule.larger_than == "1MB"
        assert rule.smaller_than == "1GB"
        assert rule.patterns == ["*.log"]
        assert rule.extensions == [".bak"]
        assert rule.skip_hidden is True


class TestCleanConfig:
    def test_default_empty(self):
        cfg = CleanConfig()
        assert cfg.rules == []

    def test_from_file_full(self, tmp_path):
        config_file = tmp_path / "clean.yaml"
        config_file.write_text(
            "rules:\n"
            "  - name: old logs\n"
            "    paths:\n"
            "      - /var/log\n"
            "    older_than: 30d\n"
            "    larger_than: 1MB\n"
            "    smaller_than: 1GB\n"
            "    patterns:\n"
            "      - '*.log'\n"
            "    extensions:\n"
            "      - .bak\n"
            "    skip_hidden: true\n"
        )
        cfg = CleanConfig.from_file(config_file)
        assert len(cfg.rules) == 1
        rule = cfg.rules[0]
        assert rule.name == "old logs"
        assert rule.paths == ["/var/log"]
        assert rule.older_than == "30d"
        assert rule.larger_than == "1MB"
        assert rule.smaller_than == "1GB"
        assert rule.patterns == ["*.log"]
        assert rule.extensions == [".bak"]
        assert rule.skip_hidden is True

    def test_from_file_minimal_rule(self, tmp_path):
        config_file = tmp_path / "clean.yaml"
        config_file.write_text("rules:\n  - name: minimal\n")
        cfg = CleanConfig.from_file(config_file)
        assert len(cfg.rules) == 1
        rule = cfg.rules[0]
        assert rule.name == "minimal"
        assert rule.paths == []
        assert rule.older_than is None
        assert rule.patterns == []

    def test_from_file_multiple_rules(self, tmp_path):
        config_file = tmp_path / "clean.yaml"
        config_file.write_text(
            "rules:\n"
            "  - name: rule1\n"
            "    paths: [/tmp]\n"
            "  - name: rule2\n"
            "    paths: [/var/log]\n"
            "    older_than: 7d\n"
        )
        cfg = CleanConfig.from_file(config_file)
        assert len(cfg.rules) == 2
        assert cfg.rules[0].name == "rule1"
        assert cfg.rules[1].name == "rule2"
        assert cfg.rules[1].older_than == "7d"

    def test_from_file_empty_yaml(self, tmp_path):
        config_file = tmp_path / "clean.yaml"
        config_file.write_text("")
        cfg = CleanConfig.from_file(config_file)
        assert cfg.rules == []

    def test_from_file_no_rules_key(self, tmp_path):
        config_file = tmp_path / "clean.yaml"
        config_file.write_text("version: 1\n")
        cfg = CleanConfig.from_file(config_file)
        assert cfg.rules == []

    def test_from_file_empty_rules_list(self, tmp_path):
        config_file = tmp_path / "clean.yaml"
        config_file.write_text("rules: []\n")
        cfg = CleanConfig.from_file(config_file)
        assert cfg.rules == []

    def test_from_file_nonexistent_raises(self):
        from fclean.config import ConfigError
        with pytest.raises(ConfigError, match="not found"):
            CleanConfig.from_file(Path("/nonexistent/config.yaml"))

    def test_from_file_rule_defaults_for_missing_fields(self, tmp_path):
        config_file = tmp_path / "clean.yaml"
        config_file.write_text("rules:\n  - {}\n")
        cfg = CleanConfig.from_file(config_file)
        assert len(cfg.rules) == 1
        rule = cfg.rules[0]
        assert rule.name == ""
        assert rule.paths == []
        assert rule.skip_hidden is False

    def test_from_file_skip_hidden_default_false(self, tmp_path):
        config_file = tmp_path / "clean.yaml"
        config_file.write_text("rules:\n  - name: norule\n")
        cfg = CleanConfig.from_file(config_file)
        assert cfg.rules[0].skip_hidden is False

    def test_from_file_paths_list(self, tmp_path):
        config_file = tmp_path / "clean.yaml"
        config_file.write_text(
            "rules:\n"
            "  - name: multi\n"
            "    paths:\n"
            "      - /a\n"
            "      - /b\n"
            "      - /c\n"
        )
        cfg = CleanConfig.from_file(config_file)
        assert cfg.rules[0].paths == ["/a", "/b", "/c"]
