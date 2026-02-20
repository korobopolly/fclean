"""Pattern-based file filtering rule."""

from __future__ import annotations

import fnmatch

from fclean.scanner import FileInfo

# Common junk file patterns
DEFAULT_JUNK_PATTERNS = [
    "*.tmp",
    "*.temp",
    "*.log",
    "*.bak",
    "*.old",
    "*.swp",
    "*.swo",
    "*~",
    "~$*",
    "Thumbs.db",
    "desktop.ini",
    ".DS_Store",
    "*.pyc",
    "__pycache__",
    "*.class",
    "*.o",
    "*.obj",
]


def filter_by_pattern(
    files: list[FileInfo],
    patterns: list[str],
    *,
    exclude: bool = False,
) -> list[FileInfo]:
    """Filter files matching glob patterns.

    Args:
        files: List of FileInfo to filter.
        patterns: Glob patterns to match against filenames.
        exclude: If True, return files NOT matching the patterns.
    """
    result = []
    for f in files:
        name = f.path.name
        matched = any(fnmatch.fnmatch(name, p) for p in patterns)
        if matched != exclude:
            result.append(f)
    return result


def filter_by_extension(
    files: list[FileInfo],
    extensions: list[str],
    *,
    exclude: bool = False,
) -> list[FileInfo]:
    """Filter files by extension.

    Args:
        files: List of FileInfo to filter.
        extensions: Extensions to match (e.g. ['.tmp', '.log']).
        exclude: If True, return files NOT matching the extensions.
    """
    ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
    result = []
    for f in files:
        matched = f.path.suffix.lower() in ext_set
        if matched != exclude:
            result.append(f)
    return result
