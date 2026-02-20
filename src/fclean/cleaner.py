"""File deletion with safety features."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

from send2trash import send2trash

from fclean.scanner import FileInfo


@dataclass
class CleanResult:
    """Result of a clean operation."""

    deleted: list[Path] = field(default_factory=list)
    failed: list[tuple[Path, str]] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)
    total_freed: int = 0


def delete_files(
    files: list[FileInfo],
    *,
    use_trash: bool = True,
    dry_run: bool = False,
) -> CleanResult:
    """Delete or trash the given files.

    Args:
        files: Files to delete.
        use_trash: If True, move to trash instead of permanent delete.
        dry_run: If True, don't actually delete anything.
    """
    result = CleanResult()

    for fi in files:
        if dry_run:
            result.deleted.append(fi.path)
            result.total_freed += fi.size
            continue

        # Safety: skip symlinks to prevent symlink-based attacks
        if fi.path.is_symlink():
            result.skipped.append((fi.path, "symlink"))
            continue

        # Safety: re-verify file is still a regular file (TOCTOU mitigation)
        try:
            current = fi.path.lstat()
            if not stat.S_ISREG(current.st_mode):
                result.skipped.append((fi.path, "no longer a regular file"))
                continue
        except OSError as e:
            result.failed.append((fi.path, str(e)))
            continue

        try:
            if use_trash:
                send2trash(str(fi.path))
            else:
                os.remove(fi.path)
            result.deleted.append(fi.path)
            result.total_freed += fi.size
        except OSError as e:
            result.failed.append((fi.path, str(e)))

    return result
