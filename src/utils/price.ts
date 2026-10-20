// Parses the `price` frontmatter field. Accepted formats:
//   "8MT" / "8.5 MT"        -> million Toman (8MT = 8,000,000 Toman)
//   "800KT"                 -> thousand Toman
//   "8,000,000 تومان"       -> Toman
//   "80,000,000"            -> Rial (plain number, kept for backward compatibility)
//   "رایگان" / "free"       -> free
// Persian/Arabic digits are accepted too. Structured data needs an ISO currency,
// so the schema value is always in Rial (IRR); the page shows Toman.

export interface ParsedPrice {
  rial: number;
  toman: number;
  label: string; // Persian display text, e.g. «۸ میلیون تومان»
}

const toLatinDigits = (s: string) =>
  s.replace(/[۰-۹]/g, (d) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d))).replace(/[٠-٩]/g, (d) => String('٠١٢٣٤٥٦٧٨٩'.indexOf(d)));

const fa = (n: number) => n.toLocaleString('fa-IR', { maximumFractionDigits: 2 });

function label(toman: number): string {
  if (toman === 0) return 'رایگان';
  if (toman >= 1_000_000 && toman % 100_000 === 0) return `${fa(toman / 1_000_000)} میلیون تومان`;
  if (toman >= 1_000 && toman < 1_000_000 && toman % 1_000 === 0) return `${fa(toman / 1_000)} هزار تومان`;
  return `${fa(toman)} تومان`;
}

export function parsePrice(value?: string): ParsedPrice | undefined {
  if (!value) return undefined;
  const v = toLatinDigits(value).trim().replace(/[,٬،\s]/g, '');
  if (/^(رایگان|free)$/i.test(v)) return { rial: 0, toman: 0, label: 'رایگان' };

  let toman: number | undefined;
  let m: RegExpMatchArray | null;
  if ((m = v.match(/^(\d+(?:\.\d+)?)MT$/i))) toman = Number(m[1]) * 1_000_000;
  else if ((m = v.match(/^(\d+(?:\.\d+)?)KT$/i))) toman = Number(m[1]) * 1_000;
  else if ((m = v.match(/^(\d+(?:\.\d+)?)تومان$/))) toman = Number(m[1]);
  else if ((m = v.match(/^(\d+(?:\.\d+)?)(ریال)?$/))) toman = Number(m[1]) / 10;

  if (toman === undefined || !Number.isFinite(toman)) return undefined;
  toman = Math.round(toman);
  return { rial: toman * 10, toman, label: label(toman) };
}
