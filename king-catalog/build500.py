#!/usr/bin/env python3
"""Generate the Persian and English KING 500-piece catalogues (HTML).

A shorter edition of the range catalogue for the 500-piece High Quality
Collection only: cover, About KING with the 500 badge, product features,
the ten designs and a closing page with the design list and contacts.
Shares data and page parts with build.py. Run `python3 build500.py` and
then `node render.cjs` to produce the PDFs.
"""
from html import escape

import build as B
from build import EN, FA, FRAME, ORN, ZW, fa_num, foot, head, icon, panel

ITEMS = B.items_of("500")
COLLECTION = next(c for c in B.COLLECTIONS if c["key"] == "500")
COVER_SOURCE = "59.webp"                            # The Starry Night
THUMBS = ["56.webp", "52.webp", "58.webp"]          # The Kiss, The Great Wave, Antique World Map
CODES = B.code_range(ITEMS)

FA500 = dict(FA, **{
    "doc_title": "کاتالوگ پازل ۵۰۰ قطعه کینگ",
    "foot_name": "پازل ۵۰۰ قطعه کینگ",
    "cover_title": "پازل ۵۰۰ قطعه کینگ",
    "cover_caps": "500 Pieces Puzzle Collection",
    "head_caps": "KING · 500 PIECES",
    "about_lead": (
        f"کینگ برندی است که کیفیت را معیار اصلی کار خود می{ZW}داند. در مجموعهٔ پازل{ZW}های ۵۰۰ قطعه، "
        f"آثار ماندگار هنری و طرح{ZW}های محبوب با دقت در ساخت و توجه به جزئیات به پازل تبدیل شده{ZW}اند "
        f"تا محصولی قابل اعتماد و ارزشمند برای فروشگاه{ZW}ها، پخش{ZW}کنندگان و دوستداران پازل فراهم شود."
    ),
    "intro_eyebrow": "KING 500 PIECES PUZZLE",
    "intro_h3": "پازل ۵۰۰ قطعه کینگ",
    "intro": (
        f"پازل{ZW}های ۵۰۰ قطعه کینگ با ترکیب کیفیت ساخت، برش دقیق و چاپ با وضوح بالا، "
        f"تجربه{ZW}ای لذت{ZW}بخش از ساخت پازل ارائه می{ZW}کنند. تنوع بالای طرح{ZW}ها، این مجموعه را "
        f"برای سلیقه{ZW}ها و علاقه{ZW}مندی{ZW}های گوناگون به انتخابی جذاب تبدیل کرده است."
    ),
    "specs": [
        ("برند", "KING", True),
        ("تعداد قطعات", "500 PIECES", True),
        (f"طرح{ZW}های این کاتالوگ", f"{fa_num(len(ITEMS))} طرح", False),
        ("کد محصولات", CODES, True),
    ],
    "badge_sub": "قطعه",
    "features_p": f"چهار ویژگی که کیفیت پازل{ZW}های ۵۰۰ قطعه کینگ را تعریف می{ZW}کنند.",
    "designs_head": f"مجموعه طرح{ZW}ها",
    "closing_pieces": "پازل ۵۰۰ قطعه",
    "list_head": f"اسامی طرح{ZW}ها",
    "list_caps": "THE DESIGNS",
})

EN500 = dict(EN, **{
    "doc_title": "KING 500 Pieces Puzzle Catalogue",
    "foot_name": "KING 500 Pieces Puzzle",
    "cover_caps": "500 Pieces Puzzle Collection",
    "head_caps": "KING · 500 PIECES",
    "about_lead": (
        "KING is a brand that holds quality as its defining standard. In the 500-piece puzzle collection, "
        "timeless works of art and much-loved designs are turned into puzzles with careful craftsmanship and "
        "close attention to detail, creating a reliable, valuable product for retailers, distributors and "
        "puzzle enthusiasts alike."
    ),
    "intro_eyebrow": "THE COLLECTION",
    "intro_h3": "KING 500 Pieces Puzzle",
    "intro": (
        "KING 500-piece puzzles combine quality construction, precise cutting and high-resolution printing "
        "to deliver a genuinely enjoyable puzzling experience. A wide variety of designs makes the collection "
        "an attractive choice for every taste and interest."
    ),
    "specs": [
        ("Brand", "KING", True),
        ("Piece count", "500 PIECES", True),
        ("Designs in this catalogue", f"{len(ITEMS)} DESIGNS", True),
        ("Product codes", CODES, True),
    ],
    "badge_sub": "in every puzzle",
    "selected_em": "from the collection",
    "features_p": "Four qualities that define every KING 500-piece puzzle.",
    "designs_head": "The Designs",
    "closing_pieces": "500 Pieces Puzzle Collection",
    "list_head": "The Designs",
    "list_caps": "COLLECTION INDEX",
})


def page_about(t, folio):
    fa = t["lang"] == "fa"
    specs = "".join(
        f'<div><dt>{escape(k)}</dt><dd class="{"latin" if latin else ""}">{escape(v)}</dd></div>'
        for k, v, latin in t["specs"])
    by_src = {p["source"]: p for p in ITEMS}
    thumbs = "".join(
        f'<figure>{panel(by_src[s])}'
        f'<figcaption>{escape(by_src[s]["name_fa"] if fa else by_src[s]["name_en"])}</figcaption></figure>'
        for s in THUMBS)
    return f'''
<section class="page about about500">
  {head(t["about_head"], t["head_caps"])}
  <div class="body">
    <div class="eyebrow caps latin">{escape(t["about_eyebrow"])}</div>
    <h2>{escape(t["about_h2"])}</h2>
    <p class="lead">{escape(t["about_lead"])}</p>
    <div class="split">
      <div>
        <div class="eyebrow caps latin">{escape(t["intro_eyebrow"])}</div>
        <h3>{escape(t["intro_h3"])}</h3>
        <p class="intro">{escape(t["intro"])}</p>
        <dl class="specs">{specs}</dl>
      </div>
      <div class="badge">
        <div class="num latin">500</div>
        <div class="caps latin">Pieces</div>
        {ORN}
        <div class="sub">{escape(t["badge_sub"])}</div>
      </div>
    </div>
    <div class="section-title"><strong>{escape(t["selected"])}</strong><span class="line"></span><em>{escape(t["selected_em"])}</em></div>
    <div class="thumbs">{thumbs}</div>
  </div>
  {foot(t, folio)}
</section>'''


def page_products(t, folio, items):
    rows = "".join(B.product_row(t, p, i % 2 == 1) for i, p in enumerate(items))
    caps = f'Designs {items[0]["code"][-3:]} — {items[-1]["code"][-3:]}'
    return f'''
<section class="page designs">
  {head(t["designs_head"], caps)}
  <div class="body"><div class="products n{len(items)}">{rows}
  </div></div>
  {foot(t, folio)}
</section>'''


def page_closing(t):
    fa = t["lang"] == "fa"
    rows = []
    for p in ITEMS:
        nm, alt = (p["name_fa"], p["name_en"]) if fa else (p["name_en"], p["artist"])
        rows.append(f'<li><span class="nm">{escape(nm)}</span><span class="alt">{escape(alt)}</span>'
                    f'<span class="dots"></span><span class="cd">{escape(p["code"])}</span></li>')
    items = []
    for ic, lbl, val, kind in t["contact"]:
        cls = "item wide" if kind == "wide" else "item"
        vcls = "val latin" if kind == "latin" else "val"
        items.append(f'<div class="{cls}"><span class="ic">{icon(ic)}</span>'
                     f'<div><div class="lbl">{escape(lbl)}</div><div class="{vcls}">{val}</div></div></div>')
    slogan_fa = f'<p class="slogan-fa">{escape(FA["slogan_fa"])}</p>' if fa else ""
    return f'''
<section class="page closing closing500">
  {FRAME}
  <div class="closing-inner">
    <img class="logo" src="assets/img/king-logo.png" alt="KING">
    <div class="brand latin">KING</div>
    <div class="pieces caps latin">500 Pieces</div>
    <div class="pieces-fa">{escape(t["closing_pieces"])}</div>
    <div class="list-head"><div class="row"><i></i><strong>{escape(t["list_head"])}</strong><i></i></div><div class="caps latin">{escape(t["list_caps"])}</div></div>
    <ul class="design-list">{"".join(rows)}</ul>
    <div class="contact">
      <span class="c tl"></span><span class="c tr"></span><span class="c bl"></span><span class="c br"></span>
      <div class="head"><div class="row"><i></i><strong>{escape(t["contact_head"])}</strong><i></i></div><div class="caps latin">{escape(t["contact_caps"])}</div></div>
      <div class="grid">{"".join(items)}</div>
    </div>
    <div class="ornament solid end"><i></i><b></b><i></i></div>
    {slogan_fa}
    <p class="slogan-en">Quality Never Goes Out of Style</p>
  </div>
</section>'''


def build(t):
    hero = next(p for p in ITEMS if p["source"] == COVER_SOURCE)
    pages = [B.page_cover(t, hero), page_about(t, 2), B.page_features(t, 3)]
    folio = 4
    for chunk in B.paginate(ITEMS, "rows"):
        pages.append(page_products(t, folio, chunk))
        folio += 1
    pages.append(page_closing(t))
    return f'''<!doctype html>
<html lang="{t["lang"]}" dir="{t["dir"]}">
<head>
<meta charset="utf-8">
<title>{escape(t["doc_title"])}</title>
<link rel="stylesheet" href="assets/catalog.css">
</head>
<body>{"".join(pages)}
</body>
</html>
'''


if __name__ == "__main__":
    for t, name in ((FA500, "catalog500-fa.html"), (EN500, "catalog500-en.html")):
        (B.ROOT / name).write_text(build(t), encoding="utf-8")
        print("wrote", name)
