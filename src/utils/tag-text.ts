import { tagAliases } from '../data/tag-aliases';

/**
 * Normalizes a tag string for comparison purposes only (never shown to users):
 * unifies unicode form, trims, lower-cases (fa-aware), strips zero-width
 * characters, and collapses whitespace. Two tags that normalize to the same
 * string are treated as the same tag.
 */
export function normalizeTag(value: string): string {
  return String(value ?? '')
    .normalize('NFKC')
    .trim()
    .toLocaleLowerCase('fa-IR')
    .replace(/[\u200c\u200d]+/g, '')
    .replace(/\s+/g, ' ');
}

const aliasMap = new Map<string, string>(
  Object.entries(tagAliases).map(([variant, canonical]) => [normalizeTag(variant), canonical]),
);

/**
 * Returns the canonical display text for a tag as written by an author.
 * - If the tag (or a case/spacing variant of it) is listed in
 *   src/data/tag-aliases.ts, the canonical form from that map is returned.
 * - Otherwise the tag is returned exactly as written — every tag works
 *   out of the box, no registration required.
 */
export function resolveCanonicalTag(value: string): string {
  const trimmed = String(value ?? '').trim();
  if (!trimmed) return trimmed;
  return aliasMap.get(normalizeTag(trimmed)) ?? trimmed;
}

/**
 * Turns tag display text into a URL- and filesystem-safe slug, used for
 * /tags/<slug>/ pages. Persian/Arabic letters are kept as-is (a normal,
 * SEO-friendly pattern for Persian-language sites); anything else that
 * isn't a letter or digit becomes a hyphen.
 */
export function slugifyTag(value: string): string {
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
