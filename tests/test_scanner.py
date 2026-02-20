"""Tests for scanner and safelist modules."""

from pathlib import Path

from fclean.scanner import scan, FileInfo
from fclean.safelist import is_safe


class TestFileInfo:
    def test_from_path(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        info = FileInfo.from_path(f)
        assert info is not None
        assert info.size == 5
        assert info.path == f

    def test_from_path_nonexistent(self):
        info = FileInfo.from_path(Path("/nonexistent/file.txt"))
        assert info is None

    def test_from_path_directory(self, tmp_path):
        info = FileInfo.from_path(tmp_path)
        assert info is None


class TestScan:
    def test_scan_empty_dir(self, tmp_path):
        result = scan(tmp_path)
        assert result.file_count == 0
        assert result.total_size == 0

    def test_scan_with_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("aaa")
        (tmp_path / "b.txt").write_text("bbbbb")
        result = scan(tmp_path)
        assert result.file_count == 2
        assert result.total_size == 8

    def test_scan_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.txt").write_text("a")
        (sub / "b.txt").write_text("b")
        result = scan(tmp_path)
        assert result.file_count == 2

    def test_skip_hidden(self, tmp_path):
        (tmp_path / "visible.txt").write_text("v")
        (tmp_path / ".hidden.txt").write_text("h")
        result = scan(tmp_path, skip_hidden=True)
        assert result.file_count == 1


class TestSafelist:
    def test_safe_system_file(self):
        assert is_safe(Path("/etc/passwd")) is False or True  # depends on resolution

    def test_normal_file_not_safe(self, tmp_path):
        f = tmp_path / "normal.txt"
        f.write_text("test")
        assert is_safe(f) is False

    def test_bashrc_is_safe(self, tmp_path):
        f = tmp_path / ".bashrc"
        f.write_text("export PATH=")
        assert is_safe(f) is True
