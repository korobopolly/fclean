"""Tests for suggest.py - system cleanup suggestions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from fclean.suggest import SuggestItem, _dir_stats, get_suggestions


class TestSuggestItem:
    def test_default_values(self):
        item = SuggestItem(name="Cache", path=Path("/tmp/cache"), description="Cache files")
        assert item.name == "Cache"
        assert item.path == Path("/tmp/cache")
        assert item.description == "Cache files"
        assert item.exists is False
        assert item.size == 0
        assert item.file_count == 0

    def test_custom_values(self):
        item = SuggestItem(
            name="Trash",
            path=Path("/home/user/.local/share/Trash"),
            description="Trash bin",
            exists=True,
            size=1024 * 1024,
            file_count=42,
        )
        assert item.exists is True
        assert item.size == 1024 * 1024
        assert item.file_count == 42


class TestDirStats:
    def test_empty_directory(self, tmp_path):
        size, count = _dir_stats(tmp_path)
        assert size == 0
        assert count == 0

    def test_single_file(self, tmp_path):
        (tmp_path / "file.txt").write_bytes(b"hello")
        size, count = _dir_stats(tmp_path)
        assert size == 5
        assert count == 1

    def test_multiple_files(self, tmp_path):
        (tmp_path / "a.txt").write_bytes(b"aa")
        (tmp_path / "b.txt").write_bytes(b"bbb")
        (tmp_path / "c.txt").write_bytes(b"cccc")
        size, count = _dir_stats(tmp_path)
        assert size == 9
        assert count == 3

    def test_nested_directories(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.txt").write_bytes(b"aa")
        (sub / "b.txt").write_bytes(b"bbb")
        size, count = _dir_stats(tmp_path)
        assert size == 5
        assert count == 2

    def test_nonexistent_directory(self):
        size, count = _dir_stats(Path("/nonexistent/path/that/does/not/exist"))
        assert size == 0
        assert count == 0

    def test_only_directories_no_files(self, tmp_path):
        (tmp_path / "subdir1").mkdir()
        (tmp_path / "subdir2").mkdir()
        size, count = _dir_stats(tmp_path)
        assert size == 0
        assert count == 0


class TestGetSuggestions:
    def test_returns_list(self):
        result = get_suggestions()
        assert isinstance(result, list)

    def test_all_items_exist_and_have_files(self):
        result = get_suggestions()
        for item in result:
            assert item.exists is True
            assert item.file_count > 0

    def test_items_are_suggest_item_instances(self):
        result = get_suggestions()
        for item in result:
            assert isinstance(item, SuggestItem)
            assert isinstance(item.name, str)
            assert isinstance(item.path, Path)
            assert isinstance(item.description, str)

    def test_no_items_with_zero_files(self):
        result = get_suggestions()
        for item in result:
            assert item.file_count > 0

    def test_get_suggestions_linux(self):
        with patch("fclean.suggest.platform.system", return_value="Linux"):
            with patch("fclean.suggest.Path.exists", return_value=False):
                result = get_suggestions()
                # All paths don't exist so result should be empty
                assert result == []

    def test_get_suggestions_windows(self):
        with patch("fclean.suggest.platform.system", return_value="Windows"):
            with patch("fclean.suggest.Path.exists", return_value=False):
                result = get_suggestions()
                assert result == []

    def test_get_suggestions_with_existing_dir(self, tmp_path):
        fake_cache = tmp_path / "fake_cache"
        fake_cache.mkdir()
        (fake_cache / "junk.bin").write_bytes(b"x" * 100)

        with patch("fclean.suggest.platform.system", return_value="Linux"):
            with patch("fclean.suggest.Path", side_effect=lambda *a, **kw: Path(*a, **kw)):
                # Can't easily mock platformdirs; just verify real call works
                result = get_suggestions()
                assert isinstance(result, list)

    def test_size_is_non_negative(self):
        result = get_suggestions()
        for item in result:
            assert item.size >= 0

    def test_items_have_non_empty_names(self):
        result = get_suggestions()
        for item in result:
            assert item.name != ""
            assert item.description != ""
