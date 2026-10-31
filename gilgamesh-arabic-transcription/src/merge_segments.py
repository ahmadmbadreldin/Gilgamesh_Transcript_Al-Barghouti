from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def norm_word(word: str) -> str:
    return re.sub(r"[^\u0621-\u064A0-9]", "", word).replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")


def overlap_size(left: list[str], right: list[str], limit: int = 30) -> int:
    a = [norm_word(w) for w in left[-limit:]]
    b = [norm_word(w) for w in right[:limit]]
    best = 0
    for n in range(1, min(len(a), len(b)) + 1):
        if a[-n:] == b[:n] and all(a[-n:]):
            best = n
    return best


def merge(raw_dir: Path) -> dict:
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(raw_dir.glob("chunk_*.json"))]
    merged_words: list[dict] = []
    chunk_summaries = []
    for rec in records:
        offset = float(rec.get("metadata", {}).get("start", 0.0))
        words = []
        for seg in rec["segments"]:
            for w in seg.get("words", []):
                words.append({**w, "start": w["start"] + offset, "end": w["end"] + offset})
        n = overlap_size([w["word"] for w in merged_words], [w["word"] for w in words])
        merged_words.extend(words[n:])
        chunk_summaries.append({
            "index": rec.get("metadata", {}).get("index"),
            "start": offset,
            "end": rec.get("metadata", {}).get("end"),
            "overlap_words_removed": n,
            "elapsed_seconds": rec.get("elapsed_seconds"),
            "segment_count": len(rec["segments"]),
        })
    text = " ".join(w["word"].strip() for w in merged_words if w["word"].strip())
    return {"text": text, "words": merged_words, "chunks": chunk_summaries, "chunk_count": len(records)}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("raw_dir", type=Path)
    p.add_argument("output_json", type=Path)
    p.add_argument("output_txt", type=Path)
    args = p.parse_args()
    result = merge(args.raw_dir)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_txt.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_txt.write_text(result["text"] + "\n", encoding="utf-8")
    print(f"chunks={result['chunk_count']} words={len(result['words'])}")


if __name__ == "__main__":
    main()

