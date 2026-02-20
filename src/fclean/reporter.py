"""Rich-based report output for scan results."""

from __future__ import annotations

import humanize
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from fclean.scanner import FileInfo, ScanResult
from fclean.rules.duplicate import DuplicateGroup

console = Console()


def format_size(size: int) -> str:
    return humanize.naturalsize(size, binary=True)


def format_time(timestamp: float) -> str:
    import datetime
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc).astimezone()
    return dt.strftime("%Y-%m-%d %H:%M")


def print_scan_summary(result: ScanResult) -> None:
    """Print a summary of the scan result."""
    console.print(
        Panel(
            f"[bold]{result.file_count:,}[/bold] files  |  "
            f"[bold]{format_size(result.total_size)}[/bold] total  |  "
            f"[dim]{result.skipped_safe} safe-skipped, {result.error_count} errors[/dim]",
            title="Scan Result",
        )
    )


def print_file_table(
    files: list[FileInfo],
    *,
    title: str = "Files",
    limit: int = 20,
) -> None:
    """Print a table of files."""
    table = Table(title=title, show_lines=False)
    table.add_column("File", style="cyan", max_width=60, no_wrap=True)
    table.add_column("Size", style="green", justify="right")
    table.add_column("Modified", style="yellow")

    shown = files[:limit]
    for f in shown:
        table.add_row(
            str(f.path),
            format_size(f.size),
            format_time(f.mtime),
        )

    if len(files) > limit:
        table.add_row(
            f"[dim]... and {len(files) - limit} more[/dim]",
            "",
            "",
        )

    console.print(table)
    console.print(
        f"  Total: [bold]{len(files)}[/bold] files, "
        f"[bold]{format_size(sum(f.size for f in files))}[/bold]"
    )
    console.print()


def print_duplicate_report(groups: list[DuplicateGroup]) -> None:
    """Print duplicate file groups."""
    if not groups:
        console.print("[green]No duplicate files found.[/green]")
        return

    total_wasted = sum(g.wasted_bytes for g in groups)
    console.print(
        Panel(
            f"[bold]{len(groups)}[/bold] duplicate groups  |  "
            f"[bold]{format_size(total_wasted)}[/bold] recoverable",
            title="Duplicates",
        )
    )

    for i, group in enumerate(groups, 1):
        table = Table(
            title=f"Group {i} - {format_size(group.size)} x {group.count} copies",
            show_lines=False,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("File", style="cyan")
        table.add_column("Modified", style="yellow")

        for j, f in enumerate(group.files, 1):
            table.add_row(str(j), str(f.path), format_time(f.mtime))

        console.print(table)
        console.print()


def print_full_report(
    result: ScanResult,
    *,
    top_size: int = 10,
    top_old: int = 10,
) -> None:
    """Print a comprehensive report: summary, top by size, top by age."""
    print_scan_summary(result)
    console.print()

    if not result.files:
        console.print("[dim]No files to report.[/dim]")
        return

    # Top by size
    by_size = sorted(result.files, key=lambda f: f.size, reverse=True)
    print_file_table(by_size, title="Largest Files", limit=top_size)

    # Top by age (oldest)
    by_age = sorted(result.files, key=lambda f: f.mtime)
    print_file_table(by_age, title="Oldest Files", limit=top_old)
