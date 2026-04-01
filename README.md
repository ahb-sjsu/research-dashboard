# research-dashboard

[![PyPI version](https://img.shields.io/pypi/v/research-dashboard)](https://pypi.org/project/research-dashboard/)
[![CI](https://github.com/ahbond/research-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/ahbond/research-dashboard/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A tmux-based system monitoring dashboard for ML research workstations. One command gives you GPU, CPU, disk I/O, network, temperatures, RAID status, and live log tailing in a single terminal.

![Screenshot placeholder](https://via.placeholder.com/800x400?text=research-dashboard+screenshot)

## Installation

```bash
pip install research-dashboard
```

Or install from source:

```bash
git clone https://github.com/ahbond/research-dashboard.git
cd research-dashboard
pip install -e .
```

## Usage

```bash
research-dashboard
```

### Options

| Flag               | Description                                |
|--------------------|--------------------------------------------|
| `--session-name`   | Tmux session name (default: `atlas-dash`)  |
| `--no-gpu`         | Skip GPU monitoring pane                   |
| `--no-net`         | Skip network monitoring pane               |
| `--no-disk`        | Skip disk I/O monitoring pane              |
| `--dry-run`        | Print tmux commands without executing them |

### Examples

```bash
# Launch with defaults
research-dashboard

# Custom session name, skip network pane
research-dashboard --session-name ml-monitor --no-net

# Preview commands without launching
research-dashboard --dry-run
```

## Layout

```
+---------------------+----------------------+
|    nvtop (GPUs)     |   htop (processes)   |
|                     |                       |
+----------+----------+----------+------------+
| iotop    | nethogs  | sensors  | live logs  |
| (disk)   | (net)    | raid/df  |            |
+----------+----------+----------+------------+
```

- **Top-left** -- GPU monitoring via `nvtop` (falls back to `nvidia-smi watch`)
- **Top-right** -- Process monitoring via `htop` (falls back to `btop` or `top`)
- **Bottom-left** -- Disk I/O via `iotop` (falls back to `iostat`)
- **Bottom-mid-left** -- Network via `nethogs` (falls back to `nload` or `/proc/net/dev`)
- **Bottom-mid-right** -- Temperatures, GPU stats, RAID status, disk usage
- **Bottom-right** -- Live log tailing from `/tmp/*.log`

## Requirements

- **tmux** (required)
- Optional monitoring tools (the dashboard adapts to what is installed):
  - `nvtop` or `nvidia-smi` -- GPU monitoring
  - `htop`, `btop`, or `top` -- process monitoring
  - `iotop` or `iostat` -- disk I/O
  - `nethogs` or `nload` -- network monitoring
  - `sensors` (lm-sensors) -- temperature readings

Install everything on Ubuntu/Debian:

```bash
sudo apt install tmux nvtop htop iotop nethogs lm-sensors
```

## License

MIT
