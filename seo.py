
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بات مستقل پیشنهاد کلمات کلیدی برای سایت Optimization Expert

ویژگی‌ها
--------
1) بررسی صفحات فعلی سایت از طریق sitemap.xml
2) دریافت پیشنهادهای Google Autocomplete
3) بررسی Google Trends RSS و Google News RSS به‌عنوان سیگنال تازگی
4) خواندن اختیاری خروجی CSV سرچ کنسول، بدون نیاز به API یا نصب پکیج
5) جلوگیری از پیشنهادهای تکراری با history.json
6) ساخت گزارش CSV، Markdown و HTML فارسی
7) ارسال اختیاری خلاصه گزارش به تلگرام
8) امکان اجرای یک‌باره یا اجرای خودکار روزانه

این فایل فقط از کتابخانه‌های استاندارد پایتون استفاده می‌کند و به pip نیاز ندارد.

اجرای معمولی:
    python seo_keyword_bot.py

اجرای آزمایشی بدون اینترنت:
    python seo_keyword_bot.py --offline

اجرای مداوم روزانه:
    python seo_keyword_bot.py --daily

نکته: امتیاز تولیدشده «امتیاز اولویت محتوا» است، نه حجم جست‌وجو.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import html
import hashlib
import json
import math
import os
import re
import socket
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


# =============================================================================
# تنظیمات اصلی - فقط در صورت نیاز این بخش را تغییر دهید
# =============================================================================

SITE_URL = "https://optimizationexpert.github.io/"
SITE_NAME = "Optimization Expert"
TARGET_COUNTRY = "IR"
TARGET_LANGUAGE = "fa"

TOP_N = 20
QUERY_BUDGET = 18
REQUEST_TIMEOUT_SECONDS = 3
MAX_SITE_PAGES = 40
HISTORY_RETENTION_DAYS = 90
MIN_PRIORITY_SCORE = 18.0

# گزارش بعد از اجرا در مرورگر باز شود؟
OPEN_HTML_REPORT = True

# اگر فایل را داخل Spyder اجرا می‌کنید و می‌خواهید برنامه همیشه باز بماند
# و هر روز رأس ساعت مشخص اجرا شود، مقدار زیر را True کنید.
RUN_DAILY_LOOP = False
DAILY_RUN_TIME = "09:00"  # ساعت سیستم کامپیوتر؛ قالب HH:MM
RUN_IMMEDIATELY_IN_DAILY_MODE = True

# ارسال اختیاری گزارش به تلگرام
# مقادیر را می‌توانید اینجا وارد کنید یا به‌صورت Environment Variable تنظیم کنید.
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
TELEGRAM_TOP_N = 8

# فایل اختیاری خروجی Google Search Console را کنار همین فایل قرار دهید.
# نام‌های زیر به‌صورت خودکار جست‌وجو می‌شوند.
GSC_CSV_NAMES = (
    "gsc_export.csv",
    "search_console.csv",
    "Queries.csv",
    "queries.csv",
)

# تعداد درخواست‌های همزمان برای خواندن صفحات سایت
SITE_FETCH_WORKERS = 8
SUGGEST_FETCH_WORKERS = 6
NEWS_FETCH_WORKERS = 5

# بین درخواست‌های Google Suggest کمی مکث می‌کنیم تا درخواست‌ها تهاجمی نباشند.
SUGGEST_REQUEST_DELAY_SECONDS = 0.05

# یک timeout پیش‌فرض سراسری نیز برای DNS و socket قرار می‌دهیم.
socket.setdefaulttimeout(REQUEST_TIMEOUT_SECONDS)


COURSES: list[dict[str, Any]] = [
    {
        "id": "modeling",
        "name": "مدل‌سازی مسائل بهینه‌سازی",
        "url": "/posts/2026/06/21/optimization-modeling-course/",
        "signals": [
            "مدل سازی", "مدلسازی", "فرمول بندی", "بهینه سازی ریاضی",
            "متغیر تصمیم", "تابع هدف", "قید", "خطی سازی", "pyomo",
            "gurobi", "jump", "مدل ریاضی", "بهینه سازی در پایتون",
        ],
        "seeds": [
            "آموزش مدل سازی ریاضی",
            "فرمول بندی مسائل بهینه سازی",
            "مدل سازی بهینه سازی در پایتون",
            "آموزش Pyomo فارسی",
            "متغیر تصمیم تابع هدف و قیود",
            "خطی سازی قیود در بهینه سازی",
            "ساخت مدل بهینه سازی با Pyomo",
        ],
    },
    {
        "id": "power_intro",
        "name": "بهینه‌سازی مقدماتی سیستم‌های قدرت",
        "url": "/posts/2026/06/22/intro-power-system-course/",
        "signals": [
            "سیستم قدرت", "پخش بار اقتصادی", "economic dispatch",
            "dc opf", "باتری", "ذخیره ساز", "unit commitment", "pyomo",
            "تولید اقتصادی", "پخش بار بهینه", "شبکه برق",
        ],
        "seeds": [
            "پخش بار اقتصادی در پایتون",
            "آموزش DC OPF با Pyomo",
            "مدل سازی باتری در Pyomo",
            "آرایش بهینه واحدها در پایتون",
            "بهینه سازی سیستم قدرت در پایتون",
            "Dynamic Economic Dispatch در پایتون",
        ],
    },
    {
        "id": "power_advanced",
        "name": "بهینه‌سازی پیشرفته سیستم‌های قدرت",
        "url": "/posts/2026/06/20/Advanced-Power-System-Course/",
        "signals": [
            "ac opf", "n-1", "ptdf", "lodf", "توسعه شبکه", "tep",
            "سوئیچینگ خطوط", "volt var", "پارتو", "جایابی باتری",
            "سیستم قدرت", "امنیت شبکه", "بهینه سازی چند هدفه",
        ],
        "seeds": [
            "آموزش AC OPF با Pyomo",
            "قیود امنیت N-1 در پایتون",
            "محاسبه PTDF و LODF",
            "جایابی بهینه باتری در شبکه قدرت",
            "توسعه شبکه انتقال با Pyomo",
            "بهینه سازی چند هدفه سیستم قدرت",
            "سوئیچینگ بهینه خطوط انتقال",
        ],
    },
    {
        "id": "uncertainty",
        "name": "مدل‌سازی عدم قطعیت",
        "url": "/posts/2026/06/23/uncertainty-modeling-course/",
        "signals": [
            "عدم قطعیت", "robust", "مقاوم", "stochastic", "تصادفی",
            "igdt", "فازی", "سناریو", "مونت کارلو", "احتمالاتی",
            "scenario reduction", "chance constraint",
        ],
        "seeds": [
            "مدل سازی عدم قطعیت در پایتون",
            "آموزش robust optimization",
            "آموزش IGDT با مثال",
            "stochastic optimization با Pyomo",
            "تفاوت بهینه سازی مقاوم و تصادفی",
            "بهینه سازی فازی در پایتون",
            "سناریوسازی و کاهش سناریو در پایتون",
        ],
    },
    {
        "id": "vrp",
        "name": "مسیریابی وسایل نقلیه در Python",
        "url": "/posts/2026/06/24/vrp-python-course/",
        "signals": [
            "vrp", "مسیریابی", "ortools", "or-tools", "cvrp", "vrptw",
            "evrp", "tsp", "تحویل تقسیمی", "چند انباره", "پنجره زمانی",
            "لجستیک", "vehicle routing", "مسئله مسیریابی خودرو",
        ],
        "seeds": [
            "آموزش VRP در پایتون",
            "OR-Tools VRP فارسی",
            "آموزش CVRP با OR-Tools",
            "آموزش VRPTW در پایتون",
            "مسیریابی خودروی برقی EVRP",
            "Split Delivery VRP در پایتون",
            "Multi Depot VRP در پایتون",
            "Time Dependent VRP",
            "مسئله مسیریابی خودرو با پنجره زمانی",
        ],
    },
]


# =============================================================================
# مدل داده و ابزارهای متنی
# =============================================================================

FA_STOPWORDS = {
    "از", "به", "در", "با", "برای", "و", "یا", "که", "را", "یک", "این",
    "آن", "چیست", "چگونه", "چطور", "آموزش", "مثال", "پروژه", "کد", "حل",
    "روش", "روی", "بر", "تا", "های", "the", "a", "an", "of", "for", "with",
    "in", "to", "and", "tutorial", "how", "what", "is",
}

INTENT_TERMS = {
    "آموزشی": ("آموزش", "راهنما", "گام به گام", "مثال", "کد", "پیاده سازی", "tutorial", "how"),
    "پروژه‌ای": ("پروژه", "کد آماده", "case study", "پایان نامه", "صنعتی", "مثال واقعی"),
    "مقایسه‌ای": ("تفاوت", "مقایسه", "بهتر", "versus", " vs "),
    "تعریفی": ("چیست", "مفهوم", "تعریف", "what is"),
    "تجاری": ("دوره", "ثبت نام", "هزینه", "خرید", "کلاس"),
}

QUESTION_PREFIXES = ("چگونه", "چطور", "چرا", "آیا", "کدام", "چه ")


@dataclass
class ExistingPage:
    title: str
    description: str
    url: str


@dataclass
class Candidate:
    keyword: str
    sources: set[str] = field(default_factory=set)
    source_details: list[str] = field(default_factory=list)
    course_votes: dict[str, int] = field(default_factory=dict)

    course_id: str = ""
    course_name: str = ""
    course_url: str = ""
    intent: str = "آموزشی"
    content_type: str = "آموزش گام‌به‌گام"
    suggested_title: str = ""

    score: float = 0.0
    similarity: float = 0.0
    closest_title: str = ""
    closest_url: str = ""
    action: str = "محتوای جدید"
    reason: str = ""

    impressions: float = 0.0
    clicks: float = 0.0
    ctr: float = 0.0
    position: float = 0.0
    gsc_page: str = ""

    last_suggested: str = ""
    history_penalty: float = 0.0


def normalise(text: str) -> str:
    """متن فارسی و انگلیسی را برای مقایسه یکنواخت می‌کند."""
    text = html.unescape(text or "")
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(str.maketrans({
        "ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه",
        "ؤ": "و", "إ": "ا", "أ": "ا", "ـ": " ", "\u200c": " ",
        "\u200f": " ", "\u200e": " ",
    }))
    text = text.lower()
    text = re.sub(r"[\u064b-\u065f\u0670]", "", text)
    text = re.sub(r"[^0-9a-z\u0600-\u06ff+.#-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    aliases = (
        ("python", "پایتون"),
        ("or tools", "ortools"),
        ("or-tools", "ortools"),
        ("مدل سازی", "مدلسازی"),
        ("بهینه سازی", "بهینهسازی"),
        ("عدم قطعیت", "عدمقطعیت"),
        ("سیستم های قدرت", "سیستم قدرت"),
    )
    for old, new in aliases:
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def display_clean(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -–—|:،")


def token_set(text: str) -> set[str]:
    return {
        token
        for token in normalise(text).split()
        if len(token) > 1 and token not in FA_STOPWORDS
    }


def absolute_url(url_or_path: str) -> str:
    return urllib.parse.urljoin(SITE_URL.rstrip("/") + "/", url_or_path)


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip().replace(",", "")
    text = text.replace("٪", "%")
    if not text:
        return default
    try:
        if text.endswith("%"):
            return float(text[:-1]) / 100.0
        return float(text)
    except ValueError:
        return default


def md_escape(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def html_escape(text: Any) -> str:
    return html.escape(str(text), quote=True)


# =============================================================================
# ارتباط شبکه
# =============================================================================


def http_get(
    url: str,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
    accept: str = "*/*",
    attempts: int = 1,
) -> bytes:
    """یک URL عمومی را با retry محدود دریافت می‌کند."""
    last_error: Exception | None = None

    for attempt in range(attempts):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; OptimizationExpertKeywordBot/2.0; "
                    "+https://optimizationexpert.github.io/)"
                ),
                "Accept": accept,
                "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.6",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504}:
                raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc

        if attempt + 1 < attempts:
            time.sleep(0.7 + attempt * 0.5)

    if last_error is not None:
        raise last_error
    raise RuntimeError("HTTP request failed")


class PageMetaParser(HTMLParser):
    """title و meta description را از HTML استخراج می‌کند."""

    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                if not self.description:
                    self.description = display_clean(attrs_dict.get("content", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return display_clean(" ".join(self.title_parts))


def fetch_sitemap_urls(status: dict[str, str]) -> list[str]:
    sitemap_url = absolute_url("/sitemap.xml")
    try:
        raw = http_get(
            sitemap_url,
            accept="application/xml,text/xml;q=0.9,*/*;q=0.5",
        )
        root = ET.fromstring(raw)
        urls: list[str] = []
        for element in root.iter():
            if element.tag.lower().endswith("loc") and element.text:
                url = display_clean(element.text)
                if url.startswith(SITE_URL.rstrip("/")):
                    urls.append(url)
        unique = list(dict.fromkeys(urls))[:MAX_SITE_PAGES]
        status["Sitemap"] = f"فعال؛ {len(unique)} نشانی پیدا شد"
        return unique
    except Exception as exc:
        status["Sitemap"] = f"خطا؛ {type(exc).__name__}"
        return []


def fetch_page_metadata(url: str) -> ExistingPage | None:
    try:
        raw = http_get(url, accept="text/html,application/xhtml+xml")
        text = raw.decode("utf-8", errors="replace")
        parser = PageMetaParser()
        parser.feed(text)
        title = parser.title
        # نام برند انتهای title را برای مقایسه حذف می‌کنیم.
        title = re.sub(r"\s*[|–—-]\s*Optimization Expert\s*$", "", title, flags=re.I)
        if not title:
            return None
        return ExistingPage(title=title, description=parser.description, url=url)
    except Exception:
        return None


def collect_existing_pages(status: dict[str, str], offline: bool) -> list[ExistingPage]:
    if offline:
        status["صفحات سایت"] = "در حالت آفلاین بررسی نشد"
        return []

    urls = fetch_sitemap_urls(status)
    if not urls:
        return []

    pages: list[ExistingPage] = []
    with ThreadPoolExecutor(max_workers=SITE_FETCH_WORKERS) as executor:
        future_map = {executor.submit(fetch_page_metadata, url): url for url in urls}
        for future in as_completed(future_map):
            try:
                page = future.result()
                if page is not None:
                    pages.append(page)
            except Exception:
                continue

    status["صفحات سایت"] = f"{len(pages)} صفحه با موفقیت خوانده شد"
    return sorted(pages, key=lambda p: p.url)


def fetch_google_suggestions(query: str) -> list[str]:
    params = urllib.parse.urlencode({
        "client": "firefox",
        "hl": TARGET_LANGUAGE,
        "q": query,
    })
    url = f"https://suggestqueries.google.com/complete/search?{params}"
    raw = http_get(url, accept="application/json,text/javascript,*/*;q=0.5")
    data = json.loads(raw.decode("utf-8", errors="replace"))
    values = data[1] if isinstance(data, list) and len(data) > 1 else []
    return [display_clean(str(value)) for value in values if display_clean(str(value))]


def google_sources_available() -> bool:
    """با یک درخواست کوچک بررسی می‌کند منابع گوگل در دسترس هستند یا نه."""
    try:
        fetch_google_suggestions("بهینه سازی")
        return True
    except Exception:
        return False


def fetch_google_news_titles(query: str) -> list[str]:
    encoded = urllib.parse.quote_plus(query)
    url = (
        "https://news.google.com/rss/search?"
        f"q={encoded}&hl=fa&gl={TARGET_COUNTRY}&ceid={TARGET_COUNTRY}:fa"
    )
    raw = http_get(url, accept="application/rss+xml,application/xml,text/xml")
    root = ET.fromstring(raw)
    titles: list[str] = []
    for item in root.findall(".//item")[:20]:
        title = display_clean(item.findtext("title") or "")
        title = re.sub(r"\s+-\s+[^-]{2,80}$", "", title).strip()
        if title:
            titles.append(title)
    return titles


def fetch_google_trends_titles() -> list[str]:
    url = f"https://trends.google.com/trending/rss?geo={TARGET_COUNTRY}"
    raw = http_get(url, accept="application/rss+xml,application/xml,text/xml")
    root = ET.fromstring(raw)
    return [
        display_clean(item.findtext("title") or "")
        for item in root.findall(".//item")
        if display_clean(item.findtext("title") or "")
    ]


# =============================================================================
# جمع‌آوری کلمات کلیدی
# =============================================================================


def add_candidate(
    store: dict[str, Candidate],
    keyword: str,
    source: str,
    course_id: str = "",
    detail: str = "",
) -> None:
    keyword = display_clean(keyword)
    key = normalise(keyword)

    if len(key) < 4 or len(key) > 180:
        return
    if len(key.split()) > 18:
        return

    candidate = store.setdefault(key, Candidate(keyword=keyword))
    candidate.sources.add(source)

    if detail and detail not in candidate.source_details:
        candidate.source_details.append(detail)
    if course_id:
        candidate.course_votes[course_id] = candidate.course_votes.get(course_id, 0) + 1


def generated_variants(course: dict[str, Any], seed: str) -> list[str]:
    """حتی در صورت قطع اینترنت، چند long-tail منطقی ایجاد می‌کند."""
    seed = display_clean(seed)
    norm = normalise(seed)
    values = [seed]

    if "آموزش" not in norm:
        values.append(f"آموزش {seed}")
    if "پایتون" not in norm:
        values.append(f"{seed} در پایتون")
    if not any(term in norm for term in ("مثال", "پروژه", "کد")):
        values.append(f"{seed} با مثال و کد")

    if course["id"] == "vrp" and "ortools" not in norm:
        values.append(f"{seed} با OR-Tools")
    elif course["id"] in {"modeling", "power_intro", "power_advanced", "uncertainty"}:
        if "pyomo" not in norm:
            values.append(f"{seed} با Pyomo")

    return list(dict.fromkeys(display_clean(v) for v in values if display_clean(v)))


def build_query_rotation(run_date: dt.date) -> list[tuple[dict[str, Any], str]]:
    """هر روز ترکیب متفاوتی از seedها انتخاب می‌شود، ولی همه دوره‌ها پوشش داده می‌شوند."""
    modifiers = ("", "آموزش ", "مثال ", "پروژه ", " چیست", " در پایتون")
    pool: list[tuple[dict[str, Any], str]] = []

    for course_index, course in enumerate(COURSES):
        for seed_index, seed in enumerate(course["seeds"]):
            modifier = modifiers[(run_date.toordinal() + seed_index + course_index) % len(modifiers)]
            if modifier.endswith(" "):
                query = f"{modifier}{seed}"
            else:
                query = f"{seed}{modifier}"
            pool.append((course, display_clean(query)))

    # مرتب‌سازی قطعی اما روزانه متفاوت؛ بدون random سراسری.
    def daily_key(item: tuple[dict[str, Any], str]) -> tuple[str, str]:
        payload = (normalise(item[1]) + "|" + run_date.isoformat()).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        return digest, item[0]["id"]

    pool.sort(key=daily_key)
    selected = pool[:QUERY_BUDGET]

    selected_ids = {course["id"] for course, _ in selected}
    for course in COURSES:
        if course["id"] not in selected_ids and course["seeds"]:
            selected.append((course, course["seeds"][0]))

    return selected


def find_optional_gsc_csv(base_dir: Path) -> Path | None:
    for name in GSC_CSV_NAMES:
        path = base_dir / name
        if path.exists() and path.is_file():
            return path
    return None


def canonical_header(value: str) -> str:
    value = normalise(value)
    value = value.replace(" ", "")
    return value


def choose_column(fieldnames: Iterable[str], aliases: Iterable[str]) -> str | None:
    mapping = {canonical_header(name): name for name in fieldnames if name}
    for alias in aliases:
        key = canonical_header(alias)
        if key in mapping:
            return mapping[key]
    return None


def load_gsc_csv(
    path: Path,
    store: dict[str, Candidate],
    status: dict[str, str],
) -> None:
    """خروجی CSV سرچ کنسول را با نام ستون‌های مختلف می‌خواند."""
    encodings = ("utf-8-sig", "utf-8", "cp1256", "latin-1")
    text = ""
    used_encoding = ""

    for encoding in encodings:
        try:
            text = path.read_text(encoding=encoding)
            used_encoding = encoding
            break
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            status["Search Console CSV"] = f"خطا در خواندن فایل: {exc}"
            return

    if not text:
        status["Search Console CSV"] = "فایل خالی یا غیرقابل خواندن بود"
        return

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    fields = reader.fieldnames or []

    query_col = choose_column(fields, (
        "Top queries", "Query", "Queries", "Keyword", "کلمه کلیدی",
        "عبارت جستجو", "عبارت‌های برتر", "کوئری",
    ))
    clicks_col = choose_column(fields, ("Clicks", "Click", "کلیک", "کلیک‌ها"))
    impressions_col = choose_column(fields, (
        "Impressions", "Impression", "نمایش", "نمایش‌ها",
    ))
    ctr_col = choose_column(fields, ("CTR", "نرخ کلیک"))
    position_col = choose_column(fields, (
        "Position", "Average position", "میانگین موقعیت", "رتبه",
    ))
    page_col = choose_column(fields, ("Page", "Pages", "صفحه"))

    if not query_col:
        status["Search Console CSV"] = "ستون Query/Top queries پیدا نشد"
        return

    row_count = 0
    for row in reader:
        keyword = display_clean(row.get(query_col, ""))
        if not keyword:
            continue

        add_candidate(store, keyword, "Search Console")
        candidate = store.get(normalise(keyword))
        if candidate is None:
            continue

        candidate.clicks += safe_float(row.get(clicks_col, 0.0)) if clicks_col else 0.0
        candidate.impressions += safe_float(row.get(impressions_col, 0.0)) if impressions_col else 0.0

        ctr_value = safe_float(row.get(ctr_col, 0.0)) if ctr_col else 0.0
        position_value = safe_float(row.get(position_col, 0.0)) if position_col else 0.0

        # اگر یک query چند سطر داشت، مقدار آخر را موقتاً ذخیره می‌کنیم؛ پایین‌تر
        # از clicks/impressions نیز CTR نهایی محاسبه خواهد شد.
        if ctr_value:
            candidate.ctr = ctr_value
        if position_value:
            if candidate.position <= 0:
                candidate.position = position_value
            else:
                candidate.position = (candidate.position + position_value) / 2.0
        if page_col and not candidate.gsc_page:
            candidate.gsc_page = display_clean(row.get(page_col, ""))
        row_count += 1

    for candidate in store.values():
        if candidate.impressions > 0:
            candidate.ctr = candidate.clicks / candidate.impressions

    status["Search Console CSV"] = (
        f"فعال؛ {row_count} ردیف از {path.name} با {used_encoding}"
    )


def dedupe_signature(text: str) -> str:
    """پسوندهای عمومی را حذف می‌کند تا یک موضوع با چند عنوان تکرار نشود."""
    generic = {
        "آموزش", "پایتون", "pyomo", "ortools", "مثال", "کد", "کامل",
        "پروژه", "چیست", "فارسی", "گام", "به", "با", "در", "و",
        "مدل", "پیادهسازی", "راهنما",
    }
    values = [token for token in normalise(text).split() if token not in generic]
    return " ".join(values)


def collect_candidates(
    run_date: dt.date,
    offline: bool,
    base_dir: Path,
    history_latest: dict[str, dt.date],
) -> tuple[list[Candidate], dict[str, str], list[ExistingPage]]:
    store: dict[str, Candidate] = {}
    status: dict[str, str] = {}

    existing_pages = collect_existing_pages(status, offline)

    # Seedها و variantها همیشه اضافه می‌شوند تا گزارش حتی بدون اینترنت خالی نباشد.
    for course in COURSES:
        for seed in course["seeds"]:
            for variant in generated_variants(course, seed):
                add_candidate(
                    store,
                    variant,
                    source="Seed/Content Gap",
                    course_id=course["id"],
                )

    # CSV سرچ کنسول اختیاری
    gsc_path = find_optional_gsc_csv(base_dir)
    if gsc_path:
        load_gsc_csv(gsc_path, store, status)
    else:
        status["Search Console CSV"] = "فایل اختیاری پیدا نشد"

    if offline:
        status["Google Autocomplete"] = "غیرفعال در حالت آفلاین"
        status["Google News"] = "غیرفعال در حالت آفلاین"
        status["Google Trends"] = "غیرفعال در حالت آفلاین"
    else:
        google_ok = google_sources_available()
        if not google_ok:
            status["Google Autocomplete"] = "در دسترس نبود؛ از seedهای داخلی استفاده شد"
            status["Google News"] = "به دلیل عدم دسترسی به گوگل بررسی نشد"
            status["Google Trends"] = "به دلیل عدم دسترسی به گوگل بررسی نشد"
        else:
            # Google Autocomplete؛ درخواست‌ها با تعداد محدود worker هم‌زمان اجرا
            # می‌شوند تا در اینترنت ضعیف، برنامه چند دقیقه متوقف نماند.
            suggest_success = 0
            suggest_fail = 0
            query_items = build_query_rotation(run_date)

            def suggest_task(item: tuple[dict[str, Any], str]) -> tuple[dict[str, Any], str, list[str]]:
                course, query = item
                time.sleep(SUGGEST_REQUEST_DELAY_SECONDS)
                return course, query, fetch_google_suggestions(query)

            with ThreadPoolExecutor(max_workers=SUGGEST_FETCH_WORKERS) as executor:
                future_map = {executor.submit(suggest_task, item): item for item in query_items}
                for future in as_completed(future_map):
                    course, query = future_map[future]
                    try:
                        _, _, suggestions = future.result()
                        suggest_success += 1
                        for suggestion in suggestions:
                            add_candidate(
                                store,
                                suggestion,
                                source="Google Autocomplete",
                                course_id=course["id"],
                                detail=f"پیشنهاد برای: {query}",
                            )
                    except Exception:
                        suggest_fail += 1

            status["Google Autocomplete"] = (
                f"{suggest_success} درخواست موفق، {suggest_fail} ناموفق"
            )

            # Google News: عنوان خبر را مستقیماً کلمه کلیدی نمی‌کنیم؛ فقط اگر با
            # candidateهای موجود ارتباط داشته باشد، سیگنال تازگی اضافه می‌کنیم.
            news_titles: list[str] = []
            news_success = 0

            def news_task(course: dict[str, Any]) -> list[str]:
                return fetch_google_news_titles(course["signals"][0])

            with ThreadPoolExecutor(max_workers=NEWS_FETCH_WORKERS) as executor:
                future_map = {executor.submit(news_task, course): course for course in COURSES}
                for future in as_completed(future_map):
                    try:
                        news_titles.extend(future.result())
                        news_success += 1
                    except Exception:
                        continue

            status["Google News"] = f"{news_success}/{len(COURSES)} خوشه خوانده شد"

            if news_titles:
                news_token_sets = [token_set(title) for title in news_titles]
                for candidate in store.values():
                    c_tokens = token_set(candidate.keyword)
                    if not c_tokens:
                        continue
                    best_overlap = max(
                        (len(c_tokens & n_tokens) / max(1, len(c_tokens)) for n_tokens in news_token_sets),
                        default=0.0,
                    )
                    if best_overlap >= 0.60:
                        candidate.sources.add("Google News")

            # Google Trends ایران: تنها موارد مرتبط با دوره‌ها به candidate تبدیل می‌شوند.
            try:
                trend_titles = fetch_google_trends_titles()
                relevant_count = 0
                for trend in trend_titles:
                    course, match_score = map_course(trend, COURSES)
                    if match_score >= 4.0:
                        add_candidate(
                            store,
                            trend,
                            source="Google Trends",
                            course_id=course["id"],
                        )
                        relevant_count += 1
                status["Google Trends"] = (
                    f"{len(trend_titles)} روند خوانده شد؛ {relevant_count} مورد مرتبط"
                )
            except Exception as exc:
                status["Google Trends"] = f"خطا؛ {type(exc).__name__}"
    candidates: list[Candidate] = []
    for candidate in store.values():
        course, course_match = map_course(
            candidate.keyword,
            COURSES,
            candidate.course_votes,
        )

        # عبارت‌های Search Console باید واقعاً با یکی از دوره‌ها مرتبط باشند.
        if "Search Console" in candidate.sources and course_match < 2.0:
            continue

        candidate.course_id = course["id"]
        candidate.course_name = course["name"]
        candidate.course_url = absolute_url(course["url"])
        candidate.intent, candidate.content_type = infer_intent(candidate.keyword)

        page, similarity = closest_page(candidate.keyword, existing_pages)
        candidate.similarity = similarity
        if page is not None:
            candidate.closest_title = page.title
            candidate.closest_url = page.url

        candidate.suggested_title = suggest_title(
            candidate.keyword,
            course,
            candidate.intent,
        )

        apply_history_penalty(candidate, history_latest, run_date)
        score_candidate(candidate, course_match)
        candidate.reason = build_reason(candidate)

        if candidate.score >= MIN_PRIORITY_SCORE:
            candidates.append(candidate)

    candidates.sort(
        key=lambda c: (
            -c.score,
            -c.impressions,
            normalise(c.keyword),
        )
    )

    # حذف موارد بسیار شبیه در خود خروجی نهایی؛ برای نمونه، چهار شکل مختلف
    # «Multi Depot VRP در پایتون» فقط به‌صورت یک موضوع نگه داشته می‌شود.
    deduplicated: list[Candidate] = []
    seen_signatures: set[str] = set()

    for candidate in candidates:
        signature = dedupe_signature(candidate.keyword)
        if signature and signature in seen_signatures:
            continue

        is_duplicate = False
        for selected in deduplicated:
            ratio = difflib.SequenceMatcher(
                None,
                normalise(candidate.keyword),
                normalise(selected.keyword),
            ).ratio()
            left = token_set(candidate.keyword)
            right = token_set(selected.keyword)
            union = left | right
            jaccard = len(left & right) / len(union) if union else 0.0
            if ratio >= 0.88 or jaccard >= 0.82:
                is_duplicate = True
                break

        if is_duplicate:
            continue

        deduplicated.append(candidate)
        if signature:
            seen_signatures.add(signature)
        if len(deduplicated) >= max(TOP_N * 3, 50):
            break

    return deduplicated, status, existing_pages


# =============================================================================
# تطبیق دوره، نیت و امتیازدهی
# =============================================================================


def map_course(
    keyword: str,
    courses: list[dict[str, Any]],
    course_votes: dict[str, int] | None = None,
) -> tuple[dict[str, Any], float]:
    keyword_norm = normalise(keyword)
    keyword_tokens = token_set(keyword)

    best_course = courses[0]
    best_score = -1.0

    for course in courses:
        score = float((course_votes or {}).get(course["id"], 0) * 24)

        for signal in course.get("signals", []):
            signal_norm = normalise(signal)
            if signal_norm and signal_norm in keyword_norm:
                score += 4.0 + min(len(signal_norm.split()), 3)
            else:
                score += len(keyword_tokens & token_set(signal)) * 1.4

        for seed in course.get("seeds", []):
            score += len(keyword_tokens & token_set(seed)) * 0.35

        if score > best_score:
            best_course = course
            best_score = score

    return best_course, best_score


def infer_intent(keyword: str) -> tuple[str, str]:
    value = f" {normalise(keyword)} "
    scores: dict[str, int] = {}

    for intent, terms in INTENT_TERMS.items():
        scores[intent] = sum(1 for term in terms if normalise(term) in value)

    intent = max(scores, key=scores.get) if max(scores.values(), default=0) else "آموزشی"

    content_types = {
        "مقایسه‌ای": "مقاله مقایسه‌ای",
        "تعریفی": "راهنمای مفهومی",
        "پروژه‌ای": "مطالعه موردی / پروژه",
        "تجاری": "صفحه دوره یا راهنمای انتخاب",
        "آموزشی": "آموزش گام‌به‌گام",
    }
    return intent, content_types[intent]


def closest_page(
    keyword: str,
    pages: list[ExistingPage],
) -> tuple[ExistingPage | None, float]:
    target = normalise(keyword)
    target_tokens = token_set(keyword)
    best_page: ExistingPage | None = None
    best_score = 0.0

    for page in pages:
        title_norm = normalise(page.title)
        title_tokens = token_set(page.title)

        sequence = difflib.SequenceMatcher(None, target, title_norm).ratio()
        union = target_tokens | title_tokens
        intersection = target_tokens & title_tokens
        jaccard = len(intersection) / len(union) if union else 0.0
        containment = (
            len(intersection) / min(len(target_tokens), len(title_tokens))
            if target_tokens and title_tokens
            else 0.0
        )

        score = 0.45 * sequence + 0.30 * jaccard + 0.25 * containment

        if len(target_tokens) <= 3 and containment >= 0.80:
            score = max(score, 0.82)
        elif len(target_tokens) <= 5 and containment >= 0.80:
            score = max(score, 0.72)

        if page.description:
            description_norm = normalise(page.description)
            if target and target in description_norm:
                score = max(score, 0.88)
            else:
                desc_tokens = token_set(page.description)
                desc_containment = (
                    len(target_tokens & desc_tokens) / len(target_tokens)
                    if target_tokens
                    else 0.0
                )
                score = max(score, 0.45 * desc_containment)

        if score > best_score:
            best_page = page
            best_score = score

    return best_page, best_score


def suggest_title(
    keyword: str,
    course: dict[str, Any],
    intent: str,
) -> str:
    clean = display_clean(keyword)
    norm = normalise(clean)

    if intent == "مقایسه‌ای":
        if "تفاوت" in norm or "مقایسه" in norm:
            return clean
        return f"مقایسه {clean}: تفاوت‌ها، کاربردها و انتخاب روش مناسب"

    if intent == "تعریفی" or norm.startswith(QUESTION_PREFIXES):
        return clean.rstrip("؟?") + "؛ تعریف، مدل ریاضی و مثال کاربردی"

    if intent == "پروژه‌ای":
        if "پروژه" in norm:
            return clean
        return f"پروژه {clean}: مدل‌سازی، کدنویسی و تحلیل نتایج"

    if "آموزش" in norm:
        return clean

    has_python = "پایتون" in norm

    if course["id"] == "vrp":
        if "ortools" in norm:
            suffix = "با مثال و کد کامل"
        else:
            suffix = "با OR-Tools؛ مدل و کد کامل" if has_python else "در پایتون با OR-Tools؛ مدل و کد کامل"
    else:
        if "pyomo" in norm:
            suffix = "با مثال و کد کامل"
        else:
            suffix = "با Pyomo؛ مدل، کد و مثال" if has_python else "در پایتون با Pyomo؛ مدل، کد و مثال"

    return f"آموزش {clean} {suffix}"


def history_penalty_for_days(days: int, has_gsc: bool) -> float:
    if days <= 7:
        return 8.0 if has_gsc else 34.0
    if days <= 21:
        return 4.0 if has_gsc else 18.0
    if days <= 45:
        return 2.0 if has_gsc else 8.0
    return 0.0


def apply_history_penalty(
    candidate: Candidate,
    latest_history: dict[str, dt.date],
    run_date: dt.date,
) -> None:
    key = normalise(candidate.keyword)
    previous = latest_history.get(key)
    if previous is None:
        return

    days = (run_date - previous).days
    if days < 0:
        return

    candidate.last_suggested = previous.isoformat()
    candidate.history_penalty = history_penalty_for_days(
        days,
        has_gsc="Search Console" in candidate.sources,
    )


def score_candidate(candidate: Candidate, course_match: float) -> None:
    norm = normalise(candidate.keyword)
    word_count = len(norm.split())

    score = 0.0
    score += min(len(candidate.sources), 4) * 8.0
    score += min(course_match, 24.0)

    if 3 <= word_count <= 10:
        score += 9.0
    elif word_count == 2:
        score += 3.0
    elif word_count > 13:
        score -= 7.0

    if any(term in norm for term in (
        "آموزش", "مثال", "کد", "پروژه", "پایتون", "pyomo", "ortools",
    )):
        score += 8.0

    if any(term in norm for term in (
        "چیست", "چگونه", "چطور", "تفاوت", "مقایسه",
    )):
        score += 5.0

    if "Google Autocomplete" in candidate.sources:
        score += 10.0
    if "Google News" in candidate.sources:
        score += 5.0
    if "Google Trends" in candidate.sources:
        score += 9.0

    if "Search Console" in candidate.sources:
        impressions = max(candidate.impressions, 0.0)
        score += min(math.log1p(impressions) * 5.5, 32.0)

        if 4.0 <= candidate.position <= 20.0:
            score += 20.0
        elif 20.0 < candidate.position <= 40.0:
            score += 11.0
        elif 1.0 <= candidate.position < 4.0:
            score += 3.0

        if candidate.impressions >= 5 and candidate.ctr < 0.03:
            score += 9.0

    # تصمیم درباره ساخت محتوای جدید یا به‌روزرسانی صفحه موجود
    if candidate.similarity >= 0.82:
        if "Search Console" in candidate.sources:
            score += 6.0
            candidate.action = "به‌روزرسانی صفحه موجود"
        else:
            score -= 34.0
            candidate.action = "ادغام با محتوای موجود"
    elif candidate.similarity >= 0.62:
        if "Search Console" in candidate.sources:
            score += 4.0
            candidate.action = "بهینه‌سازی صفحه موجود"
        else:
            score -= 9.0
            candidate.action = "محتوای مکمل با زاویه متفاوت"
    else:
        score += 10.0
        candidate.action = "محتوای جدید"

    if len(norm) < 7:
        score -= 10.0

    score -= candidate.history_penalty
    candidate.score = round(score, 1)


def build_reason(candidate: Candidate) -> str:
    reasons: list[str] = []

    if "Search Console" in candidate.sources:
        reasons.append(
            f"داده واقعی Search Console: {candidate.impressions:.0f} نمایش، "
            f"رتبه {candidate.position:.1f} و CTR برابر {candidate.ctr:.1%}"
        )
    if "Google Autocomplete" in candidate.sources:
        reasons.append("در پیشنهادهای خودکار گوگل دیده شده است")
    if "Google Trends" in candidate.sources:
        reasons.append("سیگنال مرتبط از Google Trends دارد")
    if "Google News" in candidate.sources:
        reasons.append("با محتوای تازه خبری هم‌پوشانی دارد")
    if "Seed/Content Gap" in candidate.sources:
        reasons.append("با سرفصل دوره مرتبط است و شکاف محتوایی احتمالی دارد")

    if candidate.action == "محتوای جدید":
        reasons.append("شباهت کمی با صفحات فعلی سایت دارد")
    elif candidate.closest_title:
        reasons.append(f"به صفحه «{candidate.closest_title}» نزدیک است")

    if candidate.last_suggested:
        reasons.append(
            f"قبلاً در {candidate.last_suggested} پیشنهاد شده و جریمه تکرار گرفته است"
        )

    return "؛ ".join(reasons) if reasons else "ارتباط موضوعی مناسب با دوره"


def outline_for(candidate: Candidate) -> list[str]:
    keyword = candidate.keyword
    course = candidate.course_name

    if candidate.intent == "مقایسه‌ای":
        return [
            f"تعریف دقیق گزینه‌های مطرح‌شده در «{keyword}»",
            "مقایسه مفروضات، داده ورودی و ساختار مدل ریاضی",
            "مقایسه کیفیت جواب، سرعت حل و محدودیت‌های هر روش",
            "یک مثال عددی مشترک و تحلیل نتایج",
            f"راهنمای انتخاب روش و ارتباط آن با دوره {course}",
        ]

    if candidate.intent == "تعریفی":
        return [
            f"{keyword} دقیقاً چیست و چه مسئله‌ای را حل می‌کند؟",
            "اجزای مدل: متغیرهای تصمیم، تابع هدف و قیود",
            "یک مثال کوچک و قابل‌فهم",
            "پیاده‌سازی مرحله‌به‌مرحله در پایتون",
            f"خطاهای رایج و مسیر یادگیری در دوره {course}",
        ]

    return [
        f"تعریف مسئله و کاربردهای واقعی {keyword}",
        "ساخت مدل ریاضی: مجموعه‌ها، پارامترها، متغیرها، تابع هدف و قیود",
        "پیاده‌سازی مرحله‌به‌مرحله در پایتون",
        "تحلیل خروجی، اعتبارسنجی و خطاهای رایج",
        f"تمرین توسعه‌ای و لینک داخلی به دوره {course}",
    ]


# =============================================================================
# تاریخچه و گزارش‌ها
# =============================================================================


def load_history(
    output_dir: Path,
    run_date: dt.date,
) -> tuple[list[dict[str, Any]], dict[str, dt.date]]:
    path = output_dir / "history.json"
    if not path.exists():
        return [], {}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], {}

    items = raw.get("items", []) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return [], {}

    cutoff = run_date - dt.timedelta(days=HISTORY_RETENTION_DAYS)
    cleaned: list[dict[str, Any]] = []
    latest: dict[str, dt.date] = {}

    for item in items:
        if not isinstance(item, dict):
            continue
        keyword = display_clean(str(item.get("keyword", "")))
        try:
            item_date = dt.date.fromisoformat(str(item.get("date", "")))
        except ValueError:
            continue

        if not keyword or item_date < cutoff or item_date > run_date:
            continue

        cleaned.append(item)
        key = normalise(keyword)
        if key not in latest or item_date > latest[key]:
            latest[key] = item_date

    return cleaned, latest


def save_history(
    output_dir: Path,
    existing_items: list[dict[str, Any]],
    selected: list[Candidate],
    run_date: dt.date,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cutoff = run_date - dt.timedelta(days=HISTORY_RETENTION_DAYS)

    retained: list[dict[str, Any]] = []
    for item in existing_items:
        try:
            item_date = dt.date.fromisoformat(str(item.get("date", "")))
        except ValueError:
            continue
        if cutoff <= item_date < run_date:
            retained.append(item)

    retained.extend({
        "date": run_date.isoformat(),
        "keyword": candidate.keyword,
        "score": candidate.score,
        "action": candidate.action,
    } for candidate in selected)

    path = output_dir / "history.json"
    path.write_text(
        json.dumps({"version": 1, "items": retained}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def prune_old_reports(output_dir: Path, run_date: dt.date) -> None:
    cutoff = run_date - dt.timedelta(days=HISTORY_RETENTION_DAYS)
    for path in output_dir.glob("seo_report_20??-??-??.*"):
        date_text = path.stem.replace("seo_report_", "")
        try:
            file_date = dt.date.fromisoformat(date_text)
        except ValueError:
            continue
        if file_date < cutoff:
            try:
                path.unlink()
            except OSError:
                pass


def write_csv_report(
    selected: list[Candidate],
    dated_path: Path,
    latest_path: Path,
) -> None:
    fieldnames = [
        "rank", "keyword", "suggested_title", "course", "course_url", "intent",
        "content_type", "action", "priority_score", "sources", "impressions",
        "clicks", "ctr", "position", "closest_title", "closest_url",
        "similarity", "last_suggested", "history_penalty", "reason",
    ]

    with dated_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, item in enumerate(selected, start=1):
            writer.writerow({
                "rank": rank,
                "keyword": item.keyword,
                "suggested_title": item.suggested_title,
                "course": item.course_name,
                "course_url": item.course_url,
                "intent": item.intent,
                "content_type": item.content_type,
                "action": item.action,
                "priority_score": item.score,
                "sources": "; ".join(sorted(item.sources)),
                "impressions": round(item.impressions, 2),
                "clicks": round(item.clicks, 2),
                "ctr": round(item.ctr, 5),
                "position": round(item.position, 2),
                "closest_title": item.closest_title,
                "closest_url": item.closest_url,
                "similarity": round(item.similarity, 3),
                "last_suggested": item.last_suggested,
                "history_penalty": item.history_penalty,
                "reason": item.reason,
            })

    latest_path.write_bytes(dated_path.read_bytes())


def write_markdown_report(
    selected: list[Candidate],
    status: dict[str, str],
    run_date: dt.date,
    dated_path: Path,
    latest_path: Path,
) -> None:
    lines = [
        f"# گزارش روزانه فرصت‌های محتوایی — {run_date.isoformat()}",
        "",
        f"- **سایت:** {SITE_NAME}",
        f"- **نشانی:** {SITE_URL}",
        "- **توضیح:** امتیازها، اولویت نسبی تولید یا به‌روزرسانی محتوا هستند و حجم جست‌وجو محسوب نمی‌شوند.",
        "",
        "## وضعیت منابع",
        "",
    ]

    for source, value in status.items():
        lines.append(f"- **{source}:** {value}")

    if selected:
        best = selected[0]
        lines.extend([
            "",
            "## پیشنهاد اصلی امروز",
            "",
            f"**{best.suggested_title}**",
            "",
            f"- کلمه کلیدی: `{best.keyword}`",
            f"- دوره مقصد: [{best.course_name}]({best.course_url})",
            f"- اقدام: {best.action}",
            f"- امتیاز اولویت: {best.score:.1f}",
            f"- دلیل: {best.reason}",
        ])

    lines.extend([
        "",
        "## فرصت‌های اولویت‌دار",
        "",
        "| رتبه | کلمه کلیدی | دوره | نیت | اقدام | امتیاز | شواهد |",
        "|---:|---|---|---|---|---:|---|",
    ])

    for rank, item in enumerate(selected, start=1):
        evidence = ", ".join(sorted(item.sources))
        if item.impressions:
            evidence += (
                f"؛ {item.impressions:.0f} imp / pos {item.position:.1f} / "
                f"CTR {item.ctr:.1%}"
            )
        lines.append(
            f"| {rank} | {md_escape(item.keyword)} | {md_escape(item.course_name)} | "
            f"{item.intent} | {item.action} | {item.score:.1f} | {md_escape(evidence)} |"
        )

    lines.extend(["", "## بریف پنج پیشنهاد اول", ""])
    for rank, item in enumerate(selected[:5], start=1):
        target = (
            item.closest_url
            if item.action != "محتوای جدید" and item.closest_url
            else item.course_url
        )
        lines.extend([
            f"### {rank}. {item.suggested_title}",
            "",
            f"- **کلمه کلیدی:** {item.keyword}",
            f"- **نوع محتوا:** {item.content_type}",
            f"- **اقدام:** {item.action}",
            f"- **صفحه هدف یا لینک داخلی:** {target}",
            f"- **دلیل:** {item.reason}",
            "- **ساختار پیشنهادی:**",
        ])
        for heading in outline_for(item):
            lines.append(f"  - {heading}")
        lines.append("")

    content = "\n".join(lines)
    dated_path.write_text(content, encoding="utf-8")
    latest_path.write_text(content, encoding="utf-8")


def write_html_report(
    selected: list[Candidate],
    status: dict[str, str],
    run_date: dt.date,
    dated_path: Path,
    latest_path: Path,
) -> None:
    status_cards = "".join(
        f"<div class='status'><strong>{html_escape(source)}</strong><span>{html_escape(value)}</span></div>"
        for source, value in status.items()
    )

    rows = []
    for rank, item in enumerate(selected, start=1):
        evidence = "، ".join(sorted(item.sources))
        metrics = ""
        if item.impressions:
            metrics = (
                f"<small>{item.impressions:.0f} نمایش | رتبه {item.position:.1f} | "
                f"CTR {item.ctr:.1%}</small>"
            )
        rows.append(
            "<tr>"
            f"<td>{rank}</td>"
            f"<td><strong>{html_escape(item.keyword)}</strong>"
            f"<div class='muted'>{html_escape(item.suggested_title)}</div></td>"
            f"<td><a href='{html_escape(item.course_url)}' target='_blank'>"
            f"{html_escape(item.course_name)}</a></td>"
            f"<td>{html_escape(item.intent)}</td>"
            f"<td>{html_escape(item.action)}</td>"
            f"<td class='score'>{item.score:.1f}</td>"
            f"<td>{html_escape(evidence)}{metrics}</td>"
            "</tr>"
        )

    briefs = []
    for rank, item in enumerate(selected[:5], start=1):
        target = (
            item.closest_url
            if item.action != "محتوای جدید" and item.closest_url
            else item.course_url
        )
        outline = "".join(f"<li>{html_escape(h)}</li>" for h in outline_for(item))
        briefs.append(
            "<article class='brief'>"
            f"<h3>{rank}. {html_escape(item.suggested_title)}</h3>"
            f"<p><b>کلمه کلیدی:</b> {html_escape(item.keyword)}</p>"
            f"<p><b>اقدام:</b> {html_escape(item.action)}</p>"
            f"<p><b>لینک داخلی:</b> <a href='{html_escape(target)}' target='_blank'>"
            f"{html_escape(target)}</a></p>"
            f"<p><b>دلیل:</b> {html_escape(item.reason)}</p>"
            f"<ol>{outline}</ol>"
            "</article>"
        )

    best_section = ""
    if selected:
        best = selected[0]
        best_section = (
            "<section class='hero'>"
            "<div class='badge'>پیشنهاد اصلی امروز</div>"
            f"<h2>{html_escape(best.suggested_title)}</h2>"
            f"<p><b>کلمه کلیدی:</b> {html_escape(best.keyword)}</p>"
            f"<p><b>دوره مقصد:</b> <a href='{html_escape(best.course_url)}' target='_blank'>"
            f"{html_escape(best.course_name)}</a></p>"
            f"<p><b>اقدام:</b> {html_escape(best.action)} | "
            f"<b>امتیاز:</b> {best.score:.1f}</p>"
            f"<p>{html_escape(best.reason)}</p>"
            "</section>"
        )

    document = f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>گزارش روزانه SEO - {run_date.isoformat()}</title>
<style>
:root {{ color-scheme: light; --bg:#f5f7fb; --card:#fff; --text:#182235; --muted:#667085; --line:#e4e7ec; --accent:#2f5bea; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Tahoma,"Segoe UI",Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.8; }}
.container {{ max-width:1280px; margin:auto; padding:28px 18px 60px; }}
h1,h2,h3 {{ line-height:1.45; }}
a {{ color:var(--accent); text-decoration:none; }}
.note {{ background:#fff7e8; border:1px solid #f5d79a; border-radius:14px; padding:13px 16px; }}
.status-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin:18px 0; }}
.status {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:14px; display:flex; flex-direction:column; gap:5px; }}
.status span,.muted,small {{ color:var(--muted); }}
.hero {{ background:linear-gradient(135deg,#ffffff,#eef3ff); border:1px solid #cdd8ff; border-radius:20px; padding:22px; margin:22px 0; box-shadow:0 8px 24px rgba(47,91,234,.08); }}
.badge {{ display:inline-block; background:#e9efff; color:#2444a7; padding:4px 10px; border-radius:999px; font-weight:700; }}
.table-wrap {{ overflow:auto; background:var(--card); border:1px solid var(--line); border-radius:16px; }}
table {{ border-collapse:collapse; width:100%; min-width:980px; }}
th,td {{ padding:12px 10px; border-bottom:1px solid var(--line); text-align:right; vertical-align:top; }}
th {{ background:#f9fafb; position:sticky; top:0; }}
.score {{ font-weight:800; font-size:1.05rem; }}
.brief {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:18px; margin:14px 0; }}
footer {{ color:var(--muted); margin-top:28px; }}
</style>
</head>
<body>
<main class="container">
<h1>گزارش روزانه فرصت‌های محتوایی</h1>
<p><b>تاریخ:</b> {run_date.isoformat()} | <b>سایت:</b> <a href="{html_escape(SITE_URL)}" target="_blank">{html_escape(SITE_NAME)}</a></p>
<p class="note">امتیازها، اولویت نسبی تولید یا به‌روزرسانی محتوا هستند و حجم جست‌وجو محسوب نمی‌شوند.</p>
<h2>وضعیت منابع</h2>
<div class="status-grid">{status_cards}</div>
{best_section}
<h2>فرصت‌های اولویت‌دار</h2>
<div class="table-wrap">
<table>
<thead><tr><th>رتبه</th><th>کلمه کلیدی و عنوان</th><th>دوره</th><th>نیت</th><th>اقدام</th><th>امتیاز</th><th>شواهد</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>
<h2>بریف پنج پیشنهاد اول</h2>
{''.join(briefs)}
<footer>ساخته‌شده با seo_keyword_bot.py — {html_escape(SITE_URL)}</footer>
</main>
</body>
</html>
"""

    dated_path.write_text(document, encoding="utf-8")
    latest_path.write_text(document, encoding="utf-8")


def write_reports(
    candidates: list[Candidate],
    status: dict[str, str],
    run_date: dt.date,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = candidates[:TOP_N]

    paths = {
        "csv": output_dir / f"seo_report_{run_date.isoformat()}.csv",
        "csv_latest": output_dir / "seo_report_latest.csv",
        "md": output_dir / f"seo_report_{run_date.isoformat()}.md",
        "md_latest": output_dir / "seo_report_latest.md",
        "html": output_dir / f"seo_report_{run_date.isoformat()}.html",
        "html_latest": output_dir / "seo_report_latest.html",
    }

    write_csv_report(selected, paths["csv"], paths["csv_latest"])
    write_markdown_report(
        selected,
        status,
        run_date,
        paths["md"],
        paths["md_latest"],
    )
    write_html_report(
        selected,
        status,
        run_date,
        paths["html"],
        paths["html_latest"],
    )

    return paths


# =============================================================================
# تلگرام و اجرای برنامه
# =============================================================================


def split_message(text: str, limit: int = 3900) -> list[str]:
    chunks: list[str] = []
    current = ""

    for line in text.splitlines():
        addition = line + "\n"
        if current and len(current) + len(addition) > limit:
            chunks.append(current.rstrip())
            current = addition
        else:
            current += addition

    if current.strip():
        chunks.append(current.rstrip())
    return chunks


def send_telegram(candidates: list[Candidate], run_date: dt.date) -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or TELEGRAM_BOT_TOKEN.strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip() or TELEGRAM_CHAT_ID.strip()

    if not token or not chat_id:
        return "غیرفعال؛ Token یا Chat ID تنظیم نشده است"

    lines = [f"گزارش روزانه SEO — {run_date.isoformat()}", ""]
    for rank, item in enumerate(candidates[:TELEGRAM_TOP_N], start=1):
        lines.extend([
            f"{rank}) {item.keyword}",
            f"عنوان: {item.suggested_title}",
            f"دوره: {item.course_name}",
            f"اقدام: {item.action} | امتیاز: {item.score:.1f}",
            "",
        ])

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        for chunk in split_message("\n".join(lines).strip()):
            payload = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": "true",
            }).encode("utf-8")
            request = urllib.request.Request(url, data=payload, method="POST")
            with urllib.request.urlopen(request, timeout=20) as response:
                response.read()
        return "ارسال شد"
    except urllib.error.HTTPError as exc:
        return f"خطای HTTP {exc.code}"
    except urllib.error.URLError:
        return "خطای اتصال"
    except Exception as exc:
        # URL را چاپ نمی‌کنیم چون token داخل آن قرار دارد.
        return f"خطا: {type(exc).__name__}"


def print_console_summary(
    candidates: list[Candidate],
    status: dict[str, str],
    paths: dict[str, Path],
    telegram_status: str,
) -> None:
    print("\n" + "=" * 78)
    print("گزارش بات کلمات کلیدی Optimization Expert")
    print("=" * 78)

    print("\nوضعیت منابع:")
    for key, value in status.items():
        print(f"- {key}: {value}")

    print("\nپیشنهادهای برتر:")
    for rank, item in enumerate(candidates[:10], start=1):
        print(
            f"{rank:>2}. {item.keyword} | {item.course_name} | "
            f"{item.action} | امتیاز {item.score:.1f}"
        )

    print("\nفایل‌های خروجی:")
    print(f"- HTML: {paths['html_latest']}")
    print(f"- CSV : {paths['csv_latest']}")
    print(f"- MD  : {paths['md_latest']}")
    print(f"- Telegram: {telegram_status}")
    print("=" * 78 + "\n")


def run_once(
    base_dir: Path,
    offline: bool = False,
    open_report: bool = OPEN_HTML_REPORT,
) -> int:
    run_date = dt.date.today()
    output_dir = base_dir / "seo_output"

    history_items, latest_history = load_history(output_dir, run_date)
    candidates, status, _ = collect_candidates(
        run_date=run_date,
        offline=offline,
        base_dir=base_dir,
        history_latest=latest_history,
    )
    status["تاریخچه"] = (
        f"{len(history_items)} رکورد قبلی"
        if history_items
        else "اولین اجرا یا بدون سابقه"
    )

    if not candidates:
        print("هیچ پیشنهاد معتبری ساخته نشد.", file=sys.stderr)
        return 1

    paths = write_reports(candidates, status, run_date, output_dir)
    save_history(output_dir, history_items, candidates[:TOP_N], run_date)
    prune_old_reports(output_dir, run_date)

    telegram_status = send_telegram(candidates, run_date)
    print_console_summary(candidates, status, paths, telegram_status)

    if open_report:
        try:
            webbrowser.open(paths["html_latest"].resolve().as_uri())
        except Exception:
            pass

    return 0


def seconds_until_next_run(run_time: str) -> float:
    try:
        hour_text, minute_text = run_time.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError as exc:
        raise ValueError("DAILY_RUN_TIME باید مانند 09:00 باشد") from exc

    now = dt.datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += dt.timedelta(days=1)
    return max(1.0, (target - now).total_seconds())


def run_daily(base_dir: Path, offline: bool, open_report: bool) -> int:
    print(f"حالت روزانه فعال شد. ساعت اجرای روزانه: {DAILY_RUN_TIME}")
    print("برای توقف برنامه Ctrl+C را بزنید.\n")

    if RUN_IMMEDIATELY_IN_DAILY_MODE:
        run_once(base_dir, offline=offline, open_report=open_report)

    try:
        while True:
            wait_seconds = seconds_until_next_run(DAILY_RUN_TIME)
            next_time = dt.datetime.now() + dt.timedelta(seconds=wait_seconds)
            print(f"اجرای بعدی: {next_time:%Y-%m-%d %H:%M}")

            # خواب در قطعات حداکثر یک‌دقیقه‌ای تا Ctrl+C سریع عمل کند.
            remaining = wait_seconds
            while remaining > 0:
                interval = min(60.0, remaining)
                time.sleep(interval)
                remaining -= interval

            run_once(base_dir, offline=offline, open_report=open_report)
    except KeyboardInterrupt:
        print("\nاجرای روزانه متوقف شد.")
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="بات مستقل پیشنهاد کلمات کلیدی برای Optimization Expert"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="بدون درخواست اینترنتی اجرا شود",
    )
    parser.add_argument(
        "--daily",
        action="store_true",
        help="پس از اجرای اولیه، هر روز در ساعت تعیین‌شده دوباره اجرا شود",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="گزارش HTML پس از اجرا در مرورگر باز نشود",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_dir = Path(__file__).resolve().parent
    daily = bool(args.daily or RUN_DAILY_LOOP)
    open_report = bool(OPEN_HTML_REPORT and not args.no_open)

    if daily:
        return run_daily(base_dir, offline=args.offline, open_report=open_report)
    return run_once(base_dir, offline=args.offline, open_report=open_report)


if __name__ == "__main__":
    raise SystemExit(main())
