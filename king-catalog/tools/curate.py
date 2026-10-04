#!/usr/bin/env python3
"""Turn the photo-intake results into data/products.json and copy the crops.

Usage: python3 tools/curate.py intake.json crops_dir

intake.json is the list produced by the photo intake step (one entry per
photo: collection, names, crop path, ...). Products are grouped by
collection, ordered by SERIES_ORDER inside each collection, numbered
KING-<collection>-NNN and their crops copied to assets/img/products/.
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
COLLECTION_ORDER = ["500", "300", "100", "2in1", "60", "40", "accessory"]
CODE_PREFIX = {"500": "KING-500", "300": "KING-300", "100": "KING-100", "2in1": "KING-2IN1",
               "60": "KING-60", "40": "KING-40", "accessory": "KING-ACC"}

# 500-piece numbering follows the client's earlier catalogue (001-009); new designs follow.
ART_ORDER = ["The Chess Players", "The Last Supper", "The Kiss", "The Great Wave", "The Starry Night",
             "The Coronation of Napoleon", "Classic Garage", "Antique World Map", "The Death of Socrates",
             "The Accolade"]
# Same characters stay next to each other inside every collection.
SERIES_ORDER = ["Paw Patrol", "Kuromi", "My Melody", "Little Princess", "My Magical Unicorn", "Stitch",
                "Minecraft", "SpongeBob", "Toy Story", "Zootopia", "Minions", "Capybara", "Labubu",
                "Explore Space", "Space", "Roro Jump", "Dino Party"]


def series_rank(name):
    for i, s in enumerate(SERIES_ORDER):
        if name.lower().startswith(s.lower()):
            return i
    return len(SERIES_ORDER)


def sort_key(p):
    if p["collection"] == "500":
        try:
            return (ART_ORDER.index(p["name_en"]), "")
        except ValueError:
            return (len(ART_ORDER), p["name_en"])
    return (series_rank(p["name_en"]), p["name_en"], p["variant_en"])


def main(intake_path, crops_dir):
    intake = json.loads(Path(intake_path).read_text(encoding="utf-8"))
    crops = Path(crops_dir)
    out_img = ROOT / "assets" / "img" / "products"
    out_img.mkdir(parents=True, exist_ok=True)
    products = []
    for it in intake:
        products.append({
            "collection": it["collection"],
            "source": Path(it["file"]).name,
            "crop": str(crops / (Path(it["file"]).stem + ".jpg")),
            "name_en": it["design_en"].strip(),
            "variant_en": it["variant_en"].strip(),
            "name_fa": it["design_fa"].strip(),
            "variant_fa": it["variant_fa"].strip(),
            "artist": it["artist"].strip(),
            "pieces": it["pieces_label"].strip(),
            "factory_code": it["factory_code"].strip(),
            "badges": it["badges"],
            "orientation": it["orientation"],
            "hero_score": it["hero_score"],
        })
    result = []
    for col in COLLECTION_ORDER:
        group = sorted((p for p in products if p["collection"] == col), key=sort_key)
        for n, p in enumerate(group, 1):
            p["code"] = f"{CODE_PREFIX[col]}-{n:03d}"
            dst = out_img / f'{p["code"].lower()}.jpg'
            # Crop pixels are kept as they are; JPEG quality 88 keeps the PDFs small enough to send.
            Image.open(p.pop("crop")).convert("RGB").save(dst, quality=88, optimize=True)
            p["img"] = f"assets/img/products/{dst.name}"
            result.append(p)
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "products.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for p in result:
        print(p["code"], "|", p["name_en"], "|", p["variant_en"], "|", p["source"])


if __name__ == "__main__":
    main(*sys.argv[1:3])
