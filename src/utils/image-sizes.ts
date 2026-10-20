// Responsive presets for <Image>. Each preset tells the browser how wide the image is
// actually displayed, so it downloads a small file for thumbnails instead of the
// original (often 1600px+) image. SVGs are vector and are left untouched.

type Src = unknown;

export const CARD = {
  widths: [400, 800, 1200],
  sizes: '(min-width: 1024px) 380px, (min-width: 640px) 46vw, 92vw',
};
export const HERO = {
  widths: [640, 960, 1280, 1600],
  sizes: '(min-width: 1024px) 860px, 94vw',
};
export const PORTRAIT = {
  widths: [200, 400],
  sizes: '160px',
};
export const COVER = {
  widths: [400, 800],
  sizes: '(min-width: 640px) 400px, 80vw',
};

function isSvg(src: Src): boolean {
  if (typeof src === 'string') return src.toLowerCase().split('?')[0].endsWith('.svg');
  return Boolean(src && typeof src === 'object' && (src as { format?: string }).format === 'svg');
}

export function sized(src: Src, preset: { widths: number[]; sizes: string }) {
  return isSvg(src) ? {} : preset;
}
