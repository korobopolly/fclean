"""System file protection - prevents deletion of critical files."""

from __future__ import annotations

import platform
from pathlib import Path

# Directories that should never be cleaned
_SAFE_DIRS_WINDOWS = {
    "windows",
    "system32",
    "syswow64",
    "winsxs",
    "program files",
    "program files (x86)",
    "programdata",
    "recovery",
    "boot",
    "$recycle.bin",
    "system volume information",
}

_SAFE_DIRS_LINUX = {
    "bin",
    "sbin",
    "lib",
    "lib64",
    "usr",
    "etc",
    "boot",
    "proc",
    "sys",
    "dev",
    "run",
    "snap",
}

_SAFE_DIRS_MACOS = {
    "system",
    "library",
    "applications",
    "bin",
    "sbin",
    "usr",
    "etc",
    "var",
    "private",
    "cores",
}

# Files that should never be deleted
_SENSITIVE_USER_DIRS = {
    ".ssh", ".gnupg", ".aws", ".config",
    ".kube", ".docker", ".password-store",
    ".mozilla", ".thunderbird",
}

_SAFE_FILES = {
    "ntldr",
    "bootmgr",
    "pagefile.sys",
    "hiberfil.sys",
    "swapfile.sys",
    ".bashrc",
    ".bash_profile",
    ".profile",
    ".zshrc",
    ".gitconfig",
}


def _get_safe_dirs() -> set[str]:
    system = platform.system()
    if system == "Windows":
        return _SAFE_DIRS_WINDOWS
    if system == "Darwin":
        return _SAFE_DIRS_MACOS | _SAFE_DIRS_LINUX
    return _SAFE_DIRS_LINUX


def is_safe(path: Path) -> bool:
    """Check if a path is a protected system file/directory."""
    resolved = path.resolve()
    name_lower = resolved.name.lower()

    # Check filename
    if name_lower in _SAFE_FILES:
        return True

    # Check if inside a safe directory
    safe_dirs = _get_safe_dirs()
    for parent in resolved.parents:
        if parent.name.lower() in safe_dirs and parent.parent == Path(parent.anchor):
            return True

    # Protect sensitive user directories
    home = Path.home()
    for parent in resolved.parents:
        if parent.name in _SENSITIVE_USER_DIRS and parent.parent == home:
            return True

    return False
