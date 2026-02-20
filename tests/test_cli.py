"""Tests for CLI commands."""

from typer.testing import CliRunner

from fclean.cli import app

runner = CliRunner()


class TestCLI:
    def test_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "fclean v" in result.output

    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "scan" in result.output
        assert "clean" in result.output
        assert "duplicates" in result.output
        assert "suggest" in result.output

    def test_scan_nonexistent_dir(self):
        result = runner.invoke(app, ["scan", "/nonexistent/path"])
        assert result.exit_code == 1

    def test_scan_real_dir(self, tmp_path):
        (tmp_path / "a.txt").write_text("hello")
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == 0
        assert "Scan Result" in result.output

    def test_scan_with_older_than(self, tmp_path):
        (tmp_path / "a.txt").write_text("test")
        result = runner.invoke(app, ["scan", str(tmp_path), "--older-than", "30d"])
        assert result.exit_code == 0

    def test_scan_with_larger_than(self, tmp_path):
        (tmp_path / "big.txt").write_text("x" * 2000)
        result = runner.invoke(app, ["scan", str(tmp_path), "--larger-than", "1KB"])
        assert result.exit_code == 0

    def test_clean_requires_filter(self, tmp_path):
        result = runner.invoke(app, ["clean", str(tmp_path)])
        assert result.exit_code == 1

    def test_clean_dry_run(self, tmp_path):
        (tmp_path / "test.tmp").write_text("junk")
        result = runner.invoke(app, ["clean", str(tmp_path), "--pattern", "*.tmp"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_duplicates_command(self, tmp_path):
        content = b"duplicate content here"
        (tmp_path / "a.txt").write_bytes(content)
        (tmp_path / "b.txt").write_bytes(content)
        result = runner.invoke(app, ["duplicates", str(tmp_path)])
        assert result.exit_code == 0

    def test_suggest_command(self):
        result = runner.invoke(app, ["suggest"])
        assert result.exit_code == 0
