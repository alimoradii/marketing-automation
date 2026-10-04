// Render catalog-fa.html / catalog-en.html to A4 PDFs with headless Chromium.
// Usage: NODE_PATH="$(npm root -g)" node render.cjs
const path = require("path");
const { chromium } = require("playwright");

const jobs = [
  ["catalog-fa.html", "KING-Puzzle-Catalog-FA.pdf"],
  ["catalog-en.html", "KING-Puzzle-Catalog-EN.pdf"],
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const [src, out] of jobs) {
    await page.goto("file://" + path.join(__dirname, src), { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    await page.pdf({
      path: path.join(__dirname, out),
      preferCSSPageSize: true,
      printBackground: true,
    });
    console.log("wrote", out);
  }
  await browser.close();
})();
