from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from audio_preprocessing import duration_seconds, extract_clip


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("audio", type=Path)
    p.add_argument("comparison_csv", type=Path)
    p.add_argument("out_dir", type=Path)
    p.add_argument("--score-column", required=True)
    p.add_argument("--threshold", type=float, default=75.0)
    p.add_argument("--padding", type=float, default=5.0)
    args = p.parse_args()
    with args.comparison_csv.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    selected = [r for r in rows if float(r[args.score_column]) < args.threshold]
    total = duration_seconds(args.audio)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    chunks = []
    for index, row in enumerate(selected):
        start = max(0.0, float(row["start"]) - args.padding)
        end = min(total, float(row["end"]) + args.padding)
        target = args.out_dir / f"review_{index:02d}_{round(start*1000):010d}_{round(end*1000):010d}.wav"
        extract_clip(args.audio, target, start, end - start)
        chunks.append({
            "index": index,
            "start": start,
            "end": end,
            "path": str(target.resolve()),
            "comparison_score": float(row[args.score_column]),
            "small_transcript": row["new_transcript"],
        })
    manifest = {"source": str(args.audio.resolve()), "duration": total, "chunks": chunks}
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"selected={len(chunks)}")


if __name__ == "__main__":
    main()
