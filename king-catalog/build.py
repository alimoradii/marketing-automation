#!/usr/bin/env python3
"""Generate the Persian and English KING puzzle trade catalogues (HTML).

Products are read from data/products.json and grouped by collection
(500, 300, 100, 2-in-1, 60, 40 pieces, accessories). Run `python3 build.py`
and then `node render.cjs` to produce the PDFs.

Product photos in assets/img/products are the client's own photos, cropped
only; nothing else is changed.
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZW = "‌"  # zero-width non-joiner for Persian compound words

PRODUCTS = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
COVER_SOURCE = "59.webp"  # The Starry Night
ABOUT_THUMBS = ["56.webp", "47.jpg", "32.jpg", "7.jpg"]  # one design from four collections

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_num(s):
    return str(s).translate(FA_DIGITS)


ICONS = {
    "layers": '<path d="M12 3 3 7.5 12 12l9-4.5L12 3Z"/><path d="m3 12 9 4.5 9-4.5"/><path d="m3 16.5 9 4.5 9-4.5"/>',
    "puzzle": '<path d="M4 8h5.2a2.4 2.4 0 1 1 3.6 0H18v4.2a2.4 2.4 0 1 1 0 3.6V20H4v-4.2a2.4 2.4 0 1 0 0-3.6Z"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="9.5" r="1.8"/><path d="m21 15.5-5-5L6.5 20"/>',
    "grid": '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/>',
    "pin": '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/>',
    "phone": '<path d="M6.2 3.8h3l1.5 4-2 1.3a11.5 11.5 0 0 0 6.2 6.2l1.3-2 4 1.5v3a1.6 1.6 0 0 1-1.7 1.6C10.6 18.8 5.2 13.4 4.6 5.5a1.6 1.6 0 0 1 1.6-1.7Z"/>',
    "whatsapp": '<path d="M4 20.2 5.2 16.4A8.4 8.4 0 1 1 8 19.1Z"/><path d="M9.3 8.3c.3-.3.7-.3.9.1l.7 1.5c.1.3 0 .5-.2.7l-.5.5a4.8 4.8 0 0 0 2.8 2.8l.5-.5c.2-.2.4-.3.7-.2l1.5.7c.4.2.4.6.1.9-.6.6-1.4.9-2.2.7a6.4 6.4 0 0 1-4.6-4.6c-.2-.8.1-1.6.7-2.2Z"/>',
    "instagram": '<rect x="4" y="4" width="16" height="16" rx="4.5"/><circle cx="12" cy="12" r="3.6"/><circle cx="16.8" cy="7.2" r=".5"/>',
    "globe": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17"/><path d="M12 3.5c2.3 2.4 3.4 5.2 3.4 8.5s-1.1 6.1-3.4 8.5c-2.3-2.4-3.4-5.2-3.4-8.5s1.1-6.1 3.4-8.5Z"/>',
}


def icon(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


# ---------------------------------------------------------------- collections
# key, big numeral, Latin caps under it, layout, and copy per language.
COLLECTIONS = [
    {
        "key": "500", "num": "500", "caps": "Pieces", "layout": "rows", "hero": "52.webp",
        "fa": {
            "title": "پازل ۵۰۰ قطعه", "series": "High Quality Collection", "short": "۵۰۰ قطعه",
            "desc": (f"شاهکارهای ماندگار نقاشی و طرح{ZW}های کلاسیک، با برش دقیق و چاپ با وضوح بالا؛ "
                     f"انتخابی شایسته برای دوستداران هنر و پازل."),
        },
        "en": {
            "title": "500 Pieces Puzzles", "series": "High Quality Collection", "short": "500 Pieces",
            "desc": ("Timeless masterpieces and classic designs, precisely cut and printed in high "
                     "resolution — a refined choice for lovers of art and puzzles."),
        },
    },
    {
        "key": "300", "num": "300", "caps": "Pieces", "layout": "rows", "hero": "47.jpg",
        "fa": {
            "title": "پازل ۳۰۰ قطعه", "series": "Jigsaw Puzzle", "short": "۳۰۰ قطعه",
            "desc": (f"محبوب{ZW}ترین شخصیت{ZW}های کارتونی و انیمیشنی در قالب پازل ۳۰۰ قطعه؛ "
                     f"چالشی سرگرم{ZW}کننده با تصاویری پرجزئیات و رنگ{ZW}های شاد."),
        },
        "en": {
            "title": "300 Pieces Puzzles", "series": "Jigsaw Puzzle", "short": "300 Pieces",
            "desc": ("Best-loved cartoon and animation characters in a 300-piece format — an engaging "
                     "challenge with detailed, colourful artwork."),
        },
    },
    {
        "key": "100", "num": "100", "caps": "Pieces", "layout": "rows", "hero": "32.jpg",
        "fa": {
            "title": "پازل ۱۰۰ قطعه", "series": "Jigsaw Puzzle", "short": "۱۰۰ قطعه",
            "desc": (f"طرح{ZW}های شاد و پرطرفدار در قالب پازل ۱۰۰ قطعه؛ "
                     f"سرگرمی لذت{ZW}بخش برای کل خانواده و قدمی خوب برای آشنایی کودکان با دنیای پازل."),
        },
        "en": {
            "title": "100 Pieces Puzzles", "series": "Jigsaw Puzzle", "short": "100 Pieces",
            "desc": ("Bright, popular designs in a 100-piece format — enjoyable fun for the whole family "
                     "and a great first step into puzzling."),
        },
    },
    {
        "key": "2in1", "num": "2 in 1", "caps": "100 + 60 Pieces", "layout": "grid", "hero": "26.webp",
        "fa": {
            "title": f"دو پازل در یک جعبه", "series": "2 Fantastic Puzzles", "short": "۲ در ۱",
            "desc": (f"دو پازل ۱۰۰ و ۶۰ قطعه با دو تصویر متفاوت در یک جعبه؛ "
                     f"دو برابر سرگرمی با یک خرید."),
        },
        "en": {
            "title": "Two Puzzles in One Box", "series": "2 Fantastic Puzzles", "short": "2 in 1",
            "desc": ("Two puzzles of 100 and 60 pieces with two different pictures in one box — "
                     "double the fun in a single purchase."),
        },
    },
    {
        "key": "60", "num": "60", "caps": "Pieces · Big Size", "layout": "rows", "hero": "13.jpg",
        "fa": {
            "title": "پازل ۶۰ قطعه کودکانه", "series": "Big Size", "short": "۶۰ قطعه",
            "desc": (f"قطعات بزرگ و تصاویر شاد از شخصیت{ZW}های محبوب کودکان؛ "
                     f"ساخته{ZW}شده برای دست{ZW}های کوچک."),
        },
        "en": {
            "title": "60 Pieces Kids Puzzles", "series": "Big Size", "short": "60 Pieces",
            "desc": ("Big Size pieces and cheerful artwork featuring children's favourite characters — "
                     "made for little hands."),
        },
    },
    {
        "key": "40", "num": "40", "caps": "Pieces · Big Size", "layout": "rows", "hero": "7.jpg",
        "fa": {
            "title": f"پازل ۴۰ قطعه کودکانه آموزشی", "series": "Educational · Big Size", "short": "۴۰ قطعه",
            "desc": (f"پازل{ZW}های آموزشی با قطعات بزرگ برای کودکان ۴ سال به بالا؛ "
                     f"یادگیری مفاهیم اولیه همراه با بازی."),
        },
        "en": {
            "title": "40 Pieces Educational Puzzles", "series": "Educational · Big Size", "short": "40 Pieces",
            "desc": "Educational Big Size puzzles for ages 4+ — learning first concepts through play.",
        },
    },
    {
        "key": "accessory", "num": "", "caps": "Accessories", "layout": "feature", "hero": None,
        "fa": {
            "title": "لوازم جانبی", "series": "Accessories", "short": "لوازم جانبی",
            "desc": f"محصولات تکمیلی کینگ برای نگهداری و نمایش پازل{ZW}های تکمیل{ZW}شده.",
        },
        "en": {
            "title": "Accessories", "series": "Accessories", "short": "Accessories",
            "desc": "KING essentials for preserving and displaying completed puzzles.",
        },
    },
]


def items_of(key):
    return [p for p in PRODUCTS if p["collection"] == key]


# ---------------------------------------------------------------- copy
FA = {
    "lang": "fa", "dir": "rtl",
    "doc_title": "کاتالوگ محصولات پازل کینگ",
    "foot_name": "کاتالوگ محصولات کینگ",
    "cover_title": "کاتالوگ محصولات پازل کینگ",
    "slogan_fa": f"کیفیت هرگز از مد نمی{ZW}افتد",
    "about_head": "معرفی کینگ",
    "about_eyebrow": "About KING",
    "about_h2": "کینگ؛ اصالت در هر قطعه",
    "about_lead": (
        f"کینگ برندی است که کیفیت را معیار اصلی کار خود می{ZW}داند. از پازل{ZW}های ۵۰۰ قطعه با آثار ماندگار هنری "
        f"تا پازل{ZW}های آموزشی کودکان، هر محصول با دقت در ساخت و توجه به جزئیات تولید می{ZW}شود تا انتخابی "
        f"قابل اعتماد و ارزشمند برای فروشگاه{ZW}ها، پخش{ZW}کنندگان و خانواده{ZW}ها باشد."
    ),
    "range_title": f"مجموعه{ZW}های کینگ",
    "range_em": "The Range",
    "selected": f"گزیده{ZW}ای از طرح{ZW}ها",
    "selected_em": "Selected Designs",
    "designs_word": "طرح",
    "items_word": "محصول",
    "page_word": "صفحه",
    "intro_title": "پازل کینگ",
    "intro": (
        f"پازل{ZW}های کینگ با ترکیب کیفیت ساخت، برش دقیق و چاپ با وضوح بالا، تجربه{ZW}ای لذت{ZW}بخش از "
        f"ساخت پازل ارائه می{ZW}کنند. تنوع بالای طرح{ZW}ها، این مجموعه را برای سلیقه{ZW}ها و "
        f"علاقه{ZW}مندی{ZW}های گوناگون به انتخابی جذاب تبدیل کرده است."
    ),
    "features_head": f"ویژگی{ZW}های محصول",
    "features_eyebrow": "PRODUCT FEATURES",
    "features_h2": f"ویژگی{ZW}های محصول",
    "features_p": f"چهار ویژگی که کیفیت پازل{ZW}های کینگ را تعریف می{ZW}کنند.",
    "features": [
        ("layers", "مقوای آبی درجه یک", "Premium Blue Board",
         "استفاده از مقوای آبی درجه یک برای ایجاد کیفیت و استحکام مناسب قطعات."),
        ("puzzle", f"برش{ZW}های دقیق", "Precise Cutting",
         f"برش دقیق قطعات برای اتصال مناسب و تجربه{ZW}ای بهتر هنگام ساخت پازل."),
        ("image", "وضوح تصویر بالا", "High Image Resolution",
         f"چاپ با وضوح تصویر بالا برای نمایش بهتر جزئیات و رنگ{ZW}های جذاب طرح."),
        ("grid", "تنوع بالای طرح", "Wide Variety of Designs",
         f"تنوع بالای طرح{ZW}ها برای سلیقه{ZW}ها و علاقه{ZW}مندی{ZW}های مختلف."),
    ],
    "collection_word": "مجموعه",
    "stat_designs": f"طرح{ZW}ها",
    "stat_codes": "کد محصولات",
    "stat_factory": "کد کارخانه",
    "pcs_small": "قطعه",
    "brand_small": "برند",
    "code_small": "کد",
    "index_head": "فهرست محصولات",
    "index_caps": "PRODUCT INDEX",
    "index_note": f"برای ثبت سفارش، کد محصول را اعلام کنید.",
    "closing_line": "پازل کینگ",
    "contact_head": "ارتباط با ما",
    "contact_caps": "CONTACT US",
    "contact": [
        ("pin", "آدرس", f"تهران، بازار، ۱۵ خرداد، کوچه مسجد جامع، پاساژ قلم", "wide"),
        ("phone", "تلفن", '<span class="ltr">۰۲۱ ۵۵۶۹ ۱۹۰۹</span><br><span class="ltr">۰۲۱ ۵۵۶۹ ۱۹۱۰</span>', ""),
        ("whatsapp", f"واتس{ZW}اپ", '<span class="ltr">۰۹۱۲ ۵۲۲ ۵۴۴۶</span>', ""),
        ("instagram", "اینستاگرام", '<span class="latin">@kinggroupamp</span>', "latin"),
        ("globe", f"وب{ZW}سایت", '<span class="latin">www.kingpuzzle.ir</span>', "latin"),
    ],
}

EN = {
    "lang": "en", "dir": "ltr",
    "doc_title": "KING Puzzle Catalogue",
    "foot_name": "KING Puzzle Catalogue",
    "about_head": "About KING",
    "about_eyebrow": "The Brand",
    "about_h2": "KING — Authenticity in Every Piece",
    "about_lead": (
        "KING is a brand that holds quality as its defining standard. From 500-piece puzzles of timeless "
        "works of art to educational puzzles for young children, every product is made with careful "
        "craftsmanship and close attention to detail — a reliable, valuable choice for retailers, "
        "distributors and families alike."
    ),
    "range_title": "The KING Range",
    "range_em": "at a glance",
    "selected": "Selected Designs",
    "selected_em": "from the range",
    "designs_word": "designs",
    "items_word": "products",
    "page_word": "page",
    "intro_title": "KING Puzzles",
    "intro": (
        "KING puzzles combine quality construction, precise cutting and high-resolution printing to deliver "
        "a genuinely enjoyable puzzling experience. A wide variety of designs makes the range an attractive "
        "choice for every taste and interest."
    ),
    "features_head": "Product Features",
    "features_eyebrow": "WHY KING",
    "features_h2": "Product Features",
    "features_p": "Four qualities that define every KING puzzle.",
    "features": [
        ("layers", "Premium Blue Board", None,
         "Premium-grade blue board gives every piece lasting quality and strength."),
        ("puzzle", "Precise Cutting", None,
         "Precisely cut pieces fit together securely for a better building experience."),
        ("image", "High Image Resolution", None,
         "High-resolution printing brings out fine detail and rich, vivid colour."),
        ("grid", "Wide Variety of Designs", None,
         "A wide range of designs to suit every taste and interest."),
    ],
    "collection_word": "Collection",
    "stat_designs": "Designs",
    "stat_codes": "Product codes",
    "stat_factory": "Factory code",
    "pcs_small": "per puzzle",
    "brand_small": "Brand",
    "code_small": "Code",
    "index_head": "Product Index",
    "index_caps": "ORDER REFERENCE",
    "index_note": "Please quote the product code when ordering.",
    "closing_line": "Puzzle Collection",
    "contact_head": "Contact Us",
    "contact_caps": "GET IN TOUCH",
    "contact": [
        ("pin", "Address", "Ghalam Passage, Masjed Jame Alley, 15 Khordad Street, Bazaar, Tehran, Iran", "wide"),
        ("phone", "Telephone", "+98 21 5569 1909<br>+98 21 5569 1910", ""),
        ("whatsapp", "WhatsApp", "+98 912 522 5446", ""),
        ("instagram", "Instagram", "@kinggroupamp", ""),
        ("globe", "Website", "www.kingpuzzle.ir", ""),
    ],
}

# ---------------------------------------------------------------- parts
ORN = '<div class="ornament"><i></i><b></b><i></i></div>'
FRAME = '<div class="frame"><span class="c tl"></span><span class="c tr"></span><span class="c bl"></span><span class="c br"></span></div>'


def num(t, n):
    return fa_num(n) if t["lang"] == "fa" else str(n)


def head(title, caps):
    return (f'<header class="running-head"><span class="title">{escape(title)}</span>'
            f'<span class="caps latin">{escape(caps)}</span></header>')


def foot(t, folio):
    return (f'<footer class="running-foot"><span class="name">{escape(t["foot_name"])}</span>'
            f'<span class="folio">{folio:02d}</span>'
            f'<span class="caps latin">KING COLLECTION</span></footer>')


def panel(p, cls="panel"):
    return f'<div class="{cls}"><img src="{p["img"]}" alt="{escape(p["name_en"])}"></div>'


def code_range(items):
    if len(items) == 1:
        return items[0]["code"]
    return f'{items[0]["code"]} — {items[-1]["code"].rsplit("-", 1)[1]}'


def pcs_box(t, p):
    label = p["pieces"]
    if not label:
        return ""
    return (f'<div class="pcs"><span class="n latin">{escape(label)}</span>'
            f'<span class="l"><span class="caps latin">Pieces</span><small>{escape(t["pcs_small"])}</small></span></div>')


def names(t, p, tag="h3"):
    fa = t["lang"] == "fa"
    name = p["name_fa"] if fa else p["name_en"]
    variant = p["variant_fa"] if fa else p["variant_en"]
    out = f'<{tag}>{escape(name)}</{tag}>'
    if variant:
        out += f'<div class="variant">{escape(variant)}</div>'
    if fa:
        alt = p["name_en"] + (f' — {p["variant_en"]}' if p["variant_en"] else "")
        out += f'<div class="en-name latin">{escape(alt)}</div>'
    if p["artist"]:
        out += f'<div class="artist latin">{escape(p["artist"])}</div>'
    return out


def tags(p):
    if not p["badges"]:
        return ""
    return f'<div class="tags latin">{" · ".join(escape(b) for b in p["badges"])}</div>'


def factory(t, p):
    if not p["factory_code"]:
        return ""
    return (f'<div class="brand-mini"><small>{escape(t["code_small"])}</small>'
            f'<b class="latin">{escape(p["factory_code"])}</b></div>')


def meta(t, p):
    return (f'<div class="meta">{pcs_box(t, p)}'
            f'<div class="brand-mini"><small>{escape(t["brand_small"])}</small><b class="latin">KING</b></div>'
            f'{factory(t, p)}</div>')


# ---------------------------------------------------------------- pages
def page_cover(t, hero):
    fa = t["lang"] == "fa"
    title = f'<div class="title-fa">{escape(t["cover_title"])}</div>' if fa else ""
    slogan_fa = f'<p class="slogan-fa">{escape(FA["slogan_fa"])}</p>' if fa else ""
    return f'''
<section class="page cover">
  {FRAME}
  <div class="cover-inner">
    <img class="logo" src="assets/img/king-logo.png" alt="KING">
    <h1 class="brand latin">KING</h1>
    <div class="collection caps latin">Puzzle Collection · Product Catalogue</div>
    {ORN}
    {title}
    <figure class="figure">{panel(hero)}</figure>
    <div class="after ornament solid"><i></i><b></b><i></i></div>
    {slogan_fa}
    <p class="slogan-en">Quality Never Goes Out of Style</p>
  </div>
</section>'''


def tile(big, name, meta_line):
    return f'''
      <div class="tile">
        {big}
        <div class="tname">{escape(name)}</div>
        <div class="tmeta">{escape(meta_line)}</div>
      </div>'''


def page_about(t, folio, starts):
    tiles = []
    for c in COLLECTIONS:
        items = items_of(c["key"])
        if not items:
            continue
        ct = c[t["lang"]]
        big = (f'<div class="tnum latin">{escape(c["num"])}</div>' if c["num"]
               else f'<div class="ticon">{icon("puzzle")}</div>')
        word = t["designs_word"] if c["key"] != "accessory" else t["items_word"]
        tiles.append(tile(big, ct["short"],
                          f'{num(t, len(items))} {word} · {t["page_word"]} {num(t, starts[c["key"]])}'))
    tiles.append(tile(f'<div class="ticon">{icon("grid")}</div>', t["index_head"],
                      f'{num(t, len(PRODUCTS))} {t["items_word"]} · {t["page_word"]} {num(t, starts["index"])}'))
    by_src = {p["source"]: p for p in PRODUCTS}
    short = {c["key"]: c[t["lang"]]["short"] for c in COLLECTIONS}
    thumbs = "".join(
        f'<figure>{panel(by_src[s])}<figcaption>'
        f'{escape(by_src[s]["name_fa"] if t["lang"] == "fa" else by_src[s]["name_en"])}'
        f'<small>{escape(short[by_src[s]["collection"]])}</small></figcaption></figure>'
        for s in ABOUT_THUMBS)
    return f'''
<section class="page about">
  {head(t["about_head"], "KING · PUZZLE COLLECTION")}
  <div class="body">
    <div class="eyebrow caps latin">{escape(t["about_eyebrow"])}</div>
    <h2>{escape(t["about_h2"])}</h2>
    <p class="lead">{escape(t["about_lead"])}</p>
    <div class="section-title"><strong>{escape(t["range_title"])}</strong><span class="line"></span><em>{escape(t["range_em"])}</em></div>
    <div class="tiles">{"".join(tiles)}
    </div>
    <div class="section-title thumbs-title"><strong>{escape(t["selected"])}</strong><span class="line"></span><em>{escape(t["selected_em"])}</em></div>
    <div class="thumbs">{thumbs}</div>
    <div class="intro-box">
      <div class="eyebrow caps latin">KING PUZZLE</div>
      <h3>{escape(t["intro_title"])}</h3>
      <p class="intro">{escape(t["intro"])}</p>
    </div>
  </div>
  {foot(t, folio)}
</section>'''


def page_features(t, folio):
    cards = []
    for i, (ic, title, caps, desc) in enumerate(t["features"], 1):
        caps_html = f'<div class="caps latin">{escape(caps)}</div>' if caps else ""
        cards.append(f'''
      <article class="card">
        <div class="top"><span class="icon">{icon(ic)}</span><span class="no latin">{i:02d}</span></div>
        <h3>{escape(title)}</h3>
        {caps_html}
        <div class="rule-short"></div>
        <p>{escape(desc)}</p>
      </article>''')
    return f'''
<section class="page features">
  {head(t["features_head"], "KING · PUZZLE COLLECTION")}
  <div class="body">
    <div class="head">
      <div class="eyebrow caps latin">{escape(t["features_eyebrow"])}</div>
      <h2>{escape(t["features_h2"])}</h2>
      <p>{escape(t["features_p"])}</p>
      {ORN}
    </div>
    <div class="cards">{"".join(cards)}
    </div>
  </div>
  {foot(t, folio)}
</section>'''


def stats(t, c, items):
    cells = [(t["stat_designs"], f'{num(t, len(items))}', False),
             (t["stat_codes"], code_range(items), True)]
    fcodes = sorted({p["factory_code"] for p in items if p["factory_code"]})
    if fcodes:
        cells.append((t["stat_factory"], " · ".join(fcodes), True))
    return "".join(
        f'<div><span class="k">{escape(k)}</span><span class="v{" latin" if latin else ""}">{escape(v)}</span></div>'
        for k, v, latin in cells)


def page_divider(t, folio, idx, c, items):
    ct = c[t["lang"]]
    hero = next((p for p in items if p["source"] == c["hero"]), items[0])
    big = (f'<div class="dnum latin">{escape(c["num"])}</div>' if c["num"] else "")
    return f'''
<section class="page divider">
  {FRAME}
  <div class="divider-inner">
    <div class="eyebrow caps latin">Collection {idx:02d}</div>
    {big}
    <div class="dcaps caps latin">{escape(c["caps"])}</div>
    {ORN}
    <h2>{escape(ct["title"])}</h2>
    <div class="dseries latin">{escape(ct["series"])}</div>
    <p class="ddesc">{escape(ct["desc"])}</p>
    <figure class="dfig">{panel(hero)}</figure>
    <div class="dstats">{stats(t, c, items)}</div>
  </div>
  <div class="dfolio latin">{folio:02d}</div>
</section>'''


def product_row(t, p, flip):
    return f'''
      <article class="product{" flip" if flip else ""}">
        {panel(p)}
        <div class="info">
          <div class="code caps latin">{escape(p["code"])}</div>
          {names(t, p)}
          {tags(p)}
          <div class="rule-short"></div>
          {meta(t, p)}
        </div>
      </article>'''


def product_card(t, p):
    return f'''
      <article class="pcard">
        {panel(p)}
        <div class="info">
          <div class="code caps latin">{escape(p["code"])}</div>
          {names(t, p)}
          {meta(t, p)}
        </div>
      </article>'''


def page_products(t, folio, c, items):
    ct = c[t["lang"]]
    caps = f'KING · {c["caps"]}' if c["key"] != "2in1" else "KING · 2 FANTASTIC PUZZLES"
    if c["layout"] == "grid":
        inner = f'<div class="pgrid">{"".join(product_card(t, p) for p in items)}\n  </div>'
    else:
        rows = "".join(product_row(t, p, i % 2 == 1) for i, p in enumerate(items))
        inner = f'<div class="products n{len(items)}">{rows}\n  </div>'
    return f'''
<section class="page designs">
  {head(ct["title"], caps)}
  <div class="body">{inner}</div>
  {foot(t, folio)}
</section>'''


def page_feature(t, folio, idx, c, items):
    """Accessories: divider and product on one page."""
    ct = c[t["lang"]]
    blocks = "".join(f'''
    <article class="feature-item">
      {panel(p)}
      <div class="info">
        <div class="code caps latin">{escape(p["code"])}</div>
        {names(t, p, "h3")}
        <div class="rule-short"></div>
        {meta(t, p)}
      </div>
    </article>''' for p in items)
    return f'''
<section class="page divider accessory">
  {FRAME}
  <div class="divider-inner">
    <div class="eyebrow caps latin">Collection {idx:02d}</div>
    <div class="dcaps caps latin">{escape(c["caps"])}</div>
    {ORN}
    <h2>{escape(ct["title"])}</h2>
    <p class="ddesc">{escape(ct["desc"])}</p>
    {blocks}
  </div>
  <div class="dfolio latin">{folio:02d}</div>
</section>'''


def page_index(t, folio):
    fa = t["lang"] == "fa"
    groups = []
    for c in COLLECTIONS:
        items = items_of(c["key"])
        if not items:
            continue
        ct = c[t["lang"]]
        rows = []
        for p in items:
            nm = p["name_fa"] if fa else p["name_en"]
            var = p["variant_fa"] if fa else p["variant_en"]
            label = nm + (f" — {var}" if var else "")
            rows.append(f'<li><span class="cd latin">{escape(p["code"])}</span>'
                        f'<span class="nm">{escape(label)}</span></li>')
        groups.append(f'<div class="igroup"><div class="ihead"><strong>{escape(ct["title"])}</strong>'
                      f'<span class="caps latin">{escape(c["caps"])}</span></div><ul>{"".join(rows)}</ul></div>')
    return f'''
<section class="page index">
  {head(t["index_head"], t["index_caps"])}
  <div class="body">
    <div class="icols">{"".join(groups)}</div>
    <p class="inote">{escape(t["index_note"])}</p>
  </div>
  {foot(t, folio)}
</section>'''


def page_closing(t):
    fa = t["lang"] == "fa"
    items = []
    for ic, lbl, val, kind in t["contact"]:
        cls = "item wide" if kind == "wide" else "item"
        vcls = "val latin" if kind == "latin" else "val"
        items.append(f'<div class="{cls}"><span class="ic">{icon(ic)}</span>'
                     f'<div><div class="lbl">{escape(lbl)}</div><div class="{vcls}">{val}</div></div></div>')
    slogan_fa = f'<p class="slogan-fa">{escape(FA["slogan_fa"])}</p>' if fa else ""
    return f'''
<section class="page closing">
  {FRAME}
  <div class="closing-inner">
    <img class="logo" src="assets/img/king-logo.png" alt="KING">
    <div class="brand latin">KING</div>
    <div class="pieces caps latin">Puzzle Collection</div>
    <div class="pieces-fa">{escape(t["closing_line"])}</div>
    <div class="ornament solid end"><i></i><b></b><i></i></div>
    {slogan_fa}
    <p class="slogan-en">Quality Never Goes Out of Style</p>
    <div class="contact">
      <span class="c tl"></span><span class="c tr"></span><span class="c bl"></span><span class="c br"></span>
      <div class="head"><div class="row"><i></i><strong>{escape(t["contact_head"])}</strong><i></i></div><div class="caps latin">{escape(t["contact_caps"])}</div></div>
      <div class="grid">{"".join(items)}</div>
    </div>
  </div>
</section>'''


def paginate(items, layout):
    """Split a collection into pages: 3 rows per page (never a lone row), 4 cards per grid page."""
    if layout == "grid":
        return [items[i:i + 4] for i in range(0, len(items), 4)]
    n = len(items)
    if n <= 3:
        return [items]
    sizes = [3] * (n // 3)
    rest = n % 3
    if rest == 1:            # 3,1 -> 2,2
        sizes[-1] = 2
        sizes.append(2)
    elif rest == 2:
        sizes.append(2)
    out, i = [], 0
    for s in sizes:
        out.append(items[i:i + s])
        i += s
    return out


def plan():
    """Return [(kind, payload)] in page order plus each collection's first page number."""
    pages = [("cover", None), ("about", None), ("features", None)]
    starts = {}
    idx = 0
    for c in COLLECTIONS:
        items = items_of(c["key"])
        if not items:
            continue
        idx += 1
        starts[c["key"]] = len(pages) + 1
        if c["layout"] == "feature":
            pages.append(("feature", (idx, c, items)))
            continue
        pages.append(("divider", (idx, c, items)))
        for chunk in paginate(items, c["layout"]):
            pages.append(("products", (c, chunk)))
    starts["index"] = len(pages) + 1
    pages.append(("index", None))
    pages.append(("closing", None))
    return pages, starts


def build(t):
    pages, starts = plan()
    hero = next(p for p in PRODUCTS if p["source"] == COVER_SOURCE)
    html = []
    for folio, (kind, data) in enumerate(pages, 1):
        if kind == "cover":
            html.append(page_cover(t, hero))
        elif kind == "about":
            html.append(page_about(t, folio, starts))
        elif kind == "features":
            html.append(page_features(t, folio))
        elif kind == "divider":
            html.append(page_divider(t, folio, *data))
        elif kind == "products":
            html.append(page_products(t, folio, *data))
        elif kind == "feature":
            html.append(page_feature(t, folio, *data))
        elif kind == "index":
            html.append(page_index(t, folio))
        elif kind == "closing":
            html.append(page_closing(t))
    return f'''<!doctype html>
<html lang="{t["lang"]}" dir="{t["dir"]}">
<head>
<meta charset="utf-8">
<title>{escape(t["doc_title"])}</title>
<link rel="stylesheet" href="assets/catalog.css">
</head>
<body>{"".join(html)}
</body>
</html>
'''


if __name__ == "__main__":
    for t, name in ((FA, "catalog-fa.html"), (EN, "catalog-en.html")):
        (ROOT / name).write_text(build(t), encoding="utf-8")
        print("wrote", name)
