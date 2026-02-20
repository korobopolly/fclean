"""Tests for cleaner.py - file deletion with safety features."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from fclean.cleaner import CleanResult, delete_files
from fclean.scanner import FileInfo


def make_file_info(path: Path, size: int = 100) -> FileInfo:
    return FileInfo(path=path, size=size, mtime=0.0, atime=0.0, ctime=0.0)


class TestCleanResult:
    def test_default_values(self):
        result = CleanResult()
        assert result.deleted == []
        assert result.failed == []
        assert result.total_freed == 0

    def test_can_add_deleted(self):
        result = CleanResult()
        result.deleted.append(Path("/tmp/a.txt"))
        assert len(result.deleted) == 1

    def test_can_add_failed(self):
        result = CleanResult()
        result.failed.append((Path("/tmp/b.txt"), "Permission denied"))
        assert len(result.failed) == 1


class TestDeleteFilesDryRun:
    def test_dry_run_does_not_delete(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("data")
        info = make_file_info(f, size=4)

        result = delete_files([info], dry_run=True)

        assert f.exists()  # file still there
        assert result.deleted == [f]
        assert result.total_freed == 4

    def test_dry_run_multiple_files(self, tmp_path):
        files = []
        infos = []
        for i in range(3):
            p = tmp_path / f"file{i}.txt"
            p.write_text("x" * (i + 1))
            files.append(p)
            infos.append(make_file_info(p, size=i + 1))

        result = delete_files(infos, dry_run=True)

        assert len(result.deleted) == 3
        assert result.total_freed == 6
        assert result.failed == []
        for p in files:
            assert p.exists()

    def test_dry_run_empty_list(self):
        result = delete_files([], dry_run=True)
        assert result.deleted == []
        assert result.total_freed == 0


class TestDeleteFilesTrash:
    def test_trash_mode_calls_send2trash(self, tmp_path):
        f = tmp_path / "trash_me.txt"
        f.write_text("junk")
        info = make_file_info(f, size=4)

        with patch("fclean.cleaner.send2trash") as mock_trash:
            result = delete_files([info], use_trash=True, dry_run=False)

        mock_trash.assert_called_once_with(str(f))
        assert result.deleted == [f]
        assert result.total_freed == 4
        assert result.failed == []

    def test_trash_failure_recorded(self, tmp_path):
        f = tmp_path / "fail.txt"
        f.write_text("data")
        info = make_file_info(f, size=4)

        with patch("fclean.cleaner.send2trash", side_effect=OSError("Trash error")):
            result = delete_files([info], use_trash=True, dry_run=False)

        assert result.deleted == []
        assert len(result.failed) == 1
        assert result.failed[0][0] == f
        assert "Trash error" in result.failed[0][1]
        assert result.total_freed == 0


class TestDeleteFilesPermanent:
    def test_permanent_delete_removes_file(self, tmp_path):
        f = tmp_path / "delete_me.txt"
        f.write_text("bye")
        info = make_file_info(f, size=3)

        result = delete_files([info], use_trash=False, dry_run=False)

        assert not f.exists()
        assert result.deleted == [f]
        assert result.total_freed == 3
        assert result.failed == []

    def test_permanent_delete_nonexistent_file(self, tmp_path):
        f = tmp_path / "ghost.txt"
        info = make_file_info(f, size=0)

        result = delete_files([info], use_trash=False, dry_run=False)

        assert result.deleted == []
        assert len(result.failed) == 1
        assert result.failed[0][0] == f

    def test_permanent_delete_multiple_files(self, tmp_path):
        infos = []
        for i in range(5):
            p = tmp_path / f"file{i}.txt"
            p.write_text("data")
            infos.append(make_file_info(p, size=4))

        result = delete_files(infos, use_trash=False, dry_run=False)

        assert len(result.deleted) == 5
        assert result.total_freed == 20
        assert result.failed == []

    def test_partial_failure_continues(self, tmp_path):
        good = tmp_path / "good.txt"
        good.write_text("ok")
        good_info = make_file_info(good, size=2)

        bad = tmp_path / "bad.txt"
        bad_info = make_file_info(bad, size=0)  # doesn't exist

        result = delete_files([good_info, bad_info], use_trash=False, dry_run=False)

        assert len(result.deleted) == 1
        assert result.deleted[0] == good
        assert len(result.failed) == 1
        assert result.failed[0][0] == bad

    def test_total_freed_only_counts_successes(self, tmp_path):
        good = tmp_path / "good.txt"
        good.write_text("hello")
        good_info = make_file_info(good, size=5)

        bad = tmp_path / "bad.txt"
        bad_info = make_file_info(bad, size=999)  # doesn't exist

        result = delete_files([good_info, bad_info], use_trash=False, dry_run=False)

        assert result.total_freed == 5  # only the successfully deleted file


class TestDeleteFilesEdgeCases:
    def test_empty_list_returns_empty_result(self):
        result = delete_files([], use_trash=False, dry_run=False)
        assert result.deleted == []
        assert result.failed == []
        assert result.total_freed == 0

    def test_zero_size_file_counted(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        info = make_file_info(f, size=0)

        result = delete_files([info], use_trash=False, dry_run=False)

        assert result.deleted == [f]
        assert result.total_freed == 0
