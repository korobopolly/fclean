"""Duplicate file detection using multi-stage hashing."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import xxhash

from fclean.scanner import FileInfo

# Read first 4KB for quick hash comparison
_QUICK_HASH_SIZE = 4096
# Read in 64KB chunks for full hash
_CHUNK_SIZE = 65536


@dataclass
class DuplicateGroup:
    """A group of files that are duplicates of each other."""

    hash: str
    size: int
    files: list[FileInfo] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.files)

    @property
    def wasted_bytes(self) -> int:
        """Bytes that could be recovered by keeping only one copy."""
        return self.size * (self.count - 1)


def _hash_partial(path: Path) -> str | None:
    """Hash the first few KB of a file for quick comparison."""
    try:
        with open(path, "rb") as f:
            data = f.read(_QUICK_HASH_SIZE)
            return xxhash.xxh3_64(data).hexdigest()
    except (OSError, PermissionError):
        return None


def _hash_full(path: Path) -> str | None:
    """Hash the entire file content."""
    try:
        h = xxhash.xxh3_64()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(_CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def find_duplicates(
    files: list[FileInfo],
    *,
    min_size: int = 1,
) -> list[DuplicateGroup]:
    """Find duplicate files using 3-stage approach.

    Stage 1: Group by file size (different sizes = definitely not duplicates).
    Stage 2: Quick hash (first 4KB) to narrow candidates.
    Stage 3: Full hash to confirm duplicates.

    Args:
        files: List of FileInfo to check.
        min_size: Minimum file size to consider (skip empty/tiny files).
    """
    # Stage 1: Group by size
    by_size: dict[int, list[FileInfo]] = defaultdict(list)
    for f in files:
        if f.size >= min_size:
            by_size[f.size].append(f)

    candidates = []
    for size_group in by_size.values():
        if len(size_group) >= 2:
            candidates.extend(size_group)

    if not candidates:
        return []

    # Stage 2: Quick hash (keyed by size + quick_hash to avoid cross-size collisions)
    by_quick_hash: dict[tuple[int, str], list[FileInfo]] = defaultdict(list)
    for f in candidates:
        h = _hash_partial(f.path)
        if h is not None:
            by_quick_hash[(f.size, h)].append(f)

    final_candidates = []
    for group in by_quick_hash.values():
        if len(group) >= 2:
            final_candidates.extend(group)

    if not final_candidates:
        return []

    # Stage 3: Full hash
    by_full_hash: dict[str, list[FileInfo]] = defaultdict(list)
    for f in final_candidates:
        h = _hash_full(f.path)
        if h is not None:
            by_full_hash[h].append(f)

    results = []
    for hash_val, group in by_full_hash.items():
        if len(group) >= 2:
            results.append(
                DuplicateGroup(
                    hash=hash_val,
                    size=group[0].size,
                    files=group,
                )
            )

    results.sort(key=lambda g: g.wasted_bytes, reverse=True)
    return results
