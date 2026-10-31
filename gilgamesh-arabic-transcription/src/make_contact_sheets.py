from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw


def page_number(path: Path) -> int:
    return int(re.search(r"(\d+)", path.stem).group(1))


def ink_metrics(image: Image.Image) -> dict:
    gray = image.convert("L")
    mask = gray.point(lambda x: 255 if x < 245 else 0)
    bbox = mask.getbbox()
    histogram = mask.histogram()
    ink = histogram[255]
    return {
        "width": image.width,
        "height": image.height,
        "ink_pixels": ink,
        "ink_ratio": ink / (image.width * image.height),
        "bbox": bbox,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("render_dir", type=Path)
    p.add_argument("out_dir", type=Path)
    args = p.parse_args()
    pages = sorted(args.render_dir.glob("page-*.png"), key=page_number)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    metrics = []
    opened = []
    for path in pages:
        image = Image.open(path).convert("RGB")
        opened.append((page_number(path), image.copy()))
        metrics.append({"page": page_number(path), **ink_metrics(image)})
        image.close()
    for batch_start in range(0, len(opened), 4):
        batch = opened[batch_start:batch_start + 4]
        cell_w = max(im.width for _, im in batch)
        cell_h = max(im.height for _, im in batch) + 42
        sheet = Image.new("RGB", (cell_w * 2, cell_h * 2), "#D0D0D0")
        draw = ImageDraw.Draw(sheet)
        for offset, (number, image) in enumerate(batch):
            x = (offset % 2) * cell_w
            y = (offset // 2) * cell_h
            sheet.paste(image, (x, y + 42))
            draw.text((x + 12, y + 12), f"PAGE {number}", fill="black")
        end_page = batch[-1][0]
        out = args.out_dir / f"pages_{batch[0][0]:02d}_{end_page:02d}.png"
        sheet.save(out, optimize=True)
    (args.out_dir / "page_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps({
        "pages": len(metrics),
        "dimensions": sorted({(m['width'], m['height']) for m in metrics}),
        "low_ink_pages": [m['page'] for m in metrics if m['ink_ratio'] < 0.01],
        "contact_sheets": (len(opened) + 3) // 4,
    }, indent=2))


if __name__ == "__main__":
    main()
