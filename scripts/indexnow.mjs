// Notifies IndexNow (Bing, Yandex, Naver, Seznam, ...) about pages changed in the last push.
//
// Runs in GitHub Actions after the site is deployed. Only URLs that appear in the live
// sitemap are submitted, so drafts, renamed folders or deleted pages are never sent.
//
// Env:
//   BEFORE_SHA, AFTER_SHA  commit range of the push (set by the workflow)
//   FULL=1                 submit every URL in the sitemap (first run / manual resubmit)
//   DRY_RUN=1              print the payload without sending it
//   SITEMAP_FILE           read the sitemap from a local file instead of the live site (testing)
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const SITE = 'https://optexpert.org';
const HOST = new URL(SITE).host;
const ENDPOINT = 'https://api.indexnow.org/indexnow';
const CONTENT_COLLECTIONS = ['notes', 'projects', 'courses', 'books', 'softwares'];

// Pages whose content lists other entries; resubmitted whenever any entry changes.
const LISTING_PAGES = ['/', '/ortools/', '/notes/', '/projects/', '/courses/'];

function findKey() {
  const file = fs.readdirSync('public').find((f) => /^[0-9a-f]{32}\.txt$/.test(f));
  if (!file) throw new Error('IndexNow key file (public/<32-hex>.txt) not found.');
  const key = fs.readFileSync(path.join('public', file), 'utf-8').trim();
  if (`${key}.txt` !== file) throw new Error(`Key file ${file} does not contain its own key.`);
  return key;
}

async function loadSitemapUrls() {
  const read = async (loc) => {
    if (process.env.SITEMAP_FILE) {
      const dir = path.dirname(process.env.SITEMAP_FILE);
      const local = loc.startsWith('http') ? path.join(dir, path.basename(new URL(loc).pathname)) : loc;
      return fs.readFileSync(local, 'utf-8');
    }
    const res = await fetch(loc);
    if (!res.ok) throw new Error(`Cannot fetch ${loc}: HTTP ${res.status}`);
    return res.text();
  };
  const index = await read(process.env.SITEMAP_FILE || `${SITE}/sitemap-index.xml`);
  const childMaps = [...index.matchAll(/<loc>([^<]+\.xml)<\/loc>/g)].map((m) => m[1]);
  const xmls = childMaps.length ? await Promise.all(childMaps.map(read)) : [index];
  return new Set(xmls.flatMap((x) => [...x.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1])).filter((u) => !u.endsWith('.xml')));
}

function changedFiles() {
  const before = process.env.BEFORE_SHA || '';
  const after = process.env.AFTER_SHA || 'HEAD';
  const range = !before || /^0+$/.test(before) ? `${after}~1 ${after}` : `${before} ${after}`;
  try {
    return execSync(`git diff --name-only ${range}`, { encoding: 'utf-8' }).split('\n').filter(Boolean);
  } catch {
    console.log(`Could not diff ${range}; nothing to submit.`);
    return [];
  }
}

function urlsForFiles(files, live) {
  const urls = new Set();
  let contentChanged = false;
  for (const file of files) {
    const content = file.match(/^src\/content\/([^/]+)\/([^/]+)\//);
    if (content && CONTENT_COLLECTIONS.includes(content[1])) {
      const url = `${SITE}/${content[1]}/${content[2].toLowerCase()}/`;
      urls.add(url);
      // Listing pages only change when a published entry changes (not for drafts).
      if (live.has(url)) contentChanged = true;
      continue;
    }
    // Static pages: src/pages/about.astro -> /about/, src/pages/ortools/index.astro -> /ortools/
    const page = file.match(/^src\/pages\/(.+)\.astro$/);
    if (page && !page[1].includes('[')) {
      const route = page[1].replace(/(^|\/)index$/, '');
      urls.add(`${SITE}/${route ? `${route}/` : ''}`);
    }
  }
  if (contentChanged) LISTING_PAGES.forEach((p) => urls.add(`${SITE}${p}`));
  return urls;
}

async function main() {
  const key = findKey();
  const live = await loadSitemapUrls();

  let candidates;
  if (process.env.FULL === '1') {
    candidates = live;
    console.log('FULL=1: submitting every URL in the sitemap.');
  } else {
    const files = changedFiles();
    console.log(`Changed files: ${files.length}`);
    candidates = urlsForFiles(files, live);
  }

  const urlList = [...candidates].filter((u) => live.has(u)).sort();
  const skipped = [...candidates].filter((u) => !live.has(u));
  if (skipped.length) console.log(`Skipped (not in sitemap): ${skipped.join(', ')}`);
  if (!urlList.length) {
    console.log('No published pages changed; nothing to submit.');
    return;
  }

  const payload = { host: HOST, key, keyLocation: `${SITE}/${key}.txt`, urlList: urlList.slice(0, 10000) };
  console.log(`Submitting ${payload.urlList.length} URL(s):\n  ${payload.urlList.join('\n  ')}`);
  if (process.env.DRY_RUN === '1') {
    console.log('DRY_RUN=1: not sending.');
    return;
  }

  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(payload),
  });
  const meaning = {
    200: 'OK, submitted',
    202: 'Accepted; key validation pending',
    400: 'Bad request',
    403: 'Key not valid (key file not reachable?)',
    422: 'URLs do not belong to the host or key mismatch',
    429: 'Too many requests',
  };
  console.log(`IndexNow response: ${res.status} ${meaning[res.status] ?? ''}`);
  if (res.status >= 400) process.exitCode = 1;
}

main().catch((err) => {
  console.error(err.message);
  process.exitCode = 1;
});
