/**
 * Helpers shared by all content-driven pages.
 * Keep routing and publication rules in one place.
 */

export interface ContentEntryLike {
  id: string;
  slug?: string;
  data: {
    draft?: boolean;
  };
}

/** Return true only for content that is intended to be public. */
export function isPublished(entry: ContentEntryLike): boolean {
  return entry.data.draft !== true;
}

/**
 * Astro content entries expose `slug`. The id fallback keeps this helper
 * resilient if an entry is ever supplied by a custom loader.
 */
export function entrySlug(entry: ContentEntryLike): string {
  if (entry.slug) return entry.slug;

  return entry.id
    .replace(/\.(?:md|mdx)$/i, '')
    .split('/')
    .filter(Boolean)
    .pop() ?? '';
}

/** Normalize manually-entered related slugs for tolerant matching. */
export function normalizeSlug(value: string): string {
  return value.trim().replace(/^\/+|\/+$/g, '').toLowerCase();
}
