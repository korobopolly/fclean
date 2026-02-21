"""File scanner engine - recursively collects file metadata."""

from __future__ import annotations

import os
import stat as stat_mod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator

from fclean.safelist import is_safe


@dataclass
class FileInfo:
    """Metadata for a single file."""

    path: Path
    size: int = 0
    mtime: float = 0.0  # last modified
    atime: float = 0.0  # last accessed
    ctime: float = 0.0  # created (platform-dependent)

    @classmethod
    def from_path(cls, path: Path) -> FileInfo | None:
        """Create FileInfo from a path. Returns None if stat fails."""
        try:
            st = path.stat()
            if not stat_mod.S_ISREG(st.st_mode):
                return None
            return cls(
                path=path,
                size=st.st_size,
                mtime=st.st_mtime,
                atime=st.st_atime,
                ctime=st.st_ctime,
            )
        except OSError:
            return None

    @classmethod
    def from_stat(cls, path: Path, st: os.stat_result) -> FileInfo:
        """Create FileInfo from an already-obtained stat result."""
        return cls(
            path=path,
            size=st.st_size,
            mtime=st.st_mtime,
            atime=st.st_atime,
            ctime=st.st_ctime,
        )


@dataclass
class ScanResult:
    """Result of a directory scan."""

    files: list[FileInfo] = field(default_factory=list)
    total_size: int = 0
    error_count: int = 0
    skipped_safe: int = 0

    @property
    def file_count(self) -> int:
        return len(self.files)


# (file_count, total_size) -> None
ProgressCallback = Callable[[int, int], None]

_PROGRESS_INTERVAL = 500


def scan(
    root: Path,
    *,
    follow_symlinks: bool = False,
    skip_hidden: bool = False,
    respect_safelist: bool = True,
    on_progress: ProgressCallback | None = None,
) -> ScanResult:
    """Scan a directory tree and collect file metadata.

    Args:
        root: Directory to scan.
        follow_symlinks: Whether to follow symbolic links.
        skip_hidden: Whether to skip hidden files/directories (starting with '.').
        respect_safelist: Whether to skip system-protected paths.
        on_progress: Optional callback invoked every ~500 files with (file_count, total_size).
    """
    result = ScanResult()

    for file_path, st in _walk_files(root, follow_symlinks=follow_symlinks, skip_hidden=skip_hidden):
        if respect_safelist and is_safe(file_path):
            result.skipped_safe += 1
            continue

        if st is None:
            result.error_count += 1
            continue

        result.files.append(FileInfo.from_stat(file_path, st))
        result.total_size += st.st_size

        if on_progress and result.file_count % _PROGRESS_INTERVAL == 0:
            on_progress(result.file_count, result.total_size)

    return result


def _walk_files(
    root: Path,
    *,
    follow_symlinks: bool = False,
    skip_hidden: bool = False,
) -> Iterator[tuple[Path, os.stat_result | None]]:
    """Yield (path, stat_result) pairs under root using iterative DFS.

    Uses entry.stat() from os.scandir() to avoid a redundant stat() syscall
    per file — significant on slow filesystems like WSL /mnt/c/.
    """
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if skip_hidden and entry.name.startswith("."):
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=follow_symlinks):
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=follow_symlinks):
                            try:
                                st = entry.stat(follow_symlinks=follow_symlinks)
                            except OSError:
                                st = None
                            yield Path(entry.path), st
                    except OSError:
                        continue
        except OSError:
            continue
