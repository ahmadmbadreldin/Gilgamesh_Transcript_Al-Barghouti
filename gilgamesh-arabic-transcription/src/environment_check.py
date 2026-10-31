from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import psutil


def collect(workspace: Path) -> dict:
    vm = psutil.virtual_memory()
    disk = shutil.disk_usage(workspace)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = {
        "platform": platform.platform(),
        "python": sys.version,
        "python_executable": sys.executable,
        "cpu_physical": psutil.cpu_count(logical=False),
        "cpu_logical": psutil.cpu_count(logical=True),
        "ram_total_gb": round(vm.total / 2**30, 3),
        "ram_available_gb": round(vm.available / 2**30, 3),
        "disk_total_gb": round(disk.total / 2**30, 3),
        "disk_free_gb": round(disk.free / 2**30, 3),
        "ffmpeg": ffmpeg,
        "ffprobe_on_path": shutil.which("ffprobe"),
        "nvidia_smi_on_path": shutil.which("nvidia-smi"),
    }
    if result["nvidia_smi_on_path"]:
        p = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        result["gpu"] = p.stdout.strip() or p.stderr.strip()
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    report = collect(root)
    out = root / "output" / "reports" / "environment.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

