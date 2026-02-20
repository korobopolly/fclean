"""Size-based file filtering rule."""

from __future__ import annotations

import re

from fclean.scanner import FileInfo

_UNITS = {
    "b": 1,
    "kb": 1024,
    "mb": 1024 ** 2,
    "gb": 1024 ** 3,
    "tb": 1024 ** 4,
}

_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)\s*(b|kb|mb|gb|tb)$", re.IGNORECASE)


def parse_size(size_str: str) -> int:
    """Parse a size string like '100MB', '1.5GB' into bytes."""
    match = _PATTERN.match(size_str.strip())
    if not match:
        raise ValueError(
            f"Invalid size format: '{size_str}'. Use <number><unit> (e.g. 100MB, 1.5GB)"
        )
    value = float(match.group(1))
    unit = match.group(2).lower()
    return int(value * _UNITS[unit])


def filter_by_size(
    files: list[FileInfo],
    larger_than: str | None = None,
    smaller_than: str | None = None,
) -> list[FileInfo]:
    """Filter files by size.

    Args:
        files: List of FileInfo to filter.
        larger_than: Minimum size string (e.g. '100MB').
        smaller_than: Maximum size string (e.g. '1KB').
    """
    min_bytes = parse_size(larger_than) if larger_than else 0
    max_bytes = parse_size(smaller_than) if smaller_than else float("inf")

    result = []
    for f in files:
        if larger_than and f.size <= min_bytes:
            continue
        if smaller_than and f.size >= max_bytes:
            continue
        result.append(f)
    return result


def sort_by_size(files: list[FileInfo], *, descending: bool = True) -> list[FileInfo]:
    """Sort files by size."""
    return sorted(files, key=lambda f: f.size, reverse=descending)
