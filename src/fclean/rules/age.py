"""Age-based file filtering rule."""

from __future__ import annotations

import re
import time

from fclean.scanner import FileInfo

# Supported units: d(ays), w(eeks), m(onths), y(ears)
_UNIT_SECONDS = {
    "d": 86400,
    "w": 604800,
    "m": 2592000,   # 30 days
    "y": 31536000,  # 365 days
}

_PATTERN = re.compile(r"^(\d+)\s*([dwmy])$", re.IGNORECASE)


def parse_age(age_str: str) -> float:
    """Parse an age string like '30d', '6m', '1y' into seconds."""
    match = _PATTERN.match(age_str.strip())
    if not match:
        raise ValueError(
            f"Invalid age format: '{age_str}'. Use <number><unit> (e.g. 30d, 6m, 1y)"
        )
    value = int(match.group(1))
    unit = match.group(2).lower()
    return value * _UNIT_SECONDS[unit]


def filter_by_age(
    files: list[FileInfo],
    older_than: str,
    *,
    use_mtime: bool = True,
) -> list[FileInfo]:
    """Filter files older than the given age.

    Args:
        files: List of FileInfo to filter.
        older_than: Age string like '30d', '6m', '1y'.
        use_mtime: If True, use modification time. If False, use access time.
    """
    threshold = time.time() - parse_age(older_than)
    result = []
    for f in files:
        ts = f.mtime if use_mtime else f.atime
        if ts < threshold:
            result.append(f)
    return result
