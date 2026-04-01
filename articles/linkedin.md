# I Needed One Screen to Monitor Two GPUs, 48 CPU Cores, Three RAID Arrays, and a Dozen ML Experiments

So I built `research-dashboard` — a single command that opens a tmux session with everything you need to monitor an ML research workstation.

```
pip install research-dashboard
research-dashboard
```

## The Problem

Running ML experiments on a multi-GPU workstation means constantly switching between:
- `nvidia-smi` for GPU utilization
- `htop` for CPU and process monitoring
- `iotop` for disk I/O (is the data pipeline bottlenecking?)
- `nethogs` for network traffic (is the model still downloading?)
- `sensors` for CPU/GPU temperatures
- Various log files for experiment progress

That's six terminals. I kept losing track of which one had what.

## The Solution

One command opens a 6-panel tmux dashboard:

```
┌─────────────────────┬──────────────────────┐
│    nvtop (GPUs)     │   htop (processes)    │
│                     │                       │
├──────────┬──────────┼──────────┬────────────┤
│  iotop   │ nethogs  │ sensors  │ live logs   │
│  (disk)  │ (net)    │ RAID/df  │             │
└──────────┴──────────┴──────────┴────────────┘
```

- **Top-left:** nvtop — per-process GPU utilization, VRAM usage
- **Top-right:** htop — CPU processes sorted by usage, full command lines
- **Bottom-left:** iotop — which processes are hitting the disk
- **Bottom-center-left:** nethogs — per-process network bandwidth
- **Bottom-center-right:** sensors + RAID status + disk usage
- **Bottom-right:** live tail of experiment logs

## Smart Fallbacks

Not every machine has every tool. If nvtop isn't installed, it falls back to `watch nvidia-smi`. No htop? Uses btop or top. No nethogs? Uses nload or raw /proc/net/dev. It adapts to whatever is available.

## Why tmux?

Because it works over SSH. I monitor my workstation from my laptop, my phone (Termux), and occasionally from my desk. tmux sessions persist — I can detach, reconnect hours later, and everything is still there. No web browser needed, no port forwarding, no authentication tokens.

## The Stack

- Zero Python dependencies — it orchestrates system tools, nothing more
- tmux for the layout engine
- nvtop, htop, iotop, nethogs, sensors for the actual monitoring
- CLI flags to customize: `--no-gpu`, `--no-net`, `--no-disk`, `--session-name`
- 22 unit tests, CI with ruff + pytest

Built it while running a 31-dataset ML benchmark on a dual-GPU workstation. The dashboard paid for itself in the first hour — caught a thermal throttling issue that would have corrupted results.

MIT licensed. Works on any Linux machine with tmux.

- **PyPI:** https://pypi.org/project/research-dashboard/
- **GitHub:** https://github.com/ahb-sjsu/research-dashboard

Part of a suite with [research-portal](https://pypi.org/project/research-portal/) (web dashboard) and [batch-probe](https://pypi.org/project/batch-probe/) (GPU memory probing + thermal management).

---

#MachineLearning #Python #OpenSource #DevTools #GPU #Linux #Monitoring
