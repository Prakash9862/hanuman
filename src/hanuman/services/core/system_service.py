from __future__ import annotations

import os
import platform
import shutil
import socket
import sys
from typing import Any, Dict, Optional


def _read_proc_uptime() -> Optional[float]:
    path = "/proc/uptime"
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = handle.read().strip().split()[0]
            return float(value)
    except (OSError, ValueError):
        return None


def _read_proc_meminfo() -> Dict[str, int]:
    path = "/proc/meminfo"
    if not os.path.exists(path):
        return {}
    data: Dict[str, int] = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                parts = value.strip().split()
                if not parts:
                    continue
                try:
                    data[key] = int(parts[0]) * 1024
                except ValueError:
                    continue
    except OSError:
        return {}
    return data


def get_system_status() -> Dict[str, Any]:
    uptime_seconds = _read_proc_uptime()
    meminfo = _read_proc_meminfo()
    disk_usage = shutil.disk_usage("/")
    load_avg = None

    if hasattr(os, "getloadavg"):
        try:
            load_avg = os.getloadavg()
        except OSError:
            load_avg = None

    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "load_average": load_avg,
        "uptime_seconds": uptime_seconds,
        "memory_total_bytes": meminfo.get("MemTotal"),
        "memory_available_bytes": meminfo.get("MemAvailable"),
        "disk_total_bytes": disk_usage.total,
        "disk_free_bytes": disk_usage.free,
    }
