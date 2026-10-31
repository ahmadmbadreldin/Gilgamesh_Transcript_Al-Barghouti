from __future__ import annotations

import csv
from pathlib import Path


def unresolved(csv_path: Path) -> list[dict]:
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        return [row for row in csv.DictReader(f) if row.get("status") == "غير محسوم"]

