// Post-build CSS optimization (runs after `astro build`):
//  1. Font Awesome: write a subset stylesheet that keeps only the icons actually used
//     anywhere in the built site (HTML + JS), and point every page at it.
//  2. KaTeX: remove the math stylesheet from pages that contain no rendered math.
// Both decisions are made on the final output, so new icons or math are picked up automatically.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const FA_HREF = '/vendor/fontawesome/css/all.min.css';
const KATEX_LINK = /<link\b[^>]*href="\/katex\/dist\/katex\.min\.css"[^>]*>/g;

function walk(dir, exts, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, exts, out);
    else if (exts.some((e) => entry.name.endsWith(e))) out.push(full);
  }
  return out;
}

// Split CSS into top-level blocks, keeping @-rules (keyframes, font-face, media) intact.
function topLevelBlocks(css) {
  const blocks = [];
  let depth = 0, start = 0;
  for (let i = 0; i < css.length; i++) {
    if (css[i] === '{') depth++;
    else if (css[i] === '}') {
      depth--;
      if (depth === 0) { blocks.push(css.slice(start, i + 1)); start = i + 1; }
    }
  }
  return blocks;
}

const ICON_SELECTOR = /^\.fa-([a-z0-9-]+)(?:::?(?:before|after))?$/;

function subsetFontAwesome(css, used) {
  const header = css.slice(0, css.indexOf('*/') + 2);
  const kept = [];
  let dropped = 0;
  for (const block of topLevelBlocks(css.slice(header.length))) {
    const sel = block.slice(0, block.indexOf('{')).trim();
    if (sel.startsWith('@')) { kept.push(block); continue; }
    const selectors = sel.split(',').map((s) => s.trim());
    const icons = selectors.map((s) => s.match(ICON_SELECTOR));
    // Only rules made purely of icon selectors are candidates for removal.
    if (icons.every(Boolean) && !icons.some((m) => used.has(m[1]))) { dropped++; continue; }
    kept.push(block);
  }
  return { css: header + '\n' + kept.join(''), dropped };
}

export default function optimizeCss() {
  return {
    name: 'optimize-css',
    hooks: {
      'astro:build:done': ({ dir, logger }) => {
        const root = fileURLToPath(dir);
        const html = walk(root, ['.html']);
        const js = walk(root, ['.js']);

        // 1) Font Awesome subset
        const faPath = path.join(root, FA_HREF);
        if (fs.existsSync(faPath)) {
          const used = new Set();
          for (const file of [...html, ...js]) {
            for (const m of fs.readFileSync(file, 'utf-8').matchAll(/\bfa-([a-z0-9-]+)/g)) used.add(m[1]);
          }
          const { css, dropped } = subsetFontAwesome(fs.readFileSync(faPath, 'utf-8'), used);
          const hash = crypto.createHash('md5').update(css).digest('hex').slice(0, 8);
          const subsetHref = `/vendor/fontawesome/css/fa-subset.${hash}.css`;
          fs.writeFileSync(path.join(root, subsetHref), css);
          for (const file of html) {
            const page = fs.readFileSync(file, 'utf-8');
            if (page.includes(FA_HREF)) fs.writeFileSync(file, page.split(FA_HREF).join(subsetHref));
          }
          logger.info(`Font Awesome: kept ${(css.length / 1024).toFixed(1)} KB, dropped ${dropped} unused icon rules`);
        }

        // 2) KaTeX only where math is rendered: either already in the HTML, or rendered
        //    in the browser by a script on the page (followed through its imported chunks).
        const jsCache = new Map();
        const scriptUsesKatex = (src, seen = new Set()) => {
          if (seen.has(src)) return false;
          seen.add(src);
          if (jsCache.has(src)) return jsCache.get(src);
          const file = path.join(root, src);
          if (!fs.existsSync(file)) return false;
          const code = fs.readFileSync(file, 'utf-8');
          let uses = /katex/i.test(code);
          if (!uses) {
            for (const m of code.matchAll(/(?:from|import)\s*\(?\s*["']\.\/([^"']+\.js)["']/g)) {
              if (scriptUsesKatex(path.posix.join(path.posix.dirname(src), m[1]), seen)) { uses = true; break; }
            }
          }
          jsCache.set(src, uses);
          return uses;
        };
        let removed = 0;
        for (const file of html) {
          const page = fs.readFileSync(file, 'utf-8');
          const scripts = [...page.matchAll(/<script\b[^>]*\bsrc="(\/[^"]+\.js)"/g)].map((m) => m[1]);
          const needsKatex = page.includes('class="katex') || scripts.some((src) => scriptUsesKatex(src));
          if (!needsKatex && KATEX_LINK.test(page)) {
            KATEX_LINK.lastIndex = 0;
            fs.writeFileSync(file, page.replace(KATEX_LINK, ''));
            removed++;
          }
          KATEX_LINK.lastIndex = 0;
        }
        logger.info(`KaTeX stylesheet removed from ${removed} pages without math`);
      },
    },
  };
}
