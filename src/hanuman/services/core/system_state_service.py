from __future__ import annotations

import os
import platform
import shutil
import sys
from datetime import UTC, datetime
from typing import Any, Dict, Optional


def _read_uptime_seconds() -> Optional[float]:
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as handle:
            raw = handle.read().strip().split()
    except FileNotFoundError:
        return None
    if not raw:
        return None
    try:
        return float(raw[0])
    except ValueError:
        return None


def _read_meminfo() -> Dict[str, int]:
    meminfo: Dict[str, int] = {}
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except FileNotFoundError:
        return meminfo

    for line in lines:
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        parts = raw_value.strip().split()
        if not parts:
            continue
        try:
            value = int(parts[0])
        except ValueError:
            continue
        if len(parts) > 1 and parts[1].lower() == "kb":
            value *= 1024
        meminfo[key.strip()] = value
    return meminfo


def get_system_state() -> Dict[str, Any]:
    """Retourne un état système léger sans dépendances externes."""
    load_avg: Optional[tuple[float, float, float]]
    try:
        load_avg = os.getloadavg()
    except (AttributeError, OSError):
        load_avg = None

    meminfo = _read_meminfo()
    disk = shutil.disk_usage("/")

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "load_avg": list(load_avg) if load_avg else None,
        "uptime_seconds": _read_uptime_seconds(),
        "memory": {
            "total_bytes": meminfo.get("MemTotal"),
            "available_bytes": meminfo.get("MemAvailable"),
        },
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
        },
    }
