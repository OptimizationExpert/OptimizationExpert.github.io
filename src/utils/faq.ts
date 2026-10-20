// Extracts question/answer pairs from a note's «سوالات متداول» section so they can be
// emitted as FAQPage structured data. Supports the two formats used on the site:
//   <h3>Question?</h3> <p>Answer</p>     and     **Question?** followed by answer text
// (### headings are also accepted). Returns [] when fewer than two pairs are found.

export interface Faq {
  q: string;
  a: string;
}

const FAQ_TITLES = 'سوالات متداول|سؤالات متداول|سوال‌های متداول|سؤال‌های متداول|پرسش‌های متداول|پرسش‌های رایج|پرسش و پاسخ';
// Markdown heading (## / ###) or HTML heading (<h2> / <h3>).
const FAQ_HEADING = new RegExp(`^(?:(#{2,3})\\s*(?:${FAQ_TITLES})[^\\n]*|<h([23])[^>]*>\\s*(?:${FAQ_TITLES})[^<]*</h[23]>\\s*)$`, 'm');

// Fallback format: questions written as short <p> paragraphs ending with a question mark.
const PARAGRAPH_QUESTION = /^<p[^>]*>([^<]{5,220}[؟?])\s*<\/p>\s*$/;

const QUESTION_PATTERNS = [
  /^<h3[^>]*>([\s\S]+?)<\/h3>\s*$/, // <h3>Question</h3>
  /^###\s+(.+?)\s*$/, // ### Question
  /^\*\*(.+?)\*\*\s*$/, // **Question** on its own line
];

function toPlainText(text: string): string {
  return text
    .replace(/<[^>]+>/g, ' ') // HTML tags
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '') // images
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1') // links -> link text
    .replace(/`([^`]*)`/g, '$1') // inline code
    .replace(/\$\$?([^$]+)\$\$?/g, '$1') // inline math delimiters
    .replace(/(\*\*|__|\*|_)(.+?)\1/g, '$2') // bold / italic
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function extractFaqs(markdown: string): Faq[] {
  if (!markdown) return [];
  const heading = FAQ_HEADING.exec(markdown);
  if (!heading) return [];

  // The section ends at the next heading of the same or higher level.
  const level = heading[1] ? heading[1].length : Number(heading[2]);
  const rest = markdown.slice(heading.index + heading[0].length);
  // Under a markdown heading, questions may themselves be <h3> tags, so only a
  // strictly higher-level HTML heading ends the section. Under an HTML heading,
  // questions are paragraphs, so any heading of the same or higher level ends it.
  const htmlEnd = heading[1] ? level - 1 : level;
  const endParts = [`#{1,${level}}\\s`];
  if (htmlEnd >= 1) endParts.push(`<h[1-${htmlEnd}][\\s>]`);
  const endRe = new RegExp(`^(${endParts.join('|')})`, 'm');
  const end = endRe.exec(rest);
  const section = end ? rest.slice(0, end.index) : rest;

  const primary = parse(section, QUESTION_PATTERNS);
  if (primary.length >= 2) return primary;
  const fallback = parse(section, [PARAGRAPH_QUESTION]);
  return fallback.length >= 2 ? fallback : [];
}

function parse(section: string, patterns: RegExp[]): Faq[] {
  const faqs: Faq[] = [];
  let current: { q: string; a: string[] } | null = null;
  const flush = () => {
    if (!current) return;
    const q = toPlainText(current.q);
    const a = toPlainText(current.a.join(' '));
    if (q && a) faqs.push({ q, a });
  };

  for (const line of section.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const match = patterns.map((re) => re.exec(trimmed)).find(Boolean);
    if (match) {
      flush();
      current = { q: match[1], a: [] };
    } else if (current) {
      current.a.push(trimmed);
    }
  }
  flush();
  return faqs;
}
