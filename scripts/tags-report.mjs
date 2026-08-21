#!/usr/bin/env node
// Read-only, informational report about tags used across src/content.
// Never exits non-zero and never blocks dev/build — purely a heads-up.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(fileURLToPath(new URL('.', import.meta.url)), '..');
const MIN_HUB_USES = 3;

function normalizeTag(value) {
  return String(value ?? '')
    .normalize('NFKC')
    .trim()
    .toLocaleLowerCase('fa-IR')
    .replace(/[\u200c\u200d]+/g, '')
    .replace(/\s+/g, ' ');
}

function slugifyTag(value) {
  const slug = String(value ?? '')
    .normalize('NFKC')
    .trim()
    .replace(/[\u200c\u200d]+/g, '')
    .toLocaleLowerCase('fa-IR')
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
  return slug || 'tag';
}

function loadAliasMap() {
  const src = fs.readFileSync(path.join(ROOT, 'src/data/tag-aliases.ts'), 'utf8');
  const map = new Map();
  const entryRe = /"([^"]+)":\s*"([^"]+)"/g;
  let m;
  while ((m = entryRe.exec(src))) map.set(normalizeTag(m[1]), m[2]);
  return map;
}

function resolveCanonicalTag(value, aliasMap) {
  const trimmed = String(value ?? '').trim();
  if (!trimmed) return trimmed;
  return aliasMap.get(normalizeTag(trimmed)) ?? trimmed;
}

function findMarkdownFiles(dir) {
  let out = [];
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) out = out.concat(findMarkdownFiles(p));
    else if (entry.name.endsWith('.md') || entry.name.endsWith('.mdx')) out.push(p);
  }
  return out;
}

const aliasMap = loadAliasMap();
const files = findMarkdownFiles(path.join(ROOT, 'src/content'));

// slug -> { name, files: Set }
const tagUsage = new Map();

for (const file of files) {
  const rel = path.relative(ROOT, file);
  const content = fs.readFileSync(file, 'utf8');
  const fm = content.match(/^---\n([\s\S]*?)\n---/);
  if (!fm) continue;
  const tagsLine = fm[1].match(/^tags:\s*(\[[^\]]*\])/m);
  if (!tagsLine) continue;
  let arr;
  try {
    arr = JSON.parse(tagsLine[1].replace(/'/g, '"'));
  } catch {
    continue;
  }
  for (const raw of arr) {
    const value = String(raw ?? '').trim();
    if (!value) continue;
    const canonical = resolveCanonicalTag(value, aliasMap);
    const slug = slugifyTag(canonical);
    if (!tagUsage.has(slug)) tagUsage.set(slug, { name: canonical, files: new Set() });
    tagUsage.get(slug).files.add(rel);
  }
}

const belowThreshold = [...tagUsage.entries()].filter(([, info]) => info.files.size < MIN_HUB_USES);

console.log('\n📋 گزارش تگ‌ها (فقط اطلاع‌رسانی — هیچ‌وقت build را متوقف نمی‌کند)\n');
console.log(`✅ ${tagUsage.size} تگ یکتا در محتوای سایت پیدا شد؛ همه‌شان به‌طور خودکار کار می‌کنند.`);

if (belowThreshold.length > 0) {
  console.log(`\nℹ️  ${belowThreshold.length} تگ هنوز به آستانه‌ی ${MIN_HUB_USES} استفاده نرسیده‌اند و صفحه‌ی اختصاصی (/tags/...) نمی‌گیرند (فقط از طریق جستجو قابل مشاهده‌اند):`);
  for (const [slug, info] of belowThreshold) {
    console.log(`   - "${info.name}"  (/tags/${slug}/ — ${info.files.size} مورد)`);
  }
}
console.log('');
