"""Render numbered contact sheets and report PDF text beyond its page boundary.

Contact sheets support manual review, not automatic visual acceptance.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import fitz
from PIL import Image, ImageDraw


def inspect(folder, output):
    if output.exists():
        raise ValueError("Use a fresh review output directory")
    output.mkdir(parents=True)
    records = []
    for language in ("en", "zh"):
        for entry in ("main", "supplement", "audit-notes"):
            path = folder / language / (entry+".pdf")
            with fitz.open(path) as doc:
                outside = []
                sheets = []
                for first in range(0, len(doc), 12):
                    canvas = Image.new("RGB", (1800, 4*660), "#dddddd")
                    draw = ImageDraw.Draw(canvas)
                    for i in range(first, min(first+12, len(doc))):
                        page = doc[i]
                        pix = page.get_pixmap(matrix=fitz.Matrix(.72, .72), alpha=False)
                        thumb = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                        thumb.thumbnail((580, 625))
                        x, y = ((i-first)%3)*600, ((i-first)//3)*660
                        canvas.paste(thumb, (x+(600-thumb.width)//2, y+28))
                        draw.text((x+15, y+8), f"{language}/{entry} page {i+1}", fill="black")
                        for block in page.get_text("dict")["blocks"]:
                            for line in block.get("lines", []):
                                for span in line["spans"]:
                                    rect = fitz.Rect(span["bbox"])
                                    if not (page.rect+(-1,-1,1,1)).contains(rect):
                                        outside.append({"page": i+1, "text": span["text"], "bbox": list(rect)})
                    name = f"{language}-{entry}-{first+1:03d}.png"
                    canvas.save(output / name)
                    sheets.append(name)
                records.append({"language": language, "entry": entry, "pages": len(doc),
                    "pdf_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "sheets": sheets,
                    "text_outside_page": outside, "human_visual_review": "pending"})
    result = {"schema_version": "pirc17-revision46-page-inspection-v1", "documents": records,
              "automatic_check_is_not_manual_acceptance": True}
    (output / "inspection.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.build_dir, args.output_dir)
    print({d["language"]+"/"+d["entry"]: {"pages": d["pages"], "outside": len(d["text_outside_page"])}
           for d in result["documents"]})
