"""Command-line interface for research-dashboard."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

from research_dashboard.layout import build_layout, detect_tools


def _check_tmux() -> bool:
    """Return True if tmux is available on the system."""
    return shutil.which("tmux") is not None


def _print_tool_status(tools: dict[str, bool]) -> None:
    """Print a table showing which monitoring tools are available."""
    print("Detected tools:")
    for name, available in sorted(tools.items()):
        status = "OK" if available else "missing"
        print(f"  {name:12s}  {status}")
    print()


def main(argv: list[str] | None = None) -> int:
    """Entry point for the research-dashboard CLI.

    Returns
    -------
    int
        Exit code (0 for success, non-zero for errors).
    """
    parser = argparse.ArgumentParser(
        prog="research-dashboard",
        description="Launch a tmux monitoring dashboard for ML research workstations.",
    )
    parser.add_argument(
        "--session-name",
        default="atlas-dash",
        help="Name for the tmux session (default: atlas-dash)",
    )
    parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Skip GPU monitoring pane (nvtop / nvidia-smi)",
    )
    parser.add_argument(
        "--no-net",
        action="store_true",
        help="Skip network monitoring pane (nethogs / nload)",
    )
    parser.add_argument(
        "--no-disk",
        action="store_true",
        help="Skip disk I/O monitoring pane (iotop / iostat)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the tmux commands without executing them",
    )

    args = parser.parse_args(argv)

    # Preflight: tmux must be present.
    if not _check_tmux():
        print("ERROR: tmux is not installed. Install it first.", file=sys.stderr)
        return 1

    tools = detect_tools()
    _print_tool_status(tools)

    cmds = build_layout(
        tools,
        session_name=args.session_name,
        no_gpu=args.no_gpu,
        no_net=args.no_net,
        no_disk=args.no_disk,
    )

    if args.dry_run:
        print("Dry-run mode — commands that would be executed:\n")
        for cmd in cmds:
            print(f"  {cmd}")
        return 0

    # Execute each command sequentially.
    for cmd in cmds:
        subprocess.run(cmd, shell=True, check=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
