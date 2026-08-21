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
  } else if (
    (typeof field === 'object' || typeof field === 'function') &&
    field !== null &&
    'src' in (field as object)
  ) {
    // نکته: برای تصاویر SVG، Astro مقدار متادیتا را به‌صورت یک تابع
    // برمی‌گرداند (برای پشتیبانی از رندر inline SVG)، نه یک آبجکت ساده؛
    // این تابع همچنان ویژگی‌های src/width/height/format را دارد.
    const value = (field as { src?: unknown }).src;
    if (typeof value === 'string') src = value;
  }

  if (!src) return undefined;
  if (/^(?:https?:)?\/\//i.test(src) || src.startsWith('/')) return src;

  return `/${src.replace(/^\.\//, '')}`;
}
