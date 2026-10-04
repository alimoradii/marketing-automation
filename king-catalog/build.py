#!/usr/bin/env python3
"""Generate the Persian and English KING 500-piece catalogue pages (HTML).

Run `python3 build.py` and then `node render.mjs` to produce the PDFs.
Product photos in assets/img are used exactly as supplied (crop only).
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZW = "‌"  # zero-width non-joiner for Persian compound words

# ---------------------------------------------------------------- data
PRODUCTS = [
    # code, Persian name, English name, artist / origin
    ("001", f"شطرنج{ZW}بازان", "The Chess Players", "After Moritz Retzsch"),
    ("002", "شام آخر", "The Last Supper", "After Leonardo da Vinci"),
    ("003", "بوسه", "The Kiss", "Gustav Klimt"),
    ("004", "موج بزرگ کاناگاوا", "The Great Wave", "Katsushika Hokusai"),
    ("005", "شب پرستاره", "The Starry Night", "Vincent van Gogh"),
    ("006", f"تاج{ZW}گذاری ناپلئون", "The Coronation of Napoleon", "Jacques-Louis David"),
    ("007", "گاراژ کلاسیک", "Classic Garage", "Vintage Illustration"),
    ("008", "نقشهٔ جهان کهن", "Antique World Map", "Henricus Hondius"),
    ("009", "مرگ سقراط", "The Death of Socrates", "Jacques-Louis David"),
]
SELECTED = ["003", "004", "008"]  # thumbnails on the About page
COVER_IMG = "assets/img/king-500-cover.jpg"

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


# ---------------------------------------------------------------- copy
FA = {
    "lang": "fa", "dir": "rtl",
    "doc_title": "کاتالوگ پازل ۵۰۰ قطعه کینگ",
    "foot_name": "پازل ۵۰۰ قطعه کینگ",
    "cover_title": "پازل ۵۰۰ قطعه کینگ",
    "slogan_fa": f"کیفیت هرگز از مد نمی{ZW}افتد",
    "about_head": "معرفی کینگ",
    "about_eyebrow": "About KING",
    "about_h2": "کینگ؛ اصالت در هر قطعه",
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
        (f"طرح{ZW}های این کاتالوگ", f"{fa_num(len(PRODUCTS))} طرح", False),
        ("کد محصولات", f"KING-500-001 — {PRODUCTS[-1][0]}", True),
    ],
    "badge_sub": "قطعه",
    "selected": f"گزیده{ZW}ای از طرح{ZW}ها",
    "selected_em": "Selected Designs",
    "features_head": f"ویژگی{ZW}های محصول",
    "features_eyebrow": "PRODUCT FEATURES",
    "features_h2": f"ویژگی{ZW}های محصول",
    "features_p": f"چهار ویژگی که کیفیت پازل{ZW}های ۵۰۰ قطعه کینگ را تعریف می{ZW}کنند.",
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
    "designs_head": f"مجموعه طرح{ZW}ها",
    "pcs_small": "قطعه",
    "brand_small": "برند",
    "closing_pieces": "پازل ۵۰۰ قطعه",
    "list_head": f"اسامی طرح{ZW}ها",
    "list_caps": "THE DESIGNS",
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
    "doc_title": "KING 500 Pieces Puzzle Catalogue",
    "foot_name": "KING 500 Pieces Puzzle",
    "about_head": "About KING",
    "about_eyebrow": "The Brand",
    "about_h2": "KING — Authenticity in Every Piece",
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
        ("Designs in this catalogue", f"{len(PRODUCTS)} DESIGNS", True),
        ("Product codes", f"KING-500-001 — {PRODUCTS[-1][0]}", True),
    ],
    "badge_sub": "in every puzzle",
    "selected": "Selected Designs",
    "selected_em": "from the collection",
    "features_head": "Product Features",
    "features_eyebrow": "WHY KING",
    "features_h2": "Product Features",
    "features_p": "Four qualities that define every KING 500-piece puzzle.",
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
    "designs_head": "The Designs",
    "pcs_small": "per puzzle",
    "brand_small": "Brand",
    "closing_pieces": "500 Pieces Puzzle Collection",
    "list_head": "The Designs",
    "list_caps": "COLLECTION INDEX",
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


def img(code):
    return f"assets/img/king-500-{code}.jpg"


def head(t, title, caps):
    return (f'<header class="running-head"><span class="title">{escape(title)}</span>'
            f'<span class="caps latin">{escape(caps)}</span></header>')


def foot(t, folio):
    return (f'<footer class="running-foot"><span class="name">{escape(t["foot_name"])}</span>'
            f'<span class="folio">{folio:02d}</span>'
            f'<span class="caps latin">KING COLLECTION</span></footer>')


def page_cover(t):
    fa = t["lang"] == "fa"
    title = f'<div class="title-fa">{escape(t["cover_title"])}</div>' if fa else ""
    slogan_fa = f'<p class="slogan-fa">{escape(FA["slogan_fa"])}</p>' if fa else ""
    return f'''
<section class="page cover">
  {FRAME}
  <div class="cover-inner">
    <img class="logo" src="assets/img/king-logo.png" alt="KING">
    <h1 class="brand latin">KING</h1>
    <div class="collection caps latin">500 Pieces Puzzle Collection</div>
    {ORN}
    {title}
    <figure class="figure"><div class="panel"><img src="{COVER_IMG}" alt="KING 500 pieces puzzle box"></div></figure>
    <div class="after ornament solid"><i></i><b></b><i></i></div>
    {slogan_fa}
    <p class="slogan-en">Quality Never Goes Out of Style</p>
  </div>
</section>'''


def page_about(t, folio):
    fa = t["lang"] == "fa"
    specs = "".join(
        f'<div><dt>{escape(k)}</dt><dd class="{"latin" if latin else ""}">{escape(v)}</dd></div>'
        for k, v, latin in t["specs"])
    by_code = {p[0]: p for p in PRODUCTS}
    thumbs = "".join(
        f'<figure><div class="panel"><img src="{img(c)}" alt=""></div>'
        f'<figcaption>{escape(by_code[c][1] if fa else by_code[c][2])}</figcaption></figure>'
        for c in SELECTED)
    return f'''
<section class="page about">
  {head(t, t["about_head"], "KING · 500 PIECES")}
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
  {head(t, t["features_head"], "KING · 500 PIECES")}
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


def product_block(t, p, flip):
    fa = t["lang"] == "fa"
    code, name_fa, name_en, artist = p
    if fa:
        names = (f'<h3>{escape(name_fa)}</h3>'
                 f'<div class="en-name latin">{escape(name_en)}</div>'
                 f'<div class="artist latin">{escape(artist)}</div>')
    else:
        names = (f'<h3>{escape(name_en)}</h3>'
                 f'<div class="artist">{escape(artist)}</div>')
    return f'''
      <article class="product{" flip" if flip else ""}">
        <div class="panel"><img src="{img(code)}" alt="{escape(name_en)}"></div>
        <div class="info">
          <div class="code caps latin">KING-500-{code}</div>
          {names}
          <div class="rule-short"></div>
          <div class="meta">
            <div class="pcs"><span class="n latin">500</span><span class="l"><span class="caps latin">Pieces</span><small>{escape(t["pcs_small"])}</small></span></div>
            <div class="brand-mini"><small>{escape(t["brand_small"])}</small><b class="latin">KING</b></div>
          </div>
        </div>
      </article>'''


def page_products(t, folio, items):
    blocks = "".join(product_block(t, p, i % 2 == 1) for i, p in enumerate(items))
    caps = f"Designs {items[0][0]} — {items[-1][0]}"
    return f'''
<section class="page designs">
  {head(t, t["designs_head"], caps)}
  <div class="body"><div class="products">{blocks}
  </div></div>
  {foot(t, folio)}
</section>'''


def page_closing(t):
    fa = t["lang"] == "fa"
    rows = []
    for code, name_fa, name_en, artist in PRODUCTS:
        nm, alt = (name_fa, name_en) if fa else (name_en, artist)
        rows.append(f'<li><span class="nm">{escape(nm)}</span><span class="alt">{escape(alt)}</span>'
                    f'<span class="dots"></span><span class="cd">KING-500-{code}</span></li>')
    items = []
    for ic, lbl, val, kind in t["contact"]:
        cls = "item wide" if kind == "wide" else "item"
        vcls = "val latin" if kind == "latin" else "val"
        items.append(f'<div class="{cls}"><span class="ic">{icon(ic)}</span>'
                     f'<div><div class="lbl">{escape(lbl)}</div><div class="{vcls}">{val}</div></div></div>')
    pieces_sub = f'<div class="pieces-fa">{escape(t["closing_pieces"])}</div>'
    slogan_fa = f'<p class="slogan-fa">{escape(FA["slogan_fa"])}</p>' if fa else ""
    return f'''
<section class="page closing">
  {FRAME}
  <div class="closing-inner">
    <img class="logo" src="assets/img/king-logo.png" alt="KING">
    <div class="brand latin">KING</div>
    <div class="pieces caps latin">500 Pieces</div>
    {pieces_sub}
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
    pages = [page_cover(t), page_about(t, 2), page_features(t, 3)]
    folio = 4
    for i in range(0, len(PRODUCTS), 3):
        pages.append(page_products(t, folio, PRODUCTS[i:i + 3]))
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
    for t, name in ((FA, "catalog-fa.html"), (EN, "catalog-en.html")):
        (ROOT / name).write_text(build(t), encoding="utf-8")
        print("wrote", name)
