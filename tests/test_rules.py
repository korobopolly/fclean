"""Tests for rule modules (age, size, pattern, duplicate)."""

import time
from pathlib import Path

import pytest

from fclean.scanner import FileInfo
from fclean.rules.age import parse_age, filter_by_age
from fclean.rules.size import parse_size, filter_by_size, sort_by_size
from fclean.rules.pattern import filter_by_pattern, filter_by_extension
from fclean.rules.duplicate import find_duplicates


# --- Helpers ---

def make_file(name: str, size: int = 100, mtime: float | None = None) -> FileInfo:
    return FileInfo(
        path=Path(f"/fake/{name}"),
        size=size,
        mtime=mtime or time.time(),
        atime=mtime or time.time(),
        ctime=mtime or time.time(),
    )


# --- Age tests ---

class TestParseAge:
    def test_days(self):
        assert parse_age("30d") == 30 * 86400

    def test_weeks(self):
        assert parse_age("2w") == 2 * 604800

    def test_months(self):
        assert parse_age("6m") == 6 * 2592000

    def test_years(self):
        assert parse_age("1y") == 31536000

    def test_invalid(self):
        with pytest.raises(ValueError):
            parse_age("abc")

    def test_invalid_unit(self):
        with pytest.raises(ValueError):
            parse_age("10x")


class TestFilterByAge:
    def test_filters_old_files(self):
        now = time.time()
        old = make_file("old.txt", mtime=now - 86400 * 60)  # 60 days ago
        new = make_file("new.txt", mtime=now)
        result = filter_by_age([old, new], "30d")
        assert len(result) == 1
        assert result[0].path.name == "old.txt"

    def test_empty_input(self):
        assert filter_by_age([], "30d") == []


# --- Size tests ---

class TestParseSize:
    def test_bytes(self):
        assert parse_size("100B") == 100

    def test_kb(self):
        assert parse_size("1KB") == 1024

    def test_mb(self):
        assert parse_size("10MB") == 10 * 1024 ** 2

    def test_gb(self):
        assert parse_size("1.5GB") == int(1.5 * 1024 ** 3)

    def test_invalid(self):
        with pytest.raises(ValueError):
            parse_size("big")


class TestFilterBySize:
    def test_larger_than(self):
        files = [make_file("a", size=100), make_file("b", size=5000)]
        result = filter_by_size(files, larger_than="1KB")
        assert len(result) == 1
        assert result[0].path.name == "b"

    def test_smaller_than(self):
        files = [make_file("a", size=100), make_file("b", size=5000)]
        result = filter_by_size(files, smaller_than="1KB")
        assert len(result) == 1
        assert result[0].path.name == "a"


class TestSortBySize:
    def test_descending(self):
        files = [make_file("a", size=10), make_file("b", size=500), make_file("c", size=200)]
        result = sort_by_size(files)
        assert [f.path.name for f in result] == ["b", "c", "a"]


# --- Pattern tests ---

class TestFilterByPattern:
    def test_match_tmp(self):
        files = [make_file("data.tmp"), make_file("report.pdf"), make_file("log.tmp")]
        result = filter_by_pattern(files, ["*.tmp"])
        assert len(result) == 2

    def test_exclude(self):
        files = [make_file("data.tmp"), make_file("report.pdf")]
        result = filter_by_pattern(files, ["*.tmp"], exclude=True)
        assert len(result) == 1
        assert result[0].path.name == "report.pdf"

    def test_multiple_patterns(self):
        files = [make_file("a.tmp"), make_file("b.log"), make_file("c.txt")]
        result = filter_by_pattern(files, ["*.tmp", "*.log"])
        assert len(result) == 2


class TestFilterByExtension:
    def test_match(self):
        files = [make_file("a.py"), make_file("b.txt"), make_file("c.py")]
        result = filter_by_extension(files, [".py"])
        assert len(result) == 2

    def test_no_dot_prefix(self):
        files = [make_file("a.log")]
        result = filter_by_extension(files, ["log"])
        assert len(result) == 1


# --- Duplicate tests ---

class TestFindDuplicates:
    def test_no_duplicates(self):
        files = [make_file("a", size=100), make_file("b", size=200)]
        assert find_duplicates(files) == []

    def test_same_size_different_content(self):
        # Same size but different paths - since we can't actually read /fake/ paths,
        # hash functions will fail and return no duplicates
        files = [make_file("a", size=100), make_file("b", size=100)]
        # Both hash attempts will fail (paths don't exist), so no duplicates
        assert find_duplicates(files) == []

    def test_finds_real_duplicates(self, tmp_path):
        # Create actual duplicate files
        content = b"hello world duplicate content"
        f1 = tmp_path / "file1.txt"
        f2 = tmp_path / "file2.txt"
        f1.write_bytes(content)
        f2.write_bytes(content)

        files = [
            FileInfo.from_path(f1),
            FileInfo.from_path(f2),
        ]
        groups = find_duplicates(files)
        assert len(groups) == 1
        assert groups[0].count == 2

    def test_min_size_filter(self, tmp_path):
        content = b"hi"
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_bytes(content)
        f2.write_bytes(content)

        files = [FileInfo.from_path(f1), FileInfo.from_path(f2)]
        # min_size bigger than file size -> no results
        assert find_duplicates(files, min_size=1000) == []
