/**
 * Persian <-> English page pairs.
 *
 * The English site is a consulting-focused companion to the Persian learning site,
 * not a full translation, so only these pages have counterparts. They drive:
 *  - the language switch button (falls back to the other site's home page), and
 *  - reciprocal hreflang links, which Google requires to pair the two versions.
 */
export const LANG_PAIRS: Array<{ fa: string; en: string }> = [
  { fa: '/', en: '/en/' },
  { fa: '/consultation/', en: '/en/services/' },
  { fa: '/projects/', en: '/en/projects/' },
  { fa: '/instructors/dr-soroudi/', en: '/en/about/' },
  { fa: '/contact/', en: '/en/contact/' },
];

const withSlash = (p: string) => (p.endsWith('/') ? p : `${p}/`);

/** Counterpart of a path in the other language, or undefined if it has none. */
export function counterpart(pathname: string): { lang: 'fa' | 'en'; path: string } | undefined {
  const p = withSlash(decodeURI(pathname));
  for (const pair of LANG_PAIRS) {
    if (pair.fa === p) return { lang: 'en', path: pair.en };
    if (pair.en === p) return { lang: 'fa', path: pair.fa };
  }
  return undefined;
}

/** Where the language button should go from this page. */
export function switchTarget(pathname: string): string {
  const pair = counterpart(pathname);
  if (pair) return pair.path;
  return decodeURI(pathname).startsWith('/en/') ? '/' : '/en/';
}
