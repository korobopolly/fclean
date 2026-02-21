"""CLI entry point for fclean."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm

from fclean import __version__
from fclean.scanner import FileInfo, ProgressCallback, scan
from fclean.cleaner import delete_files
from fclean.reporter import (
    console,
    format_size,
    print_file_table,
    print_full_report,
    print_duplicate_report,
    print_scan_summary,
)

app = typer.Typer(
    name="fclean",
    help="CLI tool for cleaning up old, large, and duplicate files.",
    no_args_is_help=True,
)


@contextmanager
def _scan_progress():
    """Yield a progress callback that drives a live Rich spinner."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )
    task_id = progress.add_task("Scanning...", total=None)

    def callback(file_count: int, total_size: int) -> None:
        progress.update(
            task_id,
            description=f"Scanning  {file_count:,} files  {format_size(total_size)}",
        )

    with progress:
        yield callback


def version_callback(value: bool) -> None:
    if value:
        console.print(f"fclean v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """fclean - Clean up old, large, and duplicate files."""


@app.command("scan")
def scan_cmd(
    path: Path = typer.Argument(..., help="Directory to scan."),
    older_than: Optional[str] = typer.Option(None, "--older-than", "-o", help="Filter files older than (e.g. 30d, 6m, 1y)."),
    larger_than: Optional[str] = typer.Option(None, "--larger-than", "-l", help="Filter files larger than (e.g. 100MB, 1GB)."),
    smaller_than: Optional[str] = typer.Option(None, "--smaller-than", "-s", help="Filter files smaller than (e.g. 1KB)."),
    pattern: Optional[list[str]] = typer.Option(None, "--pattern", "-p", help="Glob patterns to match (e.g. '*.tmp')."),
    skip_hidden: bool = typer.Option(False, "--skip-hidden", help="Skip hidden files and directories."),
    limit: int = typer.Option(20, "--limit", "-n", help="Max files to show in report."),
) -> None:
    """Scan a directory and report files matching criteria."""
    if not path.is_dir():
        console.print(f"[red]Error: '{path}' is not a directory.[/red]")
        raise typer.Exit(1)

    with _scan_progress() as on_progress:
        result = scan(path, skip_hidden=skip_hidden, on_progress=on_progress)
    files = result.files

    # Apply filters
    has_filter = any([older_than, larger_than, smaller_than, pattern])

    if older_than:
        from fclean.rules.age import filter_by_age
        files = filter_by_age(files, older_than)

    if larger_than or smaller_than:
        from fclean.rules.size import filter_by_size
        files = filter_by_size(files, larger_than=larger_than, smaller_than=smaller_than)

    if pattern:
        from fclean.rules.pattern import filter_by_pattern
        files = filter_by_pattern(files, pattern)

    if has_filter:
        print_scan_summary(result)
        console.print()
        print_file_table(files, title="Matched Files", limit=limit)
    else:
        # No filter: show full comprehensive report
        from fclean.rules.duplicate import find_duplicates
        print_full_report(result, top_size=limit, top_old=limit)
        dupes = find_duplicates(result.files)
        if dupes:
            print_duplicate_report(dupes[:10])


@app.command()
def clean(
    path: Path = typer.Argument(..., help="Directory to clean."),
    older_than: Optional[str] = typer.Option(None, "--older-than", "-o", help="Filter files older than (e.g. 30d, 6m, 1y)."),
    larger_than: Optional[str] = typer.Option(None, "--larger-than", "-l", help="Filter files larger than (e.g. 100MB)."),
    smaller_than: Optional[str] = typer.Option(None, "--smaller-than", "-s", help="Filter files smaller than (e.g. 1KB)."),
    pattern: Optional[list[str]] = typer.Option(None, "--pattern", "-p", help="Glob patterns to match (e.g. '*.tmp')."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="YAML config file with rules."),
    execute: bool = typer.Option(False, "--execute", "-x", help="Actually delete files. Without this flag, only shows what would be deleted (dry-run)."),
    trash: bool = typer.Option(True, "--trash/--permanent", help="Move to trash (default) or permanently delete. Requires --execute."),
    skip_hidden: bool = typer.Option(False, "--skip-hidden", help="Skip hidden files and directories."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt. Requires --execute."),
) -> None:
    """Show files matching criteria. Use --execute to actually delete them."""
    if config:
        _clean_from_config(config, trash=trash, execute=execute, yes=yes)
        return

    if not path.is_dir():
        console.print(f"[red]Error: '{path}' is not a directory.[/red]")
        raise typer.Exit(1)

    if not any([older_than, larger_than, smaller_than, pattern]):
        console.print("[red]Error: Specify at least one filter (--older-than, --larger-than, --smaller-than, --pattern).[/red]")
        raise typer.Exit(1)

    with _scan_progress() as on_progress:
        result = scan(path, skip_hidden=skip_hidden, on_progress=on_progress)
    files = result.files

    if older_than:
        from fclean.rules.age import filter_by_age
        files = filter_by_age(files, older_than)

    if larger_than or smaller_than:
        from fclean.rules.size import filter_by_size
        files = filter_by_size(files, larger_than=larger_than, smaller_than=smaller_than)

    if pattern:
        from fclean.rules.pattern import filter_by_pattern
        files = filter_by_pattern(files, pattern)

    if not files:
        console.print("[green]No files matched the criteria.[/green]")
        return

    print_file_table(files, title="Files to Delete")

    if not execute:
        console.print("[yellow][DRY RUN] No files were deleted. Use --execute to actually delete.[/yellow]")
        return

    if not yes:
        action = "trash" if trash else "permanently delete"
        if not Confirm.ask(f"\n{action.capitalize()} {len(files)} files ({format_size(sum(f.size for f in files))})?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    clean_result = delete_files(files, use_trash=trash)
    console.print(
        f"[green]Deleted {len(clean_result.deleted)} files, "
        f"freed {format_size(clean_result.total_freed)}.[/green]"
    )
    if clean_result.failed:
        console.print(f"[red]Failed: {len(clean_result.failed)} files.[/red]")


def _clean_from_config(config_path: Path, *, trash: bool, execute: bool, yes: bool) -> None:
    """Run cleanup using a YAML config file."""
    from fclean.config import CleanConfig, ConfigError
    from fclean.rules.age import filter_by_age
    from fclean.rules.size import filter_by_size
    from fclean.rules.pattern import filter_by_pattern, filter_by_extension

    try:
        cfg = CleanConfig.from_file(config_path)
    except ConfigError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    if not cfg.rules:
        console.print("[yellow]No rules found in config.[/yellow]")
        return

    seen_paths: dict[Path, FileInfo] = {}
    for rule in cfg.rules:
        console.print(f"\n[bold]Rule: {rule.name}[/bold]")
        for p in rule.paths:
            target = Path(p).expanduser()
            if not target.is_dir():
                console.print(f"  [dim]Skipping {p} (not found)[/dim]")
                continue

            result = scan(target, skip_hidden=rule.skip_hidden)
            files = result.files

            if rule.older_than:
                files = filter_by_age(files, rule.older_than)
            if rule.larger_than or rule.smaller_than:
                files = filter_by_size(files, larger_than=rule.larger_than, smaller_than=rule.smaller_than)
            if rule.patterns:
                files = filter_by_pattern(files, rule.patterns)
            if rule.extensions:
                files = filter_by_extension(files, rule.extensions)

            for f in files:
                seen_paths[f.path.resolve()] = f
            console.print(f"  {target}: {len(files)} files matched")

    all_files = list(seen_paths.values())

    if not all_files:
        console.print("\n[green]No files matched any rules.[/green]")
        return

    print_file_table(all_files, title="All Matched Files")

    if not execute:
        console.print("[yellow][DRY RUN] No files were deleted. Use --execute to actually delete.[/yellow]")
        return

    if not yes:
        action = "trash" if trash else "permanently delete"
        if not Confirm.ask(f"\n{action.capitalize()} {len(all_files)} files ({format_size(sum(f.size for f in all_files))})?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    clean_result = delete_files(all_files, use_trash=trash)
    console.print(
        f"\n[green]Deleted {len(clean_result.deleted)} files, "
        f"freed {format_size(clean_result.total_freed)}.[/green]"
    )


@app.command()
def duplicates(
    path: Path = typer.Argument(..., help="Directory to scan for duplicates."),
    min_size: int = typer.Option(1024, "--min-size", help="Minimum file size in bytes."),
    skip_hidden: bool = typer.Option(False, "--skip-hidden", help="Skip hidden files."),
) -> None:
    """Find duplicate files."""
    if not path.is_dir():
        console.print(f"[red]Error: '{path}' is not a directory.[/red]")
        raise typer.Exit(1)

    with _scan_progress() as on_progress:
        result = scan(path, skip_hidden=skip_hidden, on_progress=on_progress)

    from fclean.rules.duplicate import find_duplicates
    groups = find_duplicates(result.files, min_size=min_size)
    print_duplicate_report(groups)


@app.command()
def suggest() -> None:
    """Suggest system directories to clean up."""
    from fclean.suggest import get_suggestions
    from rich.table import Table

    suggestions = get_suggestions()
    if not suggestions:
        console.print("[green]No cleanup suggestions found.[/green]")
        return

    table = Table(title="Cleanup Suggestions")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Files", justify="right")
    table.add_column("Size", style="green", justify="right")
    table.add_column("Description")

    total_size = 0
    for item in suggestions:
        table.add_row(
            item.name,
            str(item.path),
            f"{item.file_count:,}",
            format_size(item.size),
            item.description,
        )
        total_size += item.size

    console.print(table)
    console.print(f"\n  Total recoverable: [bold]{format_size(total_size)}[/bold]")
    console.print("  [dim]Use 'fclean clean <path>' to clean specific directories.[/dim]")
