// src/utils/image.ts
// این پروژه از دو شکل تصویر همزمان پشتیبانی می‌کند:
//   ۱. رشته‌ی مسیر ساده (فایل داخل public/ یا یک URL کامل خارجی) — شکل قدیمی
//   ۲. مسیر نسبی محلی کنار فایل md (مثل "./photo.jpg") — Astro این را در build
//      به یک آبجکت ImageMetadata تبدیل و بهینه می‌کند (سایزبندی، تبدیل فرمت، width/height خودکار)
//
// هر جا فقط یک URL متنی ساده لازم است (og:image، JSON-LD، ایندکس جستجوی سمت کلاینت)
// باید از imgSrc() استفاده شود تا هر دو حالت به یک رشته یکسان تبدیل شوند.
export function imgSrc(field: unknown): string | undefined {
  if (!field) return undefined;
  let src: string | undefined;
  if (typeof field === 'string') {
    src = field;
  } else if (typeof field === 'object' && field !== null && 'src' in field) {
    src = (field as { src: string }).src;
  }
  if (!src) return undefined;
  // اگر یک رشته‌ی خام بدون "/" یا "http" ابتدایی باشد (فراموش‌شدن اسلش)، اصلاح می‌شود.
  // آبجکت‌های تصویر محلی (خروجی خودکار Astro) همیشه src معتبر و کامل دارند، نیازی به این اصلاح ندارند.
  if (typeof field === 'string' && !src.startsWith('http') && !src.startsWith('/')) {
    return '/' + src;
  }
  return src;
}
