"""Extended CLI tests - config-based clean, edge cases, and missing coverage."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from fclean.cli import app

runner = CliRunner()


class TestScanEdgeCases:
    def test_scan_empty_dir(self, tmp_path):
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == 0

    def test_scan_skip_hidden(self, tmp_path):
        (tmp_path / "visible.txt").write_text("v")
        (tmp_path / ".hidden.txt").write_text("h")
        result = runner.invoke(app, ["scan", str(tmp_path), "--skip-hidden"])
        assert result.exit_code == 0

    def test_scan_with_pattern(self, tmp_path):
        (tmp_path / "a.tmp").write_text("junk")
        (tmp_path / "b.txt").write_text("keep")
        result = runner.invoke(app, ["scan", str(tmp_path), "--pattern", "*.tmp"])
        assert result.exit_code == 0

    def test_scan_with_smaller_than(self, tmp_path):
        (tmp_path / "small.txt").write_text("hi")
        result = runner.invoke(app, ["scan", str(tmp_path), "--smaller-than", "1KB"])
        assert result.exit_code == 0

    def test_scan_limit_option(self, tmp_path):
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text(f"content{i}")
        result = runner.invoke(app, ["scan", str(tmp_path), "--limit", "2"])
        assert result.exit_code == 0

    def test_scan_combined_filters(self, tmp_path):
        (tmp_path / "big.log").write_text("x" * 2000)
        result = runner.invoke(
            app,
            ["scan", str(tmp_path), "--larger-than", "1KB", "--pattern", "*.log"],
        )
        assert result.exit_code == 0

    def test_scan_file_path_fails(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("hi")
        result = runner.invoke(app, ["scan", str(f)])
        assert result.exit_code == 1


class TestCleanEdgeCases:
    def test_clean_with_older_than(self, tmp_path):
        (tmp_path / "old.txt").write_text("old")
        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--older-than", "30d"],
        )
        assert result.exit_code == 0

    def test_clean_with_larger_than(self, tmp_path):
        (tmp_path / "big.bin").write_bytes(b"x" * 2000)
        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--larger-than", "1KB"],
        )
        assert result.exit_code == 0

    def test_clean_no_files_matched(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--pattern", "*.tmp"],
        )
        assert result.exit_code == 0
        assert "No files matched" in result.output

    def test_clean_file_path_fails(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("hi")
        result = runner.invoke(app, ["clean", str(f), "--pattern", "*.txt"])
        assert result.exit_code == 1

    def test_clean_permanent_dry_run(self, tmp_path):
        (tmp_path / "a.tmp").write_text("junk")
        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--pattern", "*.tmp", "--permanent"],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_clean_yes_flag_skips_prompt(self, tmp_path):
        (tmp_path / "junk.tmp").write_text("junk")
        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--pattern", "*.tmp", "--execute", "--yes", "--permanent"],
        )
        assert result.exit_code == 0


class TestCleanFromConfig:
    def test_config_clean_dry_run(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "old.log").write_text("old log data")

        config = tmp_path / "clean.yaml"
        config.write_text(
            f"rules:\n"
            f"  - name: Clean logs\n"
            f"    paths:\n"
            f"      - {log_dir}\n"
            f"    patterns:\n"
            f"      - '*.log'\n"
        )

        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--config", str(config)],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_config_no_rules(self, tmp_path):
        config = tmp_path / "empty.yaml"
        config.write_text("rules: []\n")

        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--config", str(config)],
        )
        assert result.exit_code == 0
        assert "No rules" in result.output

    def test_config_nonexistent_path_skipped(self, tmp_path):
        config = tmp_path / "clean.yaml"
        config.write_text(
            "rules:\n"
            "  - name: Ghost rule\n"
            "    paths:\n"
            "      - /nonexistent/path/that/wont/exist\n"
            "    patterns:\n"
            "      - '*.tmp'\n"
        )

        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--config", str(config)],
        )
        assert result.exit_code == 0

    def test_config_no_files_matched(self, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        (target / "keep.txt").write_text("keep")

        config = tmp_path / "clean.yaml"
        config.write_text(
            f"rules:\n"
            f"  - name: Junk\n"
            f"    paths:\n"
            f"      - {target}\n"
            f"    patterns:\n"
            f"      - '*.tmp'\n"
        )

        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--config", str(config)],
        )
        assert result.exit_code == 0
        assert "No files matched" in result.output

    def test_config_with_older_than_filter(self, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        (target / "a.log").write_text("data")

        config = tmp_path / "clean.yaml"
        config.write_text(
            f"rules:\n"
            f"  - name: Old logs\n"
            f"    paths:\n"
            f"      - {target}\n"
            f"    older_than: 365d\n"
            f"    patterns:\n"
            f"      - '*.log'\n"
        )

        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--config", str(config)],
        )
        assert result.exit_code == 0

    def test_config_with_extension_filter(self, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        (target / "a.bak").write_text("backup")
        (target / "b.txt").write_text("keep")

        config = tmp_path / "clean.yaml"
        config.write_text(
            f"rules:\n"
            f"  - name: Backups\n"
            f"    paths:\n"
            f"      - {target}\n"
            f"    extensions:\n"
            f"      - .bak\n"
        )

        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--config", str(config)],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_config_with_size_filter(self, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        (target / "big.bin").write_bytes(b"x" * 2000)
        (target / "small.txt").write_bytes(b"hi")

        config = tmp_path / "clean.yaml"
        config.write_text(
            f"rules:\n"
            f"  - name: Large files\n"
            f"    paths:\n"
            f"      - {target}\n"
            f"    larger_than: 1KB\n"
        )

        result = runner.invoke(
            app,
            ["clean", str(tmp_path), "--config", str(config)],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output


class TestDuplicatesEdgeCases:
    def test_duplicates_nonexistent_dir(self):
        result = runner.invoke(app, ["duplicates", "/nonexistent/path"])
        assert result.exit_code == 1

    def test_duplicates_empty_dir(self, tmp_path):
        result = runner.invoke(app, ["duplicates", str(tmp_path)])
        assert result.exit_code == 0
        assert "No duplicate" in result.output

    def test_duplicates_no_duplicates(self, tmp_path):
        (tmp_path / "a.txt").write_text("unique content a")
        (tmp_path / "b.txt").write_text("unique content b")
        result = runner.invoke(app, ["duplicates", str(tmp_path)])
        assert result.exit_code == 0
        assert "No duplicate" in result.output

    def test_duplicates_with_min_size(self, tmp_path):
        content = b"duplicate content here!"
        (tmp_path / "a.txt").write_bytes(content)
        (tmp_path / "b.txt").write_bytes(content)
        result = runner.invoke(
            app, ["duplicates", str(tmp_path), "--min-size", "1"]
        )
        assert result.exit_code == 0

    def test_duplicates_skip_hidden(self, tmp_path):
        content = b"dup"
        (tmp_path / "a.txt").write_bytes(content)
        (tmp_path / ".hidden.txt").write_bytes(content)
        result = runner.invoke(
            app, ["duplicates", str(tmp_path), "--skip-hidden"]
        )
        assert result.exit_code == 0


class TestScannerEdgeCases:
    def test_scan_symlink_not_followed_by_default(self, tmp_path):
        real = tmp_path / "real.txt"
        real.write_text("real")
        link = tmp_path / "link.txt"
        link.symlink_to(real)
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == 0
