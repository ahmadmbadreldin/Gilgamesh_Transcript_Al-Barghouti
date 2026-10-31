from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from faster_whisper import WhisperModel


DEFAULT_PROMPT = "ملحمة جلجامش، تميم البرغوثي، أنكيدو، خُمبابا، عشتار، أوتنابشتم."


def transcribe_file(model: WhisperModel, audio: Path, settings: dict, metadata: dict | None = None) -> dict:
    started = time.time()
    segments_iter, info = model.transcribe(
        str(audio),
        language="ar",
        task="transcribe",
        beam_size=settings["beam_size"],
        best_of=settings.get("best_of", settings["beam_size"]),
        vad_filter=settings["vad_filter"],
        word_timestamps=True,
        condition_on_previous_text=False,
        initial_prompt=settings.get("initial_prompt", DEFAULT_PROMPT),
        temperature=0.0,
        compression_ratio_threshold=2.4,
        log_prob_threshold=-1.0,
        no_speech_threshold=0.6,
    )
    segments = []
    for s in segments_iter:
        words = []
        for w in s.words or []:
            words.append({
                "start": w.start,
                "end": w.end,
                "word": w.word,
                "probability": w.probability,
            })
        segments.append({
            "id": s.id,
            "start": s.start,
            "end": s.end,
            "text": s.text.strip(),
            "avg_logprob": s.avg_logprob,
            "compression_ratio": s.compression_ratio,
            "no_speech_prob": s.no_speech_prob,
            "words": words,
        })
    return {
        "audio": str(audio.resolve()),
        "metadata": metadata or {},
        "model": settings["model"],
        "device": settings["device"],
        "compute_type": settings["compute_type"],
        "settings": settings,
        "detected_language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "duration_after_vad": info.duration_after_vad,
        "elapsed_seconds": time.time() - started,
        "segments": segments,
        "text": "\n".join(s["text"] for s in segments if s["text"]),
    }


def write_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_model(settings: dict) -> WhisperModel:
    return WhisperModel(settings["model"], device=settings["device"], compute_type=settings["compute_type"], cpu_threads=settings["cpu_threads"])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path, help="audio file or chunks manifest.json")
    p.add_argument("output", type=Path)
    p.add_argument("--model", default="models/faster-whisper-small")
    p.add_argument("--device", default="cpu")
    p.add_argument("--compute-type", default="int8")
    p.add_argument("--cpu-threads", type=int, default=8)
    p.add_argument("--beam-size", type=int, default=5)
    p.add_argument("--vad-filter", action="store_true")
    args = p.parse_args()
    settings = vars(args).copy()
    settings["model"] = str(Path(args.model).resolve()) if Path(args.model).exists() else args.model
    for key in ("input", "output"):
        settings.pop(key, None)
    model = load_model(settings)
    if args.input.name == "manifest.json":
        manifest = json.loads(args.input.read_text(encoding="utf-8"))
        args.output.mkdir(parents=True, exist_ok=True)
        for item in manifest["chunks"]:
            audio = Path(item["path"])
            out = args.output / f"chunk_{item['index']:04d}.json"
            if out.exists() and out.stat().st_size > 100:
                print(f"SKIP {item['index']:04d} {out}", flush=True)
                continue
            print(f"START {item['index']:04d} {item['start']:.3f}-{item['end']:.3f}", flush=True)
            result = transcribe_file(model, audio, settings, item)
            write_atomic(out, result)
            print(f"DONE {item['index']:04d} elapsed={result['elapsed_seconds']:.1f}s", flush=True)
    else:
        result = transcribe_file(model, args.input, settings)
        write_atomic(args.output, result)
        print(result["text"])


if __name__ == "__main__":
    main()

