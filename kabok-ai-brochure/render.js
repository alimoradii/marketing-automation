// Renders brochure.html to Kabok-AI-Brochure.pdf using the IRANSans files in fonts/iransans/.
// Usage: node render.js            (fails if no IRANSans files are present)
//        node render.js --fallback (renders with Vazirmatn when IRANSans is missing)
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const FONT_DIR = path.join(__dirname, 'fonts', 'iransans');
const FORMATS = { '.woff2': 'woff2', '.woff': 'woff', '.ttf': 'truetype', '.otf': 'opentype' };
const EXT_RANK = ['.woff2', '.woff', '.ttf', '.otf'];

function weightOf(name) {
  const n = name.toLowerCase();
  if (/ultra.?light|extra.?light|thin/.test(n)) return 200;
  if (/light/.test(n)) return 300;
  if (/medium/.test(n)) return 500;
  if (/demi.?bold|semi.?bold/.test(n)) return 600;
  if (/ultra.?bold|extra.?bold/.test(n)) return 800;
  if (/black|heavy/.test(n)) return 900;
  if (/bold/.test(n)) return 700;
  return 400;
}

// One file per weight: prefer FaNum (Persian digits), then the best web format.
function buildFontCss() {
  const files = fs.existsSync(FONT_DIR)
    ? fs.readdirSync(FONT_DIR).filter(f => FORMATS[path.extname(f).toLowerCase()])
    : [];
  const byWeight = {};
  for (const f of files) {
    const w = weightOf(f);
    const score = (/fanum/i.test(f) ? 0 : 10) + EXT_RANK.indexOf(path.extname(f).toLowerCase());
    if (!byWeight[w] || score < byWeight[w].score) byWeight[w] = { f, score };
  }
  const css = Object.entries(byWeight).map(([w, { f }]) =>
    `@font-face{font-family:"IRANSans";font-weight:${w};font-style:normal;` +
    `src:url("iransans/${encodeURIComponent(f)}") format("${FORMATS[path.extname(f).toLowerCase()]}");}`
  ).join('\n');
  fs.writeFileSync(path.join(__dirname, 'fonts', 'iransans.css'), css + '\n');
  return Object.keys(byWeight).map(Number).sort();
}

(async () => {
  const weights = buildFontCss();
  const fallback = process.argv.includes('--fallback');
  if (!weights.length && !fallback) {
    console.error(`No IRANSans files found in ${FONT_DIR}. Add your licensed .woff2/.woff/.ttf files there, or pass --fallback.`);
    process.exit(1);
  }
  console.log(weights.length ? `IRANSans weights: ${weights.join(', ')}` : 'IRANSans missing; rendering with Vazirmatn fallback');

  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + __dirname + '/brochure.html', { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  // Fail instead of silently falling back to a system font.
  const family = weights.length ? 'IRANSans' : 'Vazirmatn';
  await p.evaluate(fam => Promise.all([...document.fonts].filter(f => f.family.replace(/"/g, '') === fam).map(f => f.load().catch(() => {}))), family);
  const loaded = await p.evaluate(fam => [...document.fonts].filter(f => f.family.replace(/"/g, '') === fam && f.status === 'loaded').map(f => f.weight), family);
  if (!loaded.length) { console.error(`${family} did not load in the page; check the font paths.`); await b.close(); process.exit(1); }
  console.log(`${family} loaded: ${[...new Set(loaded)].join(', ')}`);
  await p.pdf({ path: __dirname + '/Kabok-AI-Brochure.pdf', format: 'A4', printBackground: true, preferCSSPageSize: true });
  await b.close();
})();
