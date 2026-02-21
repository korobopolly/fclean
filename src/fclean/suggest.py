"""System cleanup suggestions - find known junk directories."""

from __future__ import annotations

import platform
import stat
from dataclasses import dataclass
from pathlib import Path

import platformdirs


@dataclass
class SuggestItem:
    """A suggested cleanup target."""

    name: str
    path: Path
    description: str
    exists: bool = False
    size: int = 0
    file_count: int = 0


def _dir_stats(path: Path) -> tuple[int, int]:
    """Return (total_size, file_count) for a directory."""
    import os
    total_size = 0
    count = 0
    try:
        for dirpath, _dirnames, filenames in os.walk(path, followlinks=False):
            for fname in filenames:
                try:
                    fpath = os.path.join(dirpath, fname)
                    st = os.lstat(fpath)
                    if stat.S_ISREG(st.st_mode):
                        total_size += st.st_size
                        count += 1
                except OSError:
                    pass
    except OSError:
        pass
    return total_size, count


def _is_wsl() -> bool:
    """Detect if running inside WSL."""
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def _wsl_win_homes() -> list[Path]:
    """Return Windows user home directories accessible via /mnt/c/Users."""
    users_dir = Path("/mnt/c/Users")
    skip = {"All Users", "Default", "Default User", "Public", "WsiAccount", "desktop.ini"}
    homes = []
    try:
        for entry in users_dir.iterdir():
            if entry.name in skip or not entry.is_dir():
                continue
            homes.append(entry)
    except OSError:
        pass
    return homes


def get_suggestions() -> list[SuggestItem]:
    """Get a list of cleanup suggestions for the current OS."""
    targets: list[tuple[str, Path, str]] = []
    system = platform.system()

    # Cross-platform
    cache_dir = Path(platformdirs.user_cache_dir())
    targets.append(("User Cache", cache_dir, "Application cache files"))

    temp_dir = Path(platformdirs.user_data_dir()).parent / "Temp" if system == "Windows" else Path("/tmp")
    targets.append(("Temp Files", temp_dir, "Temporary files"))

    home = Path.home()

    if system == "Windows":
        local = home / "AppData" / "Local"
        targets.extend([
            ("Windows Temp", local / "Temp", "Windows temporary files"),
            ("Thumbnail Cache", local / "Microsoft" / "Windows" / "Explorer", "Windows thumbnail cache"),
            ("Recent Files", home / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Recent", "Recent file shortcuts"),
        ])
    else:
        targets.extend([
            ("Trash", home / ".local" / "share" / "Trash", "Trash / Recycle bin"),
            ("Thumbnail Cache", home / ".cache" / "thumbnails", "Image thumbnail cache"),
            ("Journal Logs", Path("/var/log/journal"), "Systemd journal logs"),
        ])

    # Browser caches (cross-platform common paths)
    chrome_cache = cache_dir / "google-chrome" if system != "Windows" else home / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "Cache"
    targets.append(("Chrome Cache", chrome_cache, "Google Chrome browser cache"))

    # WSL: add Windows cleanup targets under /mnt/c/
    if _is_wsl():
        targets.append(("Windows Temp", Path("/mnt/c/Windows/Temp"), "Windows system temp files"))
        for wh in _wsl_win_homes():
            prefix = wh.name
            local = wh / "AppData" / "Local"
            roaming = wh / "AppData" / "Roaming"
            targets.extend([
                (f"[{prefix}] Temp", local / "Temp", "Windows user temp files"),
                (f"[{prefix}] npm cache", roaming / "npm-cache", "npm package cache"),
                (f"[{prefix}] pip cache", local / "pip" / "cache", "pip package cache"),
                (f"[{prefix}] Thumbnails", local / "Microsoft" / "Windows" / "Explorer", "Windows thumbnail cache"),
                (f"[{prefix}] Recent", roaming / "Microsoft" / "Windows" / "Recent", "Recent file shortcuts"),
                (f"[{prefix}] Chrome Cache", local / "Google" / "Chrome" / "User Data" / "Default" / "Cache", "Chrome browser cache"),
                (f"[{prefix}] Edge Cache", local / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache", "Edge browser cache"),
                (f"[{prefix}] CrashDumps", local / "CrashDumps", "Windows crash dump files"),
            ])

    results = []
    for name, path, desc in targets:
        item = SuggestItem(name=name, path=path, description=desc)
        try:
            if path.exists():
                item.exists = True
                item.size, item.file_count = _dir_stats(path)
        except OSError:
            pass
        results.append(item)

    return [item for item in results if item.exists and item.file_count > 0]
