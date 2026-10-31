from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from rapidfuzz import fuzz


def normalize(s: str) -> str:
    s = re.sub(r"[\u064B-\u065F\u0670]", "", s)
    s = s.translate(str.maketrans("أإآةىؤئ", "اااهيوي"))
    return re.sub(r"[^\u0621-\u064A0-9 ]+", " ", s).strip()


def locate_partial_end(asr_words: list[dict], ref_tokens: list[str]) -> tuple[int, float]:
    target = " ".join(ref_tokens[-35:])
    best_score, best_end = 0.0, 0
    for i in range(0, max(1, len(asr_words) - 50), 5):
        candidate = " ".join(w["word"] for w in asr_words[i:i + 50])
        score = fuzz.token_set_ratio(normalize(target), normalize(candidate))
        if score > best_score:
            best_score, best_end = score, i + 50
    return min(best_end, len(asr_words)), best_score


def local_match(piece: str, ref_tokens: list[str], expected: int, radius: int = 110) -> tuple[str, float, int]:
    piece_len = max(20, len(piece.split()))
    lo = max(0, expected - radius)
    hi = min(max(0, len(ref_tokens) - piece_len), expected + radius)
    best = ("", 0.0, expected)
    for start in range(lo, hi + 1, 3):
        candidate = " ".join(ref_tokens[start:start + piece_len])
        score = fuzz.WRatio(normalize(piece), normalize(candidate))
        if score > best[1]:
            best = (candidate, score, start)
    return best


def align(asr_json: Path, references: list[Path]) -> list[dict]:
    data = json.loads(asr_json.read_text(encoding="utf-8"))
    refs = []
    for path in references:
        lines = [
            x.strip() for x in path.read_text(encoding="utf-8-sig").splitlines()
            if x.strip() and "الملحمة ليست مكتوبة" not in x
        ]
        tokens = " ".join(lines).split()
        refs.append((path.name, tokens))
    words = data["words"]
    ref_meta = []
    for name, tokens in refs:
        if len(tokens) < len(words) * 0.55:
            coverage_end, end_score = locate_partial_end(words, tokens)
        else:
            coverage_end, end_score = len(words), 100.0
        ref_meta.append((name, tokens, coverage_end, end_score))
    rows = []
    block = 35
    for i in range(0, len(words), block):
        piece = words[i:i + block]
        raw = " ".join(w["word"].strip() for w in piece)
        row = {"start": piece[0]["start"], "end": piece[-1]["end"], "new_transcript": raw}
        human_supported = False
        auto_supported = False
        for name, tokens, coverage_end, _end_score in ref_meta:
            if i >= coverage_end:
                row[name] = ""
                row[name + " score"] = 0
                continue
            usable_asr = max(1, coverage_end - len(piece))
            usable_ref = max(1, len(tokens) - len(piece))
            expected = round(i / usable_asr * usable_ref)
            candidate, score, _start = local_match(raw, tokens, expected)
            row[name] = candidate
            row[name + " score"] = round(score, 2)
            if len(tokens) < len(words) * 0.55 and score >= 80:
                human_supported = True
            if len(tokens) >= len(words) * 0.55 and score >= 80:
                auto_supported = True
        if human_supported:
            row["status"] = "مؤيد بمصدر نصي بشري"
        elif auto_supported:
            row["status"] = "مؤيد باتفاق تفريغين آليين"
        else:
            row["status"] = "غير محسوم"
        rows.append(row)
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("asr_json", type=Path)
    p.add_argument("references", type=Path, nargs="+")
    p.add_argument("--output-csv", type=Path, required=True)
    args = p.parse_args()
    rows = align(args.asr_json, args.references)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()

