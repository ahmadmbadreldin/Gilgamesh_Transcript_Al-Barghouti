from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

import av
import imageio_ffmpeg


def duration_seconds(path: Path) -> float:
    with av.open(str(path)) as container:
        if container.duration is not None:
            return float(container.duration / av.time_base)
        stream = next(s for s in container.streams if s.type == "audio")
        return float(stream.duration * stream.time_base)


def extract_clip(source: Path, target: Path, start: float, duration: float) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{start:.3f}", "-i", str(source), "-t", f"{duration:.3f}",
        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target),
    ]
    subprocess.run(cmd, check=True)


def create_chunks(source: Path, out_dir: Path, chunk_seconds: float, overlap: float) -> dict:
    if overlap < 0 or overlap >= chunk_seconds:
        raise ValueError("overlap must be >= 0 and < chunk_seconds")
    total = duration_seconds(source)
    step = chunk_seconds - overlap
    count = max(1, math.ceil(max(0.0, total - overlap) / step))
    items = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        start = index * step
        if start >= total:
            break
        end = min(total, start + chunk_seconds)
        target = out_dir / f"chunk_{index:04d}_{round(start*1000):010d}_{round(end*1000):010d}.wav"
        if not target.exists() or target.stat().st_size == 0:
            extract_clip(source, target, start, end - start)
        items.append({"index": index, "start": start, "end": end, "path": str(target.resolve())})
    manifest = {
        "source": str(source.resolve()),
        "duration": total,
        "chunk_seconds": chunk_seconds,
        "overlap": overlap,
        "chunks": items,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("out_dir", type=Path)
    p.add_argument("--chunk-seconds", type=float, default=240.0)
    p.add_argument("--overlap", type=float, default=2.0)
    p.add_argument("--clip-start", type=float)
    p.add_argument("--clip-duration", type=float, default=45.0)
    args = p.parse_args()
    if args.clip_start is not None:
        target = args.out_dir / f"test_{round(args.clip_start):06d}_{round(args.clip_duration):03d}.wav"
        extract_clip(args.source, target, args.clip_start, args.clip_duration)
        print(target)
    else:
        print(json.dumps(create_chunks(args.source, args.out_dir, args.chunk_seconds, args.overlap), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

