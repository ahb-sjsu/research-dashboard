"""Build tmux layout commands for the research dashboard."""

from __future__ import annotations

import shutil
from typing import Any

# Tools the dashboard can use, in priority order per category.
GPU_TOOLS = ("nvtop", "nvidia-smi")
CPU_TOOLS = ("htop", "btop", "top")
DISK_TOOLS = ("iotop", "iostat")
NET_TOOLS = ("nethogs", "nload")
TEMP_TOOLS = ("sensors",)

ALL_TOOL_NAMES = (
    "nvtop",
    "nvidia-smi",
    "htop",
    "btop",
    "top",
    "iotop",
    "iostat",
    "nethogs",
    "nload",
    "sensors",
    "tmux",
    "watch",
    "df",
    "tail",
)


def detect_tools() -> dict[str, bool]:
    """Return a dict mapping tool names to whether they are installed."""
    return {name: shutil.which(name) is not None for name in ALL_TOOL_NAMES}


def _pick_first(tools: dict[str, bool], candidates: tuple[str, ...]) -> str | None:
    """Return the first available tool from *candidates*, or None."""
    for name in candidates:
        if tools.get(name, False):
            return name
    return None


def _gpu_command(tools: dict[str, bool]) -> str:
    """Return the command string for GPU monitoring."""
    preferred = _pick_first(tools, GPU_TOOLS)
    if preferred == "nvtop":
        return "nvtop"
    if preferred == "nvidia-smi":
        return (
            "watch -n2 nvidia-smi "
            "--query-gpu=index,name,memory.used,memory.total,"
            "temperature.gpu,utilization.gpu "
            "--format=csv,noheader"
        )
    return 'echo "No GPU monitoring tool found"; bash'


def _cpu_command(tools: dict[str, bool]) -> str:
    """Return the command string for CPU / process monitoring."""
    preferred = _pick_first(tools, CPU_TOOLS)
    if preferred == "htop":
        return "htop --sort-key=PERCENT_CPU"
    if preferred == "btop":
        return "btop"
    return "top"


def _disk_command(tools: dict[str, bool]) -> str:
    """Return the command string for disk I/O monitoring."""
    preferred = _pick_first(tools, DISK_TOOLS)
    if preferred == "iotop":
        return "sudo iotop -o -P -d 2 2>/dev/null || watch -n2 iostat"
    if preferred == "iostat":
        return "watch -n2 iostat"
    return 'watch -n2 "cat /proc/diskstats | head -20"'


def _net_command(tools: dict[str, bool]) -> str:
    """Return the command string for network monitoring."""
    preferred = _pick_first(tools, NET_TOOLS)
    if preferred == "nethogs":
        return (
            "sudo nethogs -d 2 2>/dev/null || nload -m 2>/dev/null "
            '|| watch -n2 "cat /proc/net/dev"'
        )
    if preferred == "nload":
        return 'nload -m 2>/dev/null || watch -n2 "cat /proc/net/dev"'
    return 'watch -n2 "cat /proc/net/dev"'


def _sensors_command(tools: dict[str, bool]) -> str:
    """Return the watch command for temperatures, RAID, and disk usage."""
    sensors_block = (
        'echo "══════ TEMPERATURES ══════"; '
        "sensors 2>/dev/null "
        '| grep -E "Package|Core 0|temp" | head -6; '
    )
    if not tools.get("sensors", False):
        sensors_block = (
            'echo "══════ TEMPERATURES ══════"; echo "(sensors not installed)"; '
        )

    gpu_block = (
        'echo ""; echo "══════ GPU ══════"; '
        "nvidia-smi --query-gpu=index,name,memory.used,memory.total,"
        "temperature.gpu,utilization.gpu "
        "--format=csv,noheader 2>/dev/null; "
    )
    if not tools.get("nvidia-smi", False):
        gpu_block = ""

    raid_block = (
        'echo ""; echo "══════ RAID ══════"; '
        'cat /proc/mdstat 2>/dev/null | grep -A1 "^md" | head -8; '
    )

    disk_block = (
        'echo ""; echo "══════ DISK ══════"; df -h / /home /tmp 2>/dev/null | tail -4'
    )

    inner = sensors_block + gpu_block + raid_block + disk_block
    return f'watch -n5 -t -c "{inner}"'


def _logs_command() -> str:
    """Return the command for tailing live logs."""
    return (
        'echo "══════ LIVE LOGS ══════"; '
        "tail -f /tmp/*.log 2>/dev/null "
        '|| (echo "No active logs found"; bash)'
    )


def build_layout(
    tools: dict[str, bool],
    session_name: str = "atlas-dash",
    *,
    no_gpu: bool = False,
    no_net: bool = False,
    no_disk: bool = False,
) -> list[str]:
    """Build a list of tmux commands that create the monitoring session.

    Layout
    ------
    ::

        +---------------------+----------------------+
        |   nvtop (GPUs)      |   htop (processes)   |
        |                     |                       |
        +----------+----------+----------+------------+
        | iotop    | nethogs  | sensors  | live logs  |
        | (disk)   | (net)    | raid/df  |            |
        +----------+----------+----------+------------+

    Parameters
    ----------
    tools:
        Output of :func:`detect_tools`.
    session_name:
        Name for the tmux session.
    no_gpu:
        Skip the GPU pane entirely.
    no_net:
        Skip the network pane.
    no_disk:
        Skip the disk I/O pane.

    Returns
    -------
    list[str]
        Ordered tmux shell commands.
    """
    cmds: list[str] = []

    # Kill any existing session with this name.
    cmds.append(f'tmux kill-session -t "{session_name}" 2>/dev/null')

    # ------------------------------------------------------------------
    # Top row
    # ------------------------------------------------------------------

    # Top-left: GPU monitoring (or CPU if --no-gpu).
    top_left = _cpu_command(tools) if no_gpu else _gpu_command(tools)
    cmds.append(f"tmux new-session -d -s \"{session_name}\" '{top_left}'")

    # Top-right: CPU / process monitoring.
    cpu_cmd = _cpu_command(tools)
    cmds.append(f"tmux split-window -t \"{session_name}\" -h '{cpu_cmd}'")

    # ------------------------------------------------------------------
    # Bottom row — left half (under GPU pane)
    # ------------------------------------------------------------------

    # Select the top-left pane, split vertically for bottom-left.
    cmds.append(f'tmux select-pane -t "{session_name}:0.0"')

    if not no_disk:
        disk_cmd = _disk_command(tools)
        cmds.append(f"tmux split-window -t \"{session_name}\" -v -p 35 '{disk_cmd}'")

        if not no_net:
            net_cmd = _net_command(tools)
            cmds.append(f"tmux split-window -t \"{session_name}\" -h '{net_cmd}'")
    elif not no_net:
        net_cmd = _net_command(tools)
        cmds.append(f"tmux split-window -t \"{session_name}\" -v -p 35 '{net_cmd}'")

    # ------------------------------------------------------------------
    # Bottom row — right half (under htop pane)
    # ------------------------------------------------------------------

    # Select the top-right pane (htop).
    cmds.append(f'tmux select-pane -t "{session_name}:0.1"')

    sensors_cmd = _sensors_command(tools)
    cmds.append(f"tmux split-window -t \"{session_name}\" -v -p 35 '{sensors_cmd}'")

    # Far bottom-right: live log tail.
    logs_cmd = _logs_command()
    cmds.append(f"tmux split-window -t \"{session_name}\" -h '{logs_cmd}'")

    # ------------------------------------------------------------------
    # Style
    # ------------------------------------------------------------------
    cmds.append(f'tmux set -t "{session_name}" pane-border-style fg=colour240')
    cmds.append(f'tmux set -t "{session_name}" pane-active-border-style fg=colour51')
    cmds.append(f'tmux set -t "{session_name}" status-style bg=colour235,fg=colour51')
    cmds.append(f"tmux set -t \"{session_name}\" status-left ' DASHBOARD '")
    cmds.append(f"tmux set -t \"{session_name}\" status-right '%H:%M '")

    # Attach.
    cmds.append(f'tmux attach -t "{session_name}"')

    return cmds


def build_layout_options(options: dict[str, Any]) -> dict[str, Any]:
    """Normalise CLI options into keyword arguments for :func:`build_layout`."""
    return {
        "no_gpu": bool(options.get("no_gpu", False)),
        "no_net": bool(options.get("no_net", False)),
        "no_disk": bool(options.get("no_disk", False)),
    }
