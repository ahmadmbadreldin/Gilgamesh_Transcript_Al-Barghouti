from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PY = sys.executable


def run(*args: str) -> None:
    subprocess.run([PY, *args], cwd=ROOT, check=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["environment", "chunk", "transcribe", "merge", "compare"])
    args = p.parse_args()
    audio = ROOT / "input/audio/تميم البرغوثي ملحمه كلكامش.mp3"
    chunks = ROOT / "data/chunks"
    raw = ROOT / "data/raw_transcripts"
    merged = ROOT / "data/aligned_transcripts/merged.json"
    if args.stage == "environment":
        run("src/environment_check.py")
    elif args.stage == "chunk":
        run("src/audio_preprocessing.py", str(audio), str(chunks), "--chunk-seconds", "240", "--overlap", "2")
    elif args.stage == "transcribe":
        run("src/transcription.py", str(chunks / "manifest.json"), str(raw), "--model", "models/faster-whisper-small", "--beam-size", "5")
    elif args.stage == "merge":
        run("src/merge_segments.py", str(raw), str(merged), str(ROOT / "output/txt/التفريغ_الآلي_الخام.txt"))
    elif args.stage == "compare":
        refs = sorted((ROOT / "input/references").glob("*.txt"))
        run(
            "src/text_comparison.py",
            str(merged),
            *(str(r) for r in refs),
            "--output-csv",
            str(ROOT / "output/reports/اختلافات_المصادر.csv"),
        )


if __name__ == "__main__":
    main()

