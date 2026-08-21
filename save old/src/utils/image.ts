/**
 * Convert an Astro ImageMetadata value or a public/URL string to a usable URL.
 * This helper is intentionally dependency-free so it can be reused by SEO,
 * search, JSON-LD and normal page components.
 */
export function imgSrc(field: unknown): string | undefined {
  if (!field) return undefined;

  let src: string | undefined;

  if (typeof field === 'string') {
    src = field;
  } else if (typeof field === 'object' && field !== null && 'src' in field) {
    const value = (field as { src?: unknown }).src;
    if (typeof value === 'string') src = value;
  }

  if (!src) return undefined;
  if (/^(?:https?:)?\/\//i.test(src) || src.startsWith('/')) return src;

  return `/${src.replace(/^\.\//, '')}`;
}
