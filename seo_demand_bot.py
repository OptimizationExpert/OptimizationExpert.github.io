#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بات کشف تقاضای واقعی جست‌وجو برای سایت Optimization Expert
=============================================================

این نسخه عمداً از موضوعات موجود سایت «ایده‌سازی» نمی‌کند.
موضوع فقط زمانی وارد گزارش می‌شود که حداقل از یکی از منابع بیرونی زیر
سیگنال گرفته باشد:

1) پیشنهادهای جست‌وجوی Google Search
2) پیشنهادهای جست‌وجوی YouTube
3) خروجی Google Ads Keyword Planner (اختیاری، برای حجم جست‌وجوی ماهانه)
4) خروجی Google Search Console (اختیاری، برای عبارت‌هایی که واقعاً impression گرفته‌اند)

سپس صفحات فعلی سایت بررسی می‌شوند و عبارت‌هایی که قبلاً صفحه متمرکز برایشان
وجود دارد، از فهرست «محتوای جدید» حذف و در گزارش جداگانه ثبت می‌شوند.

مزیت‌ها
-------
- بدون نیاز به نصب هیچ پکیج؛ فقط کتابخانه‌های استاندارد Python
- مناسب اجرا در Spyder و Windows
- ساخت گزارش HTML، CSV، Markdown و JSON
- باز کردن خودکار گزارش HTML در مرورگر
- ثبت تاریخچه برای تشخیص عبارت‌های جدید، پایدار و رو‌به‌رشد
- امکان اجرای یک‌باره یا اجرای روزانه
- امکان ارسال خلاصه به Telegram

اجرای معمولی:
    python seo_demand_bot.py

اجرای سبک برای آزمایش:
    python seo_demand_bot.py --budget 15

اجرای بدون اینترنت، فقط با CSVها و فایل‌های محلی سایت:
    python seo_demand_bot.py --offline

اجرای روزانه:
    python seo_demand_bot.py --daily

نکته مهم
---------
Google/YouTube Autocomplete «حجم دقیق جست‌وجو» ارائه نمی‌کنند؛ آن‌ها سیگنال
تقاضا و زبان واقعی کاربران هستند. برای عدد ماهانه، فایل خروجی Keyword Planner
را کنار این اسکریپت بگذارید. نام پیشنهادی فایل: keyword_planner.csv
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import hashlib
import html
import json
import math
import os
import random
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
# تنظیمات اصلی
# =============================================================================

SITE_URL = "https://optimizationexpert.github.io/"
SITE_NAME = "Optimization Expert"
TARGET_COUNTRY = "IR"
TARGET_LANGUAGE = "fa"

# تعداد queryهایی که در هر منبع Autocomplete بررسی می‌شود.
# هرچه بیشتر باشد، پوشش بهتر ولی زمان و تعداد درخواست بیشتر می‌شود.
QUERY_BUDGET_PER_SOURCE = 70
MAX_WORKERS = 4
REQUEST_TIMEOUT_SECONDS = 8
REQUEST_DELAY_SECONDS = 0.12
CACHE_HOURS = 16

TOP_N_NEW_CONTENT = 35
TOP_N_COVERED = 25
MIN_DEMAND_SCORE = 18.0
EXISTING_FOCUS_THRESHOLD = 0.76
MAX_SITE_PAGES = 120
HISTORY_DAYS = 120
RECOMMENDATION_COOLDOWN_DAYS = 21

OPEN_HTML_REPORT = True
RUN_DAILY_LOOP = False
DAILY_RUN_TIME = "09:00"
RUN_IMMEDIATELY_IN_DAILY_MODE = True

# اختیاری: ارسال خلاصه به تلگرام
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
TELEGRAM_TOP_N = 8

# اگر اسکریپت را داخل مخزن سایت قرار دهید، فایل‌های Markdown/HTML محلی نیز
# خودکار بررسی می‌شوند. در صورت نیاز می‌توانید مسیر را دستی وارد کنید.
LOCAL_SITE_FOLDER = ""

# فایل‌های اختیاری که کنار اسکریپت جست‌وجو می‌شوند.
KEYWORD_PLANNER_CSV_NAMES = (
    "keyword_planner.csv",
    "keyword-planner.csv",
    "Keyword Planner.csv",
    "keyword_ideas.csv",
    "Keyword ideas.csv",
)

GSC_CSV_NAMES = (
    "gsc_export.csv",
    "search_console.csv",
    "Queries.csv",
    "queries.csv",
)

socket.setdefaulttimeout(REQUEST_TIMEOUT_SECONDS)


# =============================================================================
# خوشه‌های بسیار کلی بازار هدف
# =============================================================================
# این‌ها فقط «نقطه شروع جست‌وجو» هستند و مستقیم وارد خروجی نمی‌شوند.
# خروجی باید از منبع بیرونی دریافت شده باشد.

CLUSTERS: list[dict[str, Any]] = [
    {
        "id": "modeling",
        "name": "مدل‌سازی و بهینه‌سازی",
        "course_url": "/posts/2026/06/21/optimization-modeling-course/",
        "roots": [
            "بهینه سازی",
            "مدل سازی ریاضی",
            "تحقیق در عملیات",
            "بهینه سازی در پایتون",
            "pyomo",
            "gurobi",
        ],
        "signals": [
            "بهینه سازی", "مدل سازی", "مدلسازی", "تحقیق در عملیات",
            "برنامه ریزی خطی", "برنامه ریزی عدد صحیح", "pyomo", "gurobi",
            "تابع هدف", "متغیر تصمیم", "قید", "خطی سازی", "solver",
            "optimization", "mathematical programming",
        ],
    },
    {
        "id": "vrp",
        "name": "مسیریابی و مهندسی حمل‌ونقل",
        "course_url": "/posts/2026/06/24/vrp-python-course/",
        "roots": [
            "مسیریابی خودرو",
            "مسئله مسیریابی",
            "vrp",
            "vehicle routing problem",
            "or tools",
            "لجستیک در پایتون",
        ],
        "signals": [
            "مسیریابی", "خودرو", "وسایل نقلیه", "vrp", "cvrp", "vrptw",
            "tsp", "evrp", "vehicle routing", "ortools", "or tools",
            "لجستیک", "حمل و نقل", "پنجره زمانی", "مسیر", "ناوگان",
        ],
    },
    {
        "id": "power",
        "name": "بهینه‌سازی سیستم‌های قدرت",
        "course_url": "/posts/2026/06/20/Advanced-Power-System-Course/",
        "roots": [
            "بهینه سازی سیستم قدرت",
            "پخش بار بهینه",
            "پخش بار اقتصادی",
            "optimal power flow",
            "unit commitment",
            "برنامه ریزی شبکه برق",
        ],
        "signals": [
            "سیستم قدرت", "شبکه برق", "پخش بار", "opf", "ac opf", "dc opf",
            "economic dispatch", "پخش بار اقتصادی", "unit commitment",
            "آرایش واحدها", "ptdf", "lodf", "n-1", "باتری", "ذخیره ساز",
            "توسعه شبکه", "انتقال", "توزیع", "power system", "load flow",
        ],
    },
    {
        "id": "uncertainty",
        "name": "مدل‌سازی عدم قطعیت",
        "course_url": "/posts/2026/06/23/uncertainty-modeling-course/",
        "roots": [
            "مدل سازی عدم قطعیت",
            "بهینه سازی مقاوم",
            "stochastic optimization",
            "robust optimization",
            "igdt",
            "بهینه سازی فازی",
        ],
        "signals": [
            "عدم قطعیت", "مقاوم", "robust", "تصادفی", "stochastic", "igdt",
            "فازی", "سناریو", "مونت کارلو", "chance constraint",
            "scenario reduction", "احتمالاتی", "uncertainty",
        ],
    },
]

PERSIAN_ALPHABET = tuple("ابتپثجچحخدذرزژسشصضطظعغفقکگلمنوهی")
ENGLISH_ALPHABET = tuple("abcdefghijklmnopqrstuvwxyz")

PERSIAN_QUERY_MODIFIERS = (
    "{root}",
    "آموزش {root}",
    "{root} چیست",
    "{root} چگونه",
    "{root} در پایتون",
    "{root} مثال",
    "{root} پروژه",
    "{root} کد",
    "{root} خطا",
    "{root} نرم افزار",
    "تفاوت {root}",
    "بهترین روش {root}",
    "{root} پایان نامه",
    "{root} مقاله",
)

ENGLISH_QUERY_MODIFIERS = (
    "{root}",
    "{root} python",
    "{root} example",
    "{root} tutorial",
    "{root} project",
    "{root} code",
    "{root} error",
    "{root} vs",
    "how to {root}",
    "best {root} method",
)

NEGATIVE_PATTERNS = (
    "دانلود آهنگ", "متن آهنگ", "فیلم کامل", "سریال", "بازی آنلاین",
    "قیمت خودرو", "خرید خودرو", "اینستاگرام", "تلگرام هک", "کرک نرم افزار",
    "serial key", "دانلود رایگان کتاب بدون", "پورن", "casino", "betting",
)

FA_STOPWORDS = {
    "از", "به", "در", "با", "برای", "و", "یا", "که", "را", "یک", "این",
    "آن", "روی", "بر", "تا", "های", "است", "می", "شود", "شد", "the",
    "a", "an", "of", "for", "with", "in", "to", "and", "is", "are",
}

INTENT_TERMS = {
    "سؤال آموزشی": ("چیست", "چگونه", "چطور", "چرا", "آیا", "what is", "how to"),
    "آموزش و کدنویسی": ("آموزش", "مثال", "کد", "پیاده سازی", "tutorial", "example", "code", "python"),
    "حل خطا": ("خطا", "ارور", "رفع", "error", "fix", "debug"),
    "مقایسه": ("تفاوت", "مقایسه", "بهتر", "versus", " vs "),
    "پروژه و پایان‌نامه": ("پروژه", "پایان نامه", "مقاله", "case study", "thesis"),
    "انتخاب ابزار": ("نرم افزار", "solver", "بهترین", "کتابخانه", "package", "library"),
}


# =============================================================================
# مدل داده
# =============================================================================


@dataclass
class ExistingPage:
    title: str
    url: str
    headings: list[str] = field(default_factory=list)
    description: str = ""
    body_text: str = ""
    origin: str = "live"


@dataclass
class Candidate:
    keyword: str
    clusters: dict[str, int] = field(default_factory=dict)
    sources: set[str] = field(default_factory=set)
    source_queries: dict[str, set[str]] = field(default_factory=dict)
    source_ranks: dict[str, list[int]] = field(default_factory=dict)

    monthly_searches: float = 0.0
    monthly_searches_raw: str = ""
    competition: str = ""
    planner_change: str = ""

    gsc_impressions: float = 0.0
    gsc_clicks: float = 0.0
    gsc_ctr: float = 0.0
    gsc_position: float = 0.0
    gsc_page: str = ""

    cluster_id: str = ""
    cluster_name: str = ""
    course_url: str = ""
    intent: str = ""
    suggested_title: str = ""

    existing_similarity: float = 0.0
    existing_title: str = ""
    existing_url: str = ""
    mentioned_in_body: bool = False
    action: str = "محتوای جدید"

    first_seen: str = ""
    seen_days: int = 1
    trend_status: str = "اولین مشاهده"
    rank_change: float = 0.0
    recommendation_penalty: float = 0.0

    demand_score: float = 0.0
    reason: str = ""

    def add_source(self, source: str, query: str = "", rank: int | None = None) -> None:
        self.sources.add(source)
        self.source_queries.setdefault(source, set())
        if query:
            self.source_queries[source].add(query)
        if rank is not None:
            self.source_ranks.setdefault(source, []).append(rank)

    @property
    def appearances(self) -> int:
        return sum(len(values) for values in self.source_queries.values())

    @property
    def best_rank(self) -> int:
        ranks = [rank for values in self.source_ranks.values() for rank in values]
        return min(ranks) if ranks else 0


# =============================================================================
# ابزارهای متن و فایل
# =============================================================================


def script_directory() -> Path:
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd().resolve()


def display_clean(text: Any) -> str:
    value = html.unescape(str(text or ""))
    value = value.replace("\u200f", " ").replace("\u200e", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n-|–—:،")


def normalise(text: Any) -> str:
    value = html.unescape(str(text or ""))
    value = unicodedata.normalize("NFKC", value)
    value = value.translate(str.maketrans({
        "ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه",
        "ؤ": "و", "إ": "ا", "أ": "ا", "ـ": " ", "\u200c": " ",
        "\u200f": " ", "\u200e": " ",
    }))
    value = value.lower()
    value = re.sub(r"[\u064b-\u065f\u0670]", "", value)
    value = re.sub(r"[^0-9a-z\u0600-\u06ff+.#-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    aliases = (
        ("python", "پایتون"),
        ("or tools", "ortools"),
        ("or-tools", "ortools"),
        ("مدل سازی", "مدلسازی"),
        ("بهینه سازی", "بهینهسازی"),
        ("عدم قطعیت", "عدمقطعیت"),
        ("سيستم", "سیستم"),
    )
    for old, new in aliases:
        value = value.replace(old, new)
    return re.sub(r"\s+", " ", value).strip()


def token_set(text: Any) -> set[str]:
    return {
        token
        for token in normalise(text).split()
        if len(token) > 1 and token not in FA_STOPWORDS
    }


def contains_persian(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06ff]", text))


def absolute_url(path_or_url: str) -> str:
    return urllib.parse.urljoin(SITE_URL.rstrip("/") + "/", path_or_url)


def safe_float(value: Any, default: float = 0.0) -> float:
    text = display_clean(value).replace(",", "").replace("٬", "")
    text = text.replace("٪", "%")
    if not text:
        return default
    try:
        if text.endswith("%"):
            return float(text[:-1]) / 100.0
        return float(text)
    except ValueError:
        return default


def canonical_header(value: str) -> str:
    return normalise(value).replace(" ", "").replace(".", "")


def choose_column(fieldnames: Iterable[str], aliases: Iterable[str]) -> str | None:
    mapping = {canonical_header(name): name for name in fieldnames if name}
    for alias in aliases:
        key = canonical_header(alias)
        if key in mapping:
            return mapping[key]
    return None


def parse_human_number(value: Any) -> float:
    """اعدادی مانند 1K، 10K-100K و ۱٬۰۰۰ را به عدد تقریبی تبدیل می‌کند."""
    text = display_clean(value).lower()
    if not text:
        return 0.0

    persian_digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    text = text.translate(persian_digits)
    text = text.replace("٬", "").replace(",", "")
    text = text.replace("–", "-").replace("—", "-")

    def one_number(part: str) -> float:
        part = part.strip()
        multiplier = 1.0
        if part.endswith("k"):
            multiplier = 1_000.0
            part = part[:-1]
        elif part.endswith("m"):
            multiplier = 1_000_000.0
            part = part[:-1]
        elif part.endswith("b"):
            multiplier = 1_000_000_000.0
            part = part[:-1]
        match = re.search(r"[-+]?\d+(?:\.\d+)?", part)
        return float(match.group()) * multiplier if match else 0.0

    parts = [part for part in re.split(r"\s*-\s*", text) if part.strip()]
    values = [one_number(part) for part in parts]
    values = [value for value in values if value >= 0]
    if not values:
        return 0.0
    if len(values) >= 2:
        return sum(values[:2]) / 2.0
    return values[0]


def read_text_file_flexible(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    candidates: list[str] = []
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or raw[:200].count(b"\x00") > 10:
        candidates.extend(["utf-16", "utf-16-le", "utf-16-be"])
    candidates.extend(["utf-8-sig", "utf-8", "cp1256", "latin-1"])

    for encoding in candidates:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def find_csv(base_dir: Path, names: Iterable[str]) -> Path | None:
    for name in names:
        candidate = base_dir / name
        if candidate.exists() and candidate.is_file():
            return candidate
    lower_names = {name.lower() for name in names}
    for candidate in base_dir.glob("*.csv"):
        if candidate.name.lower() in lower_names:
            return candidate
    return None


def html_escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


# =============================================================================
# شبکه و Cache
# =============================================================================


def cache_file_for(cache_dir: Path, url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.cache"


def http_get(
    url: str,
    cache_dir: Path | None = None,
    cache_hours: int = CACHE_HOURS,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
    attempts: int = 2,
    accept: str = "*/*",
) -> bytes:
    cache_path: Path | None = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_file_for(cache_dir, url)
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age <= cache_hours * 3600:
                return cache_path.read_bytes()

    last_error: Exception | None = None
    for attempt in range(attempts):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/124 Safari/537.36"
                ),
                "Accept": accept,
                "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.6",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
            if cache_path is not None:
                try:
                    cache_path.write_bytes(data)
                except OSError:
                    pass
            return data
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504}:
                break
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            last_error = exc

        if attempt + 1 < attempts:
            time.sleep(0.8 + attempt * 0.7)

    if last_error is not None:
        raise last_error
    raise RuntimeError("HTTP request failed")


def host_resolves(host: str) -> bool:
    """قبل از ساخت ده‌ها درخواست، دسترسی DNS را سریع بررسی می‌کند."""
    try:
        socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        return True
    except OSError:
        return False



# =============================================================================
# خواندن صفحات موجود سایت
# =============================================================================


class PageParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "svg", "template"}

    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.heading_level = ""
        self.skip_depth = 0
        self.title_parts: list[str] = []
        self.current_heading: list[str] = []
        self.headings: list[str] = []
        self.description = ""
        self.body_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if tag == "title":
            self.in_title = True
        elif tag in {"h1", "h2"}:
            self.heading_level = tag
            self.current_heading = []
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                if not self.description:
                    self.description = display_clean(attrs_dict.get("content", ""))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if tag == "title":
            self.in_title = False
        elif tag in {"h1", "h2"} and self.heading_level == tag:
            heading = display_clean(" ".join(self.current_heading))
            if heading:
                self.headings.append(heading)
            self.heading_level = ""
            self.current_heading = []

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        clean = display_clean(data)
        if not clean:
            return
        if self.in_title:
            self.title_parts.append(clean)
        if self.heading_level:
            self.current_heading.append(clean)
        self.body_parts.append(clean)

    @property
    def title(self) -> str:
        value = display_clean(" ".join(self.title_parts))
        return re.sub(r"\s*[|–—-]\s*Optimization Expert\s*$", "", value, flags=re.I)

    @property
    def body_text(self) -> str:
        return display_clean(" ".join(self.body_parts))[:30000]


def fetch_sitemap_urls(cache_dir: Path, status: dict[str, str]) -> list[str]:
    sitemap_url = absolute_url("/sitemap.xml")
    try:
        raw = http_get(
            sitemap_url,
            cache_dir=cache_dir,
            cache_hours=4,
            timeout=4,
            attempts=1,
            accept="application/xml,text/xml;q=0.9,*/*;q=0.5",
        )
        root = ET.fromstring(raw)
        urls: list[str] = []
        for element in root.iter():
            if element.tag.lower().endswith("loc") and element.text:
                url = display_clean(element.text)
                if url.startswith(SITE_URL.rstrip("/")):
                    urls.append(url)
        urls = list(dict.fromkeys(urls))[:MAX_SITE_PAGES]
        status["Sitemap"] = f"{len(urls)} نشانی پیدا شد"
        return urls
    except Exception as exc:
        status["Sitemap"] = f"خوانده نشد: {type(exc).__name__}"
        return []


def fetch_live_page(url: str, cache_dir: Path) -> ExistingPage | None:
    try:
        raw = http_get(
            url,
            cache_dir=cache_dir,
            cache_hours=8,
            timeout=4,
            attempts=1,
            accept="text/html,application/xhtml+xml",
        )
        parser = PageParser()
        parser.feed(raw.decode("utf-8", errors="replace"))
        if not parser.title:
            return None
        return ExistingPage(
            title=parser.title,
            url=url,
            headings=parser.headings,
            description=parser.description,
            body_text=parser.body_text,
            origin="live",
        )
    except Exception:
        return None


def detect_local_site_root(base_dir: Path) -> Path | None:
    if LOCAL_SITE_FOLDER:
        candidate = Path(LOCAL_SITE_FOLDER).expanduser().resolve()
        return candidate if candidate.exists() else None

    if (base_dir / "_config.yml").exists() or (base_dir / "_posts").exists():
        return base_dir

    possible_names = (
        "OptimizationExpert.github.io",
        "OptimizationExpert.github.io (2)",
        "optimizationexpert.github.io",
    )
    for name in possible_names:
        candidate = base_dir / name
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, flags=re.S)
    if not match:
        return {}, text

    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip().strip("'\"")
        if key in {"title", "description", "permalink"}:
            values[key] = value
    return values, text[match.end():]


def markdown_to_plain(text: str) -> tuple[list[str], str]:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    headings = [display_clean(m.group(2)) for m in re.finditer(r"^(#{1,2})\s+(.+)$", text, flags=re.M)]
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[#*_>`~]", " ", text)
    return headings, display_clean(text)[:30000]


def collect_local_pages(root: Path, status: dict[str, str]) -> list[ExistingPage]:
    excluded_dirs = {".git", "_site", "vendor", "node_modules", "seo_demand_output", ".jekyll-cache"}
    pages: list[ExistingPage] = []

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".markdown", ".html", ".htm"}:
            continue
        if any(part in excluded_dirs for part in path.parts):
            continue
        try:
            text, _ = read_text_file_flexible(path)
        except OSError:
            continue

        front, body = parse_front_matter(text)
        title = display_clean(front.get("title", ""))
        description = display_clean(front.get("description", ""))
        headings: list[str] = []
        body_text = ""

        if path.suffix.lower() in {".html", ".htm"}:
            parser = PageParser()
            try:
                parser.feed(body)
            except Exception:
                pass
            title = title or parser.title
            headings = parser.headings
            description = description or parser.description
            body_text = parser.body_text
        else:
            headings, body_text = markdown_to_plain(body)
            if not title and headings:
                title = headings[0]

        if not title:
            continue
        relative = path.relative_to(root).as_posix()
        permalink = front.get("permalink", "")
        url = absolute_url(permalink) if permalink else f"local://{relative}"
        pages.append(ExistingPage(
            title=title,
            url=url,
            headings=headings,
            description=description,
            body_text=body_text,
            origin="local",
        ))

    status["فایل‌های محلی سایت"] = f"{len(pages)} صفحه/پست خوانده شد از {root}"
    return pages


def collect_existing_pages(
    base_dir: Path,
    cache_dir: Path,
    offline: bool,
    status: dict[str, str],
) -> list[ExistingPage]:
    pages: list[ExistingPage] = []

    local_root = detect_local_site_root(base_dir)
    if local_root is not None:
        pages.extend(collect_local_pages(local_root, status))
    else:
        status["فایل‌های محلی سایت"] = "مخزن محلی کنار اسکریپت پیدا نشد"

    if offline:
        status["صفحات زنده سایت"] = "در حالت آفلاین بررسی نشد"
    elif not host_resolves(urllib.parse.urlparse(SITE_URL).hostname or ""):
        status["صفحات زنده سایت"] = "DNS/اینترنت در دسترس نبود؛ بررسی زنده رد شد"
        status["Sitemap"] = "به علت نبود دسترسی شبکه بررسی نشد"
    else:
        urls = fetch_sitemap_urls(cache_dir, status)
        live_pages: list[ExistingPage] = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_live_page, url, cache_dir): url for url in urls}
            for future in as_completed(futures):
                try:
                    page = future.result()
                    if page is not None:
                        live_pages.append(page)
                except Exception:
                    continue
        status["صفحات زنده سایت"] = f"{len(live_pages)} صفحه خوانده شد"
        pages.extend(live_pages)

    # حذف نسخه‌های تکراری محلی و زنده بر اساس عنوان
    deduped: dict[str, ExistingPage] = {}
    for page in pages:
        key = normalise(page.title)
        if not key:
            continue
        current = deduped.get(key)
        if current is None or (current.origin == "live" and page.origin == "local"):
            deduped[key] = page
    return list(deduped.values())


def focus_similarity(keyword: str, page: ExistingPage) -> tuple[float, bool]:
    target_norm = normalise(keyword)
    target_tokens = token_set(keyword)
    if not target_norm or not target_tokens:
        return 0.0, False

    focus_values = [page.title] + page.headings[:4]
    best = 0.0

    for value in focus_values:
        value_norm = normalise(value)
        value_tokens = token_set(value)
        if not value_norm or not value_tokens:
            continue

        if target_norm == value_norm:
            best = max(best, 1.0)
            continue
        if len(target_tokens) >= 3 and target_norm in value_norm:
            best = max(best, 0.96)
        if len(value_tokens) >= 3 and value_norm in target_norm:
            best = max(best, 0.90)

        seq = difflib.SequenceMatcher(None, target_norm, value_norm).ratio()
        union = target_tokens | value_tokens
        intersection = target_tokens & value_tokens
        jaccard = len(intersection) / len(union) if union else 0.0
        containment = len(intersection) / min(len(target_tokens), len(value_tokens))
        score = 0.42 * seq + 0.30 * jaccard + 0.28 * containment

        # اگر تقریباً همه واژه‌های عبارت هدف در title/H1 موجود باشند، آن صفحه
        # از نظر موضوعی متمرکز محسوب می‌شود؛ حتی اگر عنوان جمله بلندتری باشد.
        target_coverage = len(intersection) / len(target_tokens)
        if len(target_tokens) >= 3 and target_coverage >= 0.85:
            score = max(score, 0.88)
        elif len(target_tokens) >= 4 and target_coverage >= 0.70:
            score = max(score, 0.78)

        if len(target_tokens) <= 2 and target_norm not in value_norm:
            score *= 0.75
        best = max(best, score)

    # توضیح متا سیگنال ضعیف‌تری است.
    if page.description:
        desc_norm = normalise(page.description)
        desc_tokens = token_set(page.description)
        if len(target_tokens) >= 3 and target_norm in desc_norm:
            best = max(best, 0.82)
        elif desc_tokens:
            containment = len(target_tokens & desc_tokens) / len(target_tokens)
            best = max(best, containment * 0.58)

    body_norm = normalise(page.body_text)
    mentioned = bool(len(target_tokens) >= 3 and target_norm and target_norm in body_norm)
    return min(best, 1.0), mentioned


def closest_existing_page(keyword: str, pages: list[ExistingPage]) -> tuple[ExistingPage | None, float, bool]:
    best_page: ExistingPage | None = None
    best_score = 0.0
    mentioned_anywhere = False
    for page in pages:
        score, mentioned = focus_similarity(keyword, page)
        mentioned_anywhere = mentioned_anywhere or mentioned
        if score > best_score:
            best_score = score
            best_page = page
    return best_page, best_score, mentioned_anywhere


# =============================================================================
# ساخت queryهای کشف تقاضا
# =============================================================================


def build_query_pool(run_date: dt.date) -> list[tuple[dict[str, Any], str]]:
    base_items: list[tuple[dict[str, Any], str]] = []
    extra_items: list[tuple[dict[str, Any], str]] = []

    for cluster in CLUSTERS:
        for root_index, root in enumerate(cluster["roots"]):
            # query پایه برای هر root همیشه اولویت دارد.
            base_items.append((cluster, root))

            templates = PERSIAN_QUERY_MODIFIERS if contains_persian(root) else ENGLISH_QUERY_MODIFIERS
            for template in templates[1:]:
                extra_items.append((cluster, display_clean(template.format(root=root))))

            # Alphabet soup به‌صورت چرخشی؛ هر روز حروف متفاوت بررسی می‌شوند.
            alphabet = PERSIAN_ALPHABET if contains_persian(root) else ENGLISH_ALPHABET
            start = (run_date.toordinal() + root_index * 3) % len(alphabet)
            for offset in range(3):
                letter = alphabet[(start + offset) % len(alphabet)]
                extra_items.append((cluster, f"{root} {letter}"))

    # مرتب‌سازی روزانه اما قطعی برای پوشش متفاوت در روزهای مختلف.
    def daily_key(item: tuple[dict[str, Any], str]) -> str:
        payload = f"{run_date.isoformat()}|{item[0]['id']}|{normalise(item[1])}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    extra_items.sort(key=daily_key)
    pool = base_items + extra_items

    # حذف queryهای تکراری
    unique: list[tuple[dict[str, Any], str]] = []
    seen: set[str] = set()
    for cluster, query in pool:
        key = normalise(query)
        if key and key not in seen:
            seen.add(key)
            unique.append((cluster, query))
    return unique


def choose_queries(run_date: dt.date, budget: int) -> list[tuple[dict[str, Any], str]]:
    pool = build_query_pool(run_date)
    if budget <= 0 or budget >= len(pool):
        return pool

    # ابتدا حداقل یک root از هر خوشه، سپس از کل pool.
    selected: list[tuple[dict[str, Any], str]] = []
    selected_keys: set[str] = set()
    for cluster in CLUSTERS:
        root = cluster["roots"][0]
        selected.append((cluster, root))
        selected_keys.add(normalise(root))

    for item in pool:
        if len(selected) >= budget:
            break
        key = normalise(item[1])
        if key not in selected_keys:
            selected.append(item)
            selected_keys.add(key)
    return selected


def fetch_autocomplete(query: str, source: str, cache_dir: Path) -> list[str]:
    params: dict[str, str] = {
        "client": "firefox",
        "hl": TARGET_LANGUAGE,
        "gl": TARGET_COUNTRY.lower(),
        "q": query,
    }
    if source == "YouTube Autocomplete":
        params["ds"] = "yt"

    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(params)
    raw = http_get(
        url,
        cache_dir=cache_dir,
        cache_hours=CACHE_HOURS,
        timeout=5,
        attempts=1,
        accept="application/json,text/javascript,*/*;q=0.5",
    )
    data = json.loads(raw.decode("utf-8", errors="replace"))
    raw_values = data[1] if isinstance(data, list) and len(data) > 1 else []

    values: list[str] = []
    for item in raw_values:
        if isinstance(item, str):
            value = item
        elif isinstance(item, (list, tuple)) and item:
            value = str(item[0])
        else:
            continue
        value = display_clean(value)
        if value:
            values.append(value)
    return values


def is_negative_keyword(keyword: str) -> bool:
    norm = normalise(keyword)
    return any(normalise(pattern) in norm for pattern in NEGATIVE_PATTERNS)


def map_cluster(
    keyword: str,
    votes: dict[str, int] | None = None,
) -> tuple[dict[str, Any], float]:
    keyword_norm = normalise(keyword)
    keyword_tokens = token_set(keyword)
    best_cluster = CLUSTERS[0]
    best_score = -1.0

    for cluster in CLUSTERS:
        score = float((votes or {}).get(cluster["id"], 0) * 7.0)
        for signal in cluster["signals"]:
            signal_norm = normalise(signal)
            signal_tokens = token_set(signal)
            if signal_norm and signal_norm in keyword_norm:
                score += 5.0 + min(len(signal_tokens), 3)
            elif signal_tokens:
                score += len(keyword_tokens & signal_tokens) * 1.25
        for root in cluster["roots"]:
            score += len(keyword_tokens & token_set(root)) * 0.35
        if score > best_score:
            best_cluster = cluster
            best_score = score

    return best_cluster, best_score


def relevant_to_probe(keyword: str, cluster: dict[str, Any], query: str) -> bool:
    keyword_tokens = token_set(keyword)
    if not keyword_tokens:
        return False

    query_tokens = token_set(query)
    if keyword_tokens & query_tokens:
        return True

    keyword_norm = normalise(keyword)
    for signal in cluster["signals"]:
        signal_norm = normalise(signal)
        if signal_norm and signal_norm in keyword_norm:
            return True
    return False


def add_candidate(
    store: dict[str, Candidate],
    keyword: str,
    source: str,
    cluster_id: str = "",
    query: str = "",
    rank: int | None = None,
) -> Candidate | None:
    keyword = display_clean(keyword)
    key = normalise(keyword)
    if len(key) < 4 or len(key) > 180:
        return None
    if len(key.split()) > 18 or is_negative_keyword(keyword):
        return None

    candidate = store.setdefault(key, Candidate(keyword=keyword))
    candidate.add_source(source, query=query, rank=rank)
    if cluster_id:
        candidate.clusters[cluster_id] = candidate.clusters.get(cluster_id, 0) + 1
    return candidate


def collect_autocomplete(
    store: dict[str, Candidate],
    run_date: dt.date,
    cache_dir: Path,
    budget: int,
    status: dict[str, str],
) -> None:
    if not host_resolves("suggestqueries.google.com"):
        status["Google Search Autocomplete"] = "DNS/اینترنت در دسترس نبود؛ درخواست‌ها رد شدند"
        status["YouTube Autocomplete"] = "DNS/اینترنت در دسترس نبود؛ درخواست‌ها رد شدند"
        return

    query_items = choose_queries(run_date, budget)

    for source in ("Google Search Autocomplete", "YouTube Autocomplete"):
        # یک درخواست واقعی آزمایشی مانع از آن می‌شود که در اینترنت قطع یا محدود،
        # ده‌ها request منتظر timeout بمانند. نتیجه در cache ذخیره می‌شود.
        try:
            fetch_autocomplete(query_items[0][1], source, cache_dir)
        except Exception as exc:
            status[source] = f"در دسترس نبود؛ درخواست‌های بعدی رد شدند ({type(exc).__name__})"
            continue

        success = 0
        failed = 0
        accepted = 0

        def task(item: tuple[dict[str, Any], str]) -> tuple[dict[str, Any], str, list[str]]:
            cluster, query = item
            time.sleep(REQUEST_DELAY_SECONDS + random.random() * 0.08)
            return cluster, query, fetch_autocomplete(query, source, cache_dir)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(task, item): item for item in query_items}
            for future in as_completed(futures):
                cluster, query = futures[future]
                try:
                    _, _, suggestions = future.result()
                    success += 1
                except Exception:
                    failed += 1
                    continue

                for rank, suggestion in enumerate(suggestions, start=1):
                    if not relevant_to_probe(suggestion, cluster, query):
                        continue
                    if add_candidate(
                        store,
                        suggestion,
                        source=source,
                        cluster_id=cluster["id"],
                        query=query,
                        rank=rank,
                    ) is not None:
                        accepted += 1

        status[source] = (
            f"{success} query موفق، {failed} ناموفق، {accepted} مشاهده پذیرفته‌شده"
        )


# =============================================================================
# فایل Google Ads Keyword Planner
# =============================================================================


def detect_table_start(text: str, header_aliases: Iterable[str]) -> tuple[int, str]:
    lines = text.splitlines()
    aliases = tuple(normalise(alias) for alias in header_aliases)
    for index, line in enumerate(lines[:40]):
        line_norm = normalise(line)
        if any(alias and alias in line_norm for alias in aliases):
            counts = {"\t": line.count("\t"), ",": line.count(","), ";": line.count(";")}
            delimiter = max(counts, key=counts.get)
            if counts[delimiter] > 0:
                return index, delimiter
    sample = "\n".join(lines[:20])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        return 0, dialect.delimiter
    except csv.Error:
        return 0, ","


def load_keyword_planner_csv(
    path: Path,
    store: dict[str, Candidate],
    status: dict[str, str],
) -> None:
    try:
        text, encoding = read_text_file_flexible(path)
    except OSError as exc:
        status["Keyword Planner"] = f"خطا در خواندن: {exc}"
        return

    start, delimiter = detect_table_start(text, (
        "Keyword", "Keywords", "کلمه کلیدی", "عبارت کلیدی",
        "Avg. monthly searches", "میانگین جستجوهای ماهانه",
    ))
    lines = text.splitlines()[start:]
    reader = csv.DictReader(lines, delimiter=delimiter)
    fields = reader.fieldnames or []

    keyword_col = choose_column(fields, (
        "Keyword", "Keywords", "کلمه کلیدی", "عبارت کلیدی",
    ))
    volume_col = choose_column(fields, (
        "Avg. monthly searches", "Average monthly searches",
        "Avg monthly searches", "میانگین جستجوهای ماهانه",
        "میانگین جستجوی ماهانه", "حجم جستجو",
    ))
    competition_col = choose_column(fields, (
        "Competition", "رقابت", "Competition (indexed value)",
    ))
    change_col = choose_column(fields, (
        "Three month change", "YoY change", "Year over year change",
        "تغییر سه ماهه", "تغییر سالانه",
    ))

    if not keyword_col:
        status["Keyword Planner"] = "ستون Keyword پیدا نشد"
        return

    rows = 0
    accepted = 0
    for row in reader:
        rows += 1
        keyword = display_clean(row.get(keyword_col, ""))
        if not keyword:
            continue

        cluster, relevance = map_cluster(keyword)
        if relevance < 2.0:
            continue

        candidate = add_candidate(
            store,
            keyword,
            source="Google Ads Keyword Planner",
            cluster_id=cluster["id"],
        )
        if candidate is None:
            continue

        raw_volume = display_clean(row.get(volume_col, "")) if volume_col else ""
        volume = parse_human_number(raw_volume)
        if volume > candidate.monthly_searches:
            candidate.monthly_searches = volume
            candidate.monthly_searches_raw = raw_volume
        if competition_col and not candidate.competition:
            candidate.competition = display_clean(row.get(competition_col, ""))
        if change_col and not candidate.planner_change:
            candidate.planner_change = display_clean(row.get(change_col, ""))
        accepted += 1

    status["Keyword Planner"] = (
        f"{accepted} عبارت مرتبط از {rows} ردیف؛ {path.name}؛ encoding={encoding}"
    )


# =============================================================================
# فایل Google Search Console
# =============================================================================


def load_gsc_csv(
    path: Path,
    store: dict[str, Candidate],
    status: dict[str, str],
) -> None:
    try:
        text, encoding = read_text_file_flexible(path)
    except OSError as exc:
        status["Search Console"] = f"خطا در خواندن: {exc}"
        return

    start, delimiter = detect_table_start(text, (
        "Top queries", "Query", "Queries", "عبارت جستجو", "کوئری",
    ))
    reader = csv.DictReader(text.splitlines()[start:], delimiter=delimiter)
    fields = reader.fieldnames or []

    query_col = choose_column(fields, (
        "Top queries", "Query", "Queries", "Keyword", "کلمه کلیدی",
        "عبارت جستجو", "عبارت‌های برتر", "کوئری",
    ))
    clicks_col = choose_column(fields, ("Clicks", "Click", "کلیک", "کلیک‌ها"))
    impressions_col = choose_column(fields, ("Impressions", "نمایش", "نمایش‌ها"))
    ctr_col = choose_column(fields, ("CTR", "نرخ کلیک"))
    position_col = choose_column(fields, (
        "Position", "Average position", "میانگین موقعیت", "رتبه",
    ))
    page_col = choose_column(fields, ("Page", "Pages", "صفحه"))

    if not query_col:
        status["Search Console"] = "ستون Query پیدا نشد"
        return

    rows = 0
    accepted = 0
    for row in reader:
        rows += 1
        keyword = display_clean(row.get(query_col, ""))
        if not keyword:
            continue
        impressions = safe_float(row.get(impressions_col, 0.0)) if impressions_col else 0.0
        if impressions <= 0:
            continue

        cluster, relevance = map_cluster(keyword)
        if relevance < 2.0:
            continue

        candidate = add_candidate(
            store,
            keyword,
            source="Google Search Console",
            cluster_id=cluster["id"],
        )
        if candidate is None:
            continue

        candidate.gsc_impressions += impressions
        candidate.gsc_clicks += safe_float(row.get(clicks_col, 0.0)) if clicks_col else 0.0
        if ctr_col:
            candidate.gsc_ctr = max(candidate.gsc_ctr, safe_float(row.get(ctr_col, 0.0)))
        if position_col:
            position = safe_float(row.get(position_col, 0.0))
            if position > 0:
                if candidate.gsc_position <= 0:
                    candidate.gsc_position = position
                else:
                    candidate.gsc_position = (candidate.gsc_position + position) / 2.0
        if page_col and not candidate.gsc_page:
            candidate.gsc_page = display_clean(row.get(page_col, ""))
        accepted += 1

    for candidate in store.values():
        if candidate.gsc_impressions > 0:
            candidate.gsc_ctr = candidate.gsc_clicks / candidate.gsc_impressions

    status["Search Console"] = (
        f"{accepted} عبارت مرتبط از {rows} ردیف؛ {path.name}؛ encoding={encoding}"
    )


# =============================================================================
# نیت جست‌وجو، عنوان و امتیاز
# =============================================================================


def infer_intent(keyword: str) -> str:
    value = f" {normalise(keyword)} "
    scores: dict[str, int] = {}
    for intent, terms in INTENT_TERMS.items():
        scores[intent] = sum(1 for term in terms if normalise(term) in value)
    if max(scores.values(), default=0) == 0:
        return "آموزش و کدنویسی"
    return max(scores, key=scores.get)


def suggest_title(candidate: Candidate) -> str:
    keyword = display_clean(candidate.keyword)
    norm = normalise(keyword)

    if candidate.intent == "حل خطا":
        return keyword if any(term in norm for term in ("رفع", "حل", "fix")) else f"رفع {keyword}: علت‌ها و راه‌حل مرحله‌به‌مرحله"
    if candidate.intent == "مقایسه":
        return keyword if any(term in norm for term in ("تفاوت", "مقایسه")) else f"مقایسه {keyword}: تفاوت‌ها و انتخاب روش مناسب"
    if candidate.intent == "سؤال آموزشی":
        return keyword.rstrip("؟?") + "؛ توضیح ساده، مدل ریاضی و مثال"
    if candidate.intent == "پروژه و پایان‌نامه":
        return keyword if "پروژه" in norm else f"پروژه {keyword}: مدل، کد و تحلیل نتایج"
    if "آموزش" in norm:
        return keyword

    if candidate.cluster_id == "vrp":
        return f"آموزش {keyword}: مدل‌سازی و پیاده‌سازی با OR-Tools"
    if candidate.cluster_id in {"modeling", "power", "uncertainty"}:
        return f"آموزش {keyword}: مدل‌سازی و پیاده‌سازی در Python/Pyomo"
    return f"آموزش {keyword} با مثال کاربردی"


def load_history(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 2, "keywords": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 2, "keywords": {}}
    if not isinstance(data, dict) or not isinstance(data.get("keywords"), dict):
        return {"version": 2, "keywords": {}}
    return data


def apply_history(candidate: Candidate, history: dict[str, Any], run_date: dt.date) -> None:
    key = normalise(candidate.keyword)
    previous = history.get("keywords", {}).get(key)
    current_rank = candidate.best_rank

    if not isinstance(previous, dict):
        candidate.first_seen = run_date.isoformat()
        candidate.seen_days = 1
        candidate.trend_status = "جدید امروز"
        return

    candidate.first_seen = str(previous.get("first_seen", run_date.isoformat()))
    dates = [str(value) for value in previous.get("seen_dates", []) if isinstance(value, str)]
    candidate.seen_days = len(set(dates + [run_date.isoformat()]))

    previous_rank = int(previous.get("last_best_rank", 0) or 0)
    previous_appearances = int(previous.get("last_appearances", 0) or 0)
    if current_rank and previous_rank:
        candidate.rank_change = float(previous_rank - current_rank)

    if candidate.rank_change >= 2 or candidate.appearances >= previous_appearances + 3:
        candidate.trend_status = "رو‌به‌رشد"
    elif candidate.rank_change <= -3:
        candidate.trend_status = "نزولی"
    elif candidate.seen_days >= 4:
        candidate.trend_status = "تقاضای پایدار"
    else:
        candidate.trend_status = "تکرار مشاهده"

    selected_dates = []
    for value in previous.get("selected_dates", []):
        try:
            selected_dates.append(dt.date.fromisoformat(str(value)))
        except ValueError:
            continue
    if selected_dates:
        days = (run_date - max(selected_dates)).days
        if 0 <= days <= RECOMMENDATION_COOLDOWN_DAYS:
            if candidate.trend_status == "رو‌به‌رشد":
                candidate.recommendation_penalty = 6.0
            else:
                candidate.recommendation_penalty = 18.0


def source_rank_score(candidate: Candidate, source: str) -> float:
    ranks = candidate.source_ranks.get(source, [])
    if not ranks:
        return 0.0
    best = min(ranks)
    average = sum(ranks) / len(ranks)
    return max(0.0, 12.0 - best) * 1.45 + max(0.0, 10.0 - average) * 0.35


def score_candidate(candidate: Candidate, relevance: float) -> None:
    score = 0.0

    if "Google Search Autocomplete" in candidate.sources:
        score += 22.0 + source_rank_score(candidate, "Google Search Autocomplete")
    if "YouTube Autocomplete" in candidate.sources:
        score += 14.0 + source_rank_score(candidate, "YouTube Autocomplete")
    if "Google Ads Keyword Planner" in candidate.sources:
        score += 18.0
        if candidate.monthly_searches > 0:
            score += min(math.log10(candidate.monthly_searches + 1.0) * 12.0, 38.0)
    if "Google Search Console" in candidate.sources:
        score += 15.0
        score += min(math.log1p(candidate.gsc_impressions) * 3.5, 24.0)
        if 4.0 <= candidate.gsc_position <= 20.0:
            score += 7.0

    # دیده‌شدن با queryهای مختلف و منابع مستقل، تقاضای مطمئن‌تری است.
    score += min(candidate.appearances * 2.0, 22.0)
    score += max(0, len(candidate.sources) - 1) * 8.0
    score += min(relevance, 10.0)

    word_count = len(normalise(candidate.keyword).split())
    if 3 <= word_count <= 10:
        score += 5.0
    elif word_count == 2:
        score += 1.5
    elif word_count > 13:
        score -= 6.0

    if candidate.intent in {"سؤال آموزشی", "حل خطا", "مقایسه"}:
        score += 5.0

    if candidate.trend_status == "جدید امروز":
        score += 2.0
    elif candidate.trend_status == "رو‌به‌رشد":
        score += 10.0
    elif candidate.trend_status == "تقاضای پایدار":
        score += 7.0
    elif candidate.trend_status == "نزولی":
        score -= 5.0

    if candidate.existing_similarity >= EXISTING_FOCUS_THRESHOLD:
        candidate.action = "قبلاً پوشش داده شده"
    elif candidate.existing_similarity >= 0.58:
        candidate.action = "محتوای مکمل با زاویه دقیق‌تر"
        score -= 5.0
    else:
        candidate.action = "محتوای جدید"
        score += 5.0

    score -= candidate.recommendation_penalty
    candidate.demand_score = round(max(0.0, min(score, 100.0)), 1)


def build_reason(candidate: Candidate) -> str:
    reasons: list[str] = []

    if "Google Search Autocomplete" in candidate.sources:
        ranks = candidate.source_ranks.get("Google Search Autocomplete", [])
        best = min(ranks) if ranks else 0
        reasons.append(f"پیشنهاد Google Search؛ بهترین جایگاه {best}")
    if "YouTube Autocomplete" in candidate.sources:
        ranks = candidate.source_ranks.get("YouTube Autocomplete", [])
        best = min(ranks) if ranks else 0
        reasons.append(f"پیشنهاد YouTube؛ بهترین جایگاه {best}")
    if candidate.monthly_searches > 0:
        reasons.append(f"میانگین جست‌وجوی ماهانه تقریبی {candidate.monthly_searches:,.0f}")
    elif "Google Ads Keyword Planner" in candidate.sources:
        reasons.append("در خروجی Keyword Planner دیده شده است")
    if candidate.gsc_impressions > 0:
        reasons.append(
            f"Search Console: {candidate.gsc_impressions:,.0f} نمایش، رتبه {candidate.gsc_position:.1f}"
        )
    if candidate.appearances > 1:
        reasons.append(f"با {candidate.appearances} query اکتشافی ظاهر شده است")
    if candidate.trend_status:
        reasons.append(candidate.trend_status)

    if candidate.action == "قبلاً پوشش داده شده" and candidate.existing_title:
        reasons.append(f"نزدیک به صفحه «{candidate.existing_title}»")
    elif candidate.mentioned_in_body:
        reasons.append("در متن سایت اشاره شده، اما صفحه متمرکز مشابه پیدا نشد")
    else:
        reasons.append("صفحه متمرکز مشابه در سایت پیدا نشد")

    return "؛ ".join(reasons)


def outline_for(candidate: Candidate) -> list[str]:
    keyword = candidate.keyword
    if candidate.intent == "حل خطا":
        return [
            f"نشانه‌ها و شرایط رخ‌دادن خطای «{keyword}»",
            "علت اصلی و روش تشخیص مرحله‌به‌مرحله",
            "راه‌حل سریع و سپس راه‌حل اصولی",
            "نمونه کد قبل و بعد از اصلاح",
            "خطاهای مشابه و روش جلوگیری از تکرار",
        ]
    if candidate.intent == "مقایسه":
        return [
            f"تعریف گزینه‌های مطرح‌شده در «{keyword}»",
            "مقایسه مفروضات، قابلیت‌ها و محدودیت‌ها",
            "مقایسه زمان حل و کیفیت پاسخ با یک مثال مشترک",
            "جدول تصمیم‌گیری برای انتخاب روش مناسب",
            "نمونه پیاده‌سازی و نتیجه‌گیری عملی",
        ]
    if candidate.intent == "سؤال آموزشی":
        return [
            f"پاسخ مستقیم و کوتاه به «{keyword}»",
            "تعریف اجزای مدل و منطق مسئله",
            "یک مثال عددی کوچک و قابل‌فهم",
            "پیاده‌سازی در پایتون",
            "تمرین توسعه‌ای و خطاهای رایج",
        ]
    return [
        f"مسئله و کاربرد واقعی {keyword}",
        "مجموعه‌ها، پارامترها، متغیرها، تابع هدف و قیود",
        "پیاده‌سازی مرحله‌به‌مرحله در پایتون",
        "تحلیل نتیجه و اعتبارسنجی مدل",
        "تمرین توسعه‌ای و لینک به دوره مرتبط",
    ]


# =============================================================================
# پردازش نهایی و حذف محتوای موجود
# =============================================================================


def candidate_signature(text: str) -> str:
    generic = {
        "آموزش", "پایتون", "مثال", "کد", "کامل", "پروژه", "چیست", "فارسی",
        "گام", "با", "در", "و", "راهنما", "tutorial", "example", "code",
    }
    tokens = [token for token in normalise(text).split() if token not in generic]
    return " ".join(tokens)


def deduplicate_candidates(candidates: list[Candidate], limit: int) -> list[Candidate]:
    selected: list[Candidate] = []
    signatures: set[str] = set()

    for candidate in candidates:
        signature = candidate_signature(candidate.keyword)
        if signature and signature in signatures:
            continue

        duplicate = False
        for previous in selected:
            left = normalise(candidate.keyword)
            right = normalise(previous.keyword)
            sequence = difflib.SequenceMatcher(None, left, right).ratio()
            left_tokens = token_set(candidate.keyword)
            right_tokens = token_set(previous.keyword)
            union = left_tokens | right_tokens
            jaccard = len(left_tokens & right_tokens) / len(union) if union else 0.0
            if sequence >= 0.90 or jaccard >= 0.84:
                duplicate = True
                break
        if duplicate:
            continue

        selected.append(candidate)
        if signature:
            signatures.add(signature)
        if len(selected) >= limit:
            break
    return selected


def finalise_candidates(
    store: dict[str, Candidate],
    pages: list[ExistingPage],
    history: dict[str, Any],
    run_date: dt.date,
) -> tuple[list[Candidate], list[Candidate], list[Candidate]]:
    processed: list[Candidate] = []

    for candidate in store.values():
        # شرط کلیدی: هیچ seed داخلی به‌تنهایی وجود ندارد؛ تمام candidateها باید
        # حداقل یک منبع بیرونی داشته باشند.
        if not candidate.sources:
            continue

        cluster, relevance = map_cluster(candidate.keyword, candidate.clusters)
        if relevance < 2.0:
            continue

        candidate.cluster_id = cluster["id"]
        candidate.cluster_name = cluster["name"]
        candidate.course_url = absolute_url(cluster["course_url"])
        candidate.intent = infer_intent(candidate.keyword)

        page, similarity, mentioned = closest_existing_page(candidate.keyword, pages)
        candidate.existing_similarity = similarity
        candidate.mentioned_in_body = mentioned
        if page is not None:
            candidate.existing_title = page.title
            candidate.existing_url = page.url

        apply_history(candidate, history, run_date)
        candidate.suggested_title = suggest_title(candidate)
        score_candidate(candidate, relevance)
        candidate.reason = build_reason(candidate)
        processed.append(candidate)

    processed.sort(
        key=lambda item: (
            -item.demand_score,
            -item.monthly_searches,
            -item.gsc_impressions,
            item.best_rank if item.best_rank else 99,
            normalise(item.keyword),
        )
    )

    new_content = [
        item for item in processed
        if item.action != "قبلاً پوشش داده شده" and item.demand_score >= MIN_DEMAND_SCORE
    ]
    covered = [
        item for item in processed
        if item.action == "قبلاً پوشش داده شده"
    ]

    new_content = deduplicate_candidates(new_content, TOP_N_NEW_CONTENT)
    covered = deduplicate_candidates(covered, TOP_N_COVERED)
    return new_content, covered, processed


# =============================================================================
# ذخیره تاریخچه
# =============================================================================


def update_history(
    history: dict[str, Any],
    all_candidates: list[Candidate],
    selected: list[Candidate],
    run_date: dt.date,
    path: Path,
) -> None:
    keywords = history.setdefault("keywords", {})
    selected_keys = {normalise(item.keyword) for item in selected}
    cutoff = run_date - dt.timedelta(days=HISTORY_DAYS)

    for candidate in all_candidates:
        key = normalise(candidate.keyword)
        entry = keywords.setdefault(key, {
            "keyword": candidate.keyword,
            "first_seen": run_date.isoformat(),
            "seen_dates": [],
            "selected_dates": [],
        })
        entry["keyword"] = candidate.keyword
        entry.setdefault("first_seen", run_date.isoformat())

        dates = []
        for value in entry.get("seen_dates", []):
            try:
                date_value = dt.date.fromisoformat(str(value))
            except ValueError:
                continue
            if date_value >= cutoff:
                dates.append(date_value.isoformat())
        dates.append(run_date.isoformat())
        entry["seen_dates"] = sorted(set(dates))

        selected_dates = []
        for value in entry.get("selected_dates", []):
            try:
                date_value = dt.date.fromisoformat(str(value))
            except ValueError:
                continue
            if date_value >= cutoff:
                selected_dates.append(date_value.isoformat())
        if key in selected_keys:
            selected_dates.append(run_date.isoformat())
        entry["selected_dates"] = sorted(set(selected_dates))

        entry["last_seen"] = run_date.isoformat()
        entry["last_best_rank"] = candidate.best_rank
        entry["last_appearances"] = candidate.appearances
        entry["last_score"] = candidate.demand_score
        entry["last_sources"] = sorted(candidate.sources)

    # حذف رکوردهای خیلی قدیمی
    for key in list(keywords):
        entry = keywords[key]
        try:
            last_seen = dt.date.fromisoformat(str(entry.get("last_seen", "")))
        except ValueError:
            last_seen = cutoff
        if last_seen < cutoff:
            del keywords[key]

    history["version"] = 2
    history["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


# =============================================================================
# گزارش‌ها
# =============================================================================


def source_label(candidate: Candidate) -> str:
    labels = {
        "Google Search Autocomplete": "Google Search",
        "YouTube Autocomplete": "YouTube",
        "Google Ads Keyword Planner": "Keyword Planner",
        "Google Search Console": "Search Console",
    }
    return "، ".join(labels.get(source, source) for source in sorted(candidate.sources))


def write_new_content_csv(items: list[Candidate], path: Path) -> None:
    fields = [
        "rank", "keyword", "suggested_title", "cluster", "intent", "action",
        "demand_score", "trend", "sources", "appearances", "best_rank",
        "monthly_searches", "monthly_searches_raw", "competition", "planner_change",
        "gsc_impressions", "gsc_clicks", "gsc_ctr", "gsc_position",
        "existing_similarity", "existing_title", "existing_url", "mentioned_in_body",
        "course_url", "reason", "discovery_queries",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, item in enumerate(items, start=1):
            discovery_queries = []
            for source, queries in item.source_queries.items():
                for query in sorted(queries):
                    discovery_queries.append(f"{source}: {query}")
            writer.writerow({
                "rank": rank,
                "keyword": item.keyword,
                "suggested_title": item.suggested_title,
                "cluster": item.cluster_name,
                "intent": item.intent,
                "action": item.action,
                "demand_score": item.demand_score,
                "trend": item.trend_status,
                "sources": source_label(item),
                "appearances": item.appearances,
                "best_rank": item.best_rank,
                "monthly_searches": round(item.monthly_searches, 2),
                "monthly_searches_raw": item.monthly_searches_raw,
                "competition": item.competition,
                "planner_change": item.planner_change,
                "gsc_impressions": round(item.gsc_impressions, 2),
                "gsc_clicks": round(item.gsc_clicks, 2),
                "gsc_ctr": round(item.gsc_ctr, 5),
                "gsc_position": round(item.gsc_position, 2),
                "existing_similarity": round(item.existing_similarity, 3),
                "existing_title": item.existing_title,
                "existing_url": item.existing_url,
                "mentioned_in_body": item.mentioned_in_body,
                "course_url": item.course_url,
                "reason": item.reason,
                "discovery_queries": " | ".join(discovery_queries),
            })


def write_covered_csv(items: list[Candidate], path: Path) -> None:
    fields = [
        "rank", "keyword", "demand_score", "sources", "monthly_searches",
        "gsc_impressions", "existing_similarity", "existing_title", "existing_url",
        "reason",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, item in enumerate(items, start=1):
            writer.writerow({
                "rank": rank,
                "keyword": item.keyword,
                "demand_score": item.demand_score,
                "sources": source_label(item),
                "monthly_searches": round(item.monthly_searches, 2),
                "gsc_impressions": round(item.gsc_impressions, 2),
                "existing_similarity": round(item.existing_similarity, 3),
                "existing_title": item.existing_title,
                "existing_url": item.existing_url,
                "reason": item.reason,
            })


def write_raw_json(items: list[Candidate], path: Path) -> None:
    payload = []
    for item in items:
        payload.append({
            "keyword": item.keyword,
            "sources": sorted(item.sources),
            "source_queries": {key: sorted(value) for key, value in item.source_queries.items()},
            "source_ranks": item.source_ranks,
            "cluster": item.cluster_name,
            "demand_score": item.demand_score,
            "monthly_searches": item.monthly_searches,
            "gsc_impressions": item.gsc_impressions,
            "existing_similarity": item.existing_similarity,
            "action": item.action,
            "trend": item.trend_status,
        })
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(
    new_items: list[Candidate],
    covered_items: list[Candidate],
    status: dict[str, str],
    run_date: dt.date,
    path: Path,
) -> None:
    lines = [
        f"# گزارش تقاضای جست‌وجو — {run_date.isoformat()}",
        "",
        "این گزارش فقط از سیگنال‌های بیرونی ساخته شده است؛ موضوعات داخلی سایت به‌عنوان candidate تزریق نشده‌اند.",
        "",
        "## وضعیت منابع",
        "",
    ]
    for key, value in status.items():
        lines.append(f"- **{key}:** {value}")

    lines.extend([
        "",
        "## فرصت‌های محتوای جدید",
        "",
        "| رتبه | کلمه کلیدی | خوشه | نیت | امتیاز | روند | شواهد |",
        "|---:|---|---|---|---:|---|---|",
    ])
    for rank, item in enumerate(new_items, start=1):
        evidence = source_label(item)
        if item.monthly_searches > 0:
            evidence += f"؛ ماهانه≈{item.monthly_searches:,.0f}"
        lines.append(
            f"| {rank} | {md_escape(item.keyword)} | {md_escape(item.cluster_name)} | "
            f"{md_escape(item.intent)} | {item.demand_score:.1f} | "
            f"{md_escape(item.trend_status)} | {md_escape(evidence)} |"
        )

    lines.extend(["", "## بریف پنج پیشنهاد اول", ""])
    for rank, item in enumerate(new_items[:5], start=1):
        lines.extend([
            f"### {rank}. {item.suggested_title}",
            "",
            f"- **کلمه کلیدی:** {item.keyword}",
            f"- **دلیل:** {item.reason}",
            f"- **لینک داخلی دوره:** {item.course_url}",
            "- **ساختار پیشنهادی:**",
        ])
        for heading in outline_for(item):
            lines.append(f"  - {heading}")
        lines.append("")

    lines.extend([
        "## موارد حذف‌شده چون قبلاً صفحه متمرکز دارند",
        "",
        "| عبارت دارای تقاضا | صفحه موجود | شباهت | شواهد |",
        "|---|---|---:|---|",
    ])
    for item in covered_items:
        title = item.existing_title or "صفحه موجود"
        url = item.existing_url
        link = f"[{title}]({url})" if url.startswith("http") else title
        lines.append(
            f"| {md_escape(item.keyword)} | {md_escape(link)} | "
            f"{item.existing_similarity:.0%} | {md_escape(source_label(item))} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_source_badges(item: Candidate) -> str:
    labels = {
        "Google Search Autocomplete": "Google Search",
        "YouTube Autocomplete": "YouTube",
        "Google Ads Keyword Planner": "Keyword Planner",
        "Google Search Console": "Search Console",
    }
    return " ".join(
        f'<span class="badge">{html_escape(labels.get(source, source))}</span>'
        for source in sorted(item.sources)
    )


def write_html(
    new_items: list[Candidate],
    covered_items: list[Candidate],
    status: dict[str, str],
    run_date: dt.date,
    path: Path,
) -> None:
    status_html = "".join(
        f"<li><strong>{html_escape(key)}:</strong> {html_escape(value)}</li>"
        for key, value in status.items()
    )

    cards = []
    for rank, item in enumerate(new_items[:8], start=1):
        volume = (
            f'<div><span class="label">جست‌وجوی ماهانه:</span> {item.monthly_searches:,.0f}</div>'
            if item.monthly_searches > 0
            else '<div><span class="label">حجم ماهانه:</span> فایل Keyword Planner موجود نیست/عدد ندارد</div>'
        )
        cards.append(f"""
        <article class="card">
          <div class="rank">{rank}</div>
          <div class="score">امتیاز تقاضا: {item.demand_score:.1f}</div>
          <h3>{html_escape(item.suggested_title)}</h3>
          <p class="keyword">کلمه کلیدی: <code>{html_escape(item.keyword)}</code></p>
          <div class="badges">{render_source_badges(item)}</div>
          <div class="meta">
            <div><span class="label">خوشه:</span> {html_escape(item.cluster_name)}</div>
            <div><span class="label">نیت:</span> {html_escape(item.intent)}</div>
            <div><span class="label">روند:</span> {html_escape(item.trend_status)}</div>
            <div><span class="label">تعداد ظهور:</span> {item.appearances}</div>
            {volume}
          </div>
          <p>{html_escape(item.reason)}</p>
          <details><summary>ساختار پیشنهادی مقاله</summary><ol>
            {''.join(f'<li>{html_escape(value)}</li>' for value in outline_for(item))}
          </ol></details>
        </article>
        """)

    rows = []
    for rank, item in enumerate(new_items, start=1):
        volume = f"{item.monthly_searches:,.0f}" if item.monthly_searches > 0 else "—"
        rows.append(f"""
        <tr>
          <td>{rank}</td>
          <td><strong>{html_escape(item.keyword)}</strong><br><small>{html_escape(item.suggested_title)}</small></td>
          <td>{html_escape(item.cluster_name)}</td>
          <td>{html_escape(item.intent)}</td>
          <td>{item.demand_score:.1f}</td>
          <td>{html_escape(item.trend_status)}</td>
          <td>{volume}</td>
          <td>{item.appearances}</td>
          <td>{render_source_badges(item)}</td>
          <td>{html_escape(item.action)}</td>
        </tr>
        """)

    covered_rows = []
    for item in covered_items:
        if item.existing_url.startswith("http"):
            page_link = f'<a href="{html_escape(item.existing_url)}" target="_blank">{html_escape(item.existing_title)}</a>'
        else:
            page_link = html_escape(item.existing_title)
        covered_rows.append(f"""
        <tr>
          <td>{html_escape(item.keyword)}</td>
          <td>{item.demand_score:.1f}</td>
          <td>{render_source_badges(item)}</td>
          <td>{item.existing_similarity:.0%}</td>
          <td>{page_link}</td>
        </tr>
        """)

    html_text = f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>گزارش تقاضای جست‌وجو - {run_date.isoformat()}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: Tahoma, Arial, sans-serif; background: #f5f7fb; color: #172033; line-height: 1.8; }}
  .wrap {{ max-width: 1320px; margin: auto; padding: 28px 18px 60px; }}
  .hero {{ background: white; border-radius: 18px; padding: 26px; box-shadow: 0 10px 30px rgba(22,34,61,.08); }}
  h1, h2, h3 {{ line-height: 1.45; }}
  h1 {{ margin: 0 0 8px; }}
  .notice {{ background: #fff7dd; border-right: 5px solid #e5a800; padding: 14px 16px; border-radius: 10px; margin: 18px 0; }}
  .success {{ background: #eaf8f0; border-right: 5px solid #22935c; padding: 14px 16px; border-radius: 10px; margin: 18px 0; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 16px; margin: 22px 0 34px; }}
  .card {{ position: relative; background: white; border-radius: 16px; padding: 22px; box-shadow: 0 8px 24px rgba(22,34,61,.07); border: 1px solid #e8ecf4; }}
  .rank {{ position: absolute; left: 18px; top: 15px; width: 38px; height: 38px; border-radius: 50%; background: #172033; color: white; display: grid; place-items: center; font-weight: bold; }}
  .score {{ display: inline-block; background: #e8f2ff; padding: 3px 10px; border-radius: 999px; font-weight: bold; }}
  .keyword code {{ direction: ltr; unicode-bidi: plaintext; background: #f1f3f8; padding: 3px 7px; border-radius: 6px; }}
  .badge {{ display: inline-block; background: #eef1f7; border-radius: 999px; padding: 2px 9px; margin: 2px; font-size: 12px; }}
  .meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px 12px; margin: 12px 0; font-size: 14px; }}
  .label {{ color: #5d677b; }}
  .table-wrap {{ overflow-x: auto; background: white; border-radius: 16px; box-shadow: 0 8px 24px rgba(22,34,61,.07); }}
  table {{ width: 100%; border-collapse: collapse; min-width: 1050px; }}
  th, td {{ padding: 12px 10px; border-bottom: 1px solid #edf0f5; vertical-align: top; text-align: right; }}
  th {{ background: #172033; color: white; position: sticky; top: 0; }}
  tr:hover td {{ background: #fafbfe; }}
  small {{ color: #657086; }}
  details {{ margin-top: 12px; }}
  summary {{ cursor: pointer; font-weight: bold; }}
  a {{ color: #165fbd; }}
  .empty {{ background: white; border-radius: 16px; padding: 24px; }}
  @media (max-width: 640px) {{ .meta {{ grid-template-columns: 1fr; }} .hero {{ padding: 18px; }} }}
</style>
</head>
<body>
<div class="wrap">
  <section class="hero">
    <h1>گزارش تقاضای واقعی جست‌وجو</h1>
    <p><strong>تاریخ:</strong> {run_date.isoformat()} &nbsp; | &nbsp; <strong>سایت:</strong> {html_escape(SITE_NAME)}</p>
    <div class="success"><strong>تفاوت نسخه جدید:</strong> هیچ seed یا موضوع داخلی مستقیماً در خروجی قرار نگرفته است. هر عبارت زیر حداقل یک شاهد بیرونی دارد.</div>
    <div class="notice"><strong>تفسیر عددها:</strong> «امتیاز تقاضا» یک امتیاز نسبی است. عدد جست‌وجوی ماهانه فقط زمانی معتبر است که CSV خروجی Google Ads Keyword Planner کنار اسکریپت قرار گرفته باشد.</div>
    <details open><summary>وضعیت منابع</summary><ul>{status_html}</ul></details>
  </section>

  <h2>بهترین شکاف‌های محتوایی امروز</h2>
  <div class="grid">{''.join(cards) if cards else '<div class="empty">فرصت جدیدی با شواهد کافی پیدا نشد. اتصال اینترنت یا CSVهای اختیاری را بررسی کنید.</div>'}</div>

  <h2>همه فرصت‌های محتوای جدید</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>#</th><th>کلمه و عنوان پیشنهادی</th><th>خوشه</th><th>نیت</th><th>امتیاز</th><th>روند</th><th>ماهانه</th><th>ظهور</th><th>منابع</th><th>اقدام</th></tr></thead>
    <tbody>{''.join(rows) if rows else '<tr><td colspan="10">موردی یافت نشد.</td></tr>'}</tbody>
  </table></div>

  <h2>عبارت‌های دارای تقاضا که حذف شدند چون قبلاً پوشش داده شده‌اند</h2>
  <p>این جدول دقیقاً نشان می‌دهد چه چیزهایی دوباره پیشنهاد نشده‌اند.</p>
  <div class="table-wrap"><table>
    <thead><tr><th>عبارت</th><th>امتیاز</th><th>منابع</th><th>شباهت</th><th>صفحه موجود</th></tr></thead>
    <tbody>{''.join(covered_rows) if covered_rows else '<tr><td colspan="5">مورد تکراری قابل‌توجهی پیدا نشد.</td></tr>'}</tbody>
  </table></div>
</div>
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def copy_latest(dated_path: Path, latest_path: Path) -> None:
    latest_path.write_bytes(dated_path.read_bytes())


def send_telegram(items: list[Candidate], status: dict[str, str]) -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN).strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID).strip()
    if not token or not chat_id:
        return "تنظیم نشده"
    if not items:
        return "گزارش خالی بود"

    lines = ["📈 فرصت‌های جدید محتوایی امروز", ""]
    for rank, item in enumerate(items[:TELEGRAM_TOP_N], start=1):
        volume = f" | ماهانه≈{item.monthly_searches:,.0f}" if item.monthly_searches > 0 else ""
        lines.append(f"{rank}) {item.keyword}")
        lines.append(f"امتیاز {item.demand_score:.1f} | {item.trend_status}{volume}")
        lines.append("")
    text = "\n".join(lines)[:3900]

    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            response.read()
        return "ارسال شد"
    except Exception as exc:
        return f"خطا: {type(exc).__name__}"


# =============================================================================
# اجرای کامل
# =============================================================================


def run_once(
    base_dir: Path,
    offline: bool = False,
    open_report: bool = True,
    budget: int = QUERY_BUDGET_PER_SOURCE,
) -> dict[str, Path]:
    run_date = dt.date.today()
    output_dir = base_dir / "seo_demand_output"
    cache_dir = output_dir / "cache"
    output_dir.mkdir(parents=True, exist_ok=True)

    status: dict[str, str] = {}
    store: dict[str, Candidate] = {}

    pages = collect_existing_pages(base_dir, cache_dir, offline, status)
    status["کل صفحات موجود برای مقایسه"] = str(len(pages))

    planner_path = find_csv(base_dir, KEYWORD_PLANNER_CSV_NAMES)
    if planner_path:
        load_keyword_planner_csv(planner_path, store, status)
    else:
        status["Keyword Planner"] = "فایل اختیاری پیدا نشد؛ حجم دقیق ماهانه نمایش داده نمی‌شود"

    gsc_path = find_csv(base_dir, GSC_CSV_NAMES)
    if gsc_path:
        load_gsc_csv(gsc_path, store, status)
    else:
        status["Search Console"] = "فایل اختیاری پیدا نشد"

    if offline:
        status["Google Search Autocomplete"] = "در حالت آفلاین اجرا نشد"
        status["YouTube Autocomplete"] = "در حالت آفلاین اجرا نشد"
    else:
        collect_autocomplete(store, run_date, cache_dir, budget, status)

    status["عبارت‌های خام بیرونی"] = str(len(store))

    history_path = output_dir / "demand_history.json"
    history = load_history(history_path)
    new_items, covered_items, all_items = finalise_candidates(store, pages, history, run_date)
    status["فرصت‌های جدید نهایی"] = str(len(new_items))
    status["حذف‌شده به دلیل محتوای موجود"] = str(len(covered_items))

    telegram_status = send_telegram(new_items, status)
    status["Telegram"] = telegram_status

    date_text = run_date.isoformat()
    paths = {
        "html": output_dir / f"demand_report_{date_text}.html",
        "new_csv": output_dir / f"new_content_gaps_{date_text}.csv",
        "covered_csv": output_dir / f"already_covered_{date_text}.csv",
        "markdown": output_dir / f"demand_report_{date_text}.md",
        "raw_json": output_dir / f"raw_demand_{date_text}.json",
    }

    write_new_content_csv(new_items, paths["new_csv"])
    write_covered_csv(covered_items, paths["covered_csv"])
    write_raw_json(all_items, paths["raw_json"])
    write_markdown(new_items, covered_items, status, run_date, paths["markdown"])
    write_html(new_items, covered_items, status, run_date, paths["html"])

    latest_paths = {
        "html": output_dir / "demand_report_latest.html",
        "new_csv": output_dir / "new_content_gaps_latest.csv",
        "covered_csv": output_dir / "already_covered_latest.csv",
        "markdown": output_dir / "demand_report_latest.md",
        "raw_json": output_dir / "raw_demand_latest.json",
    }
    for key, latest in latest_paths.items():
        copy_latest(paths[key], latest)

    update_history(history, all_items, new_items, run_date, history_path)

    print("\n" + "=" * 72)
    print("گزارش تقاضای جست‌وجو ساخته شد")
    print(f"فرصت محتوای جدید: {len(new_items)}")
    print(f"حذف‌شده چون قبلاً پوشش داده شده: {len(covered_items)}")
    print(f"HTML: {latest_paths['html']}")
    print(f"CSV جدیدها: {latest_paths['new_csv']}")
    print(f"CSV موارد موجود: {latest_paths['covered_csv']}")
    print("=" * 72 + "\n")

    if open_report and latest_paths["html"].exists():
        try:
            webbrowser.open(latest_paths["html"].as_uri())
        except Exception:
            pass

    return latest_paths


def parse_time(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", value)
    if not match:
        raise ValueError("DAILY_RUN_TIME باید مانند 09:00 باشد")
    hour, minute = int(match.group(1)), int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("ساعت نامعتبر است")
    return hour, minute


def run_daily_loop(base_dir: Path, offline: bool, open_report: bool, budget: int) -> None:
    hour, minute = parse_time(DAILY_RUN_TIME)
    last_run_date: dt.date | None = None

    if RUN_IMMEDIATELY_IN_DAILY_MODE:
        run_once(base_dir, offline=offline, open_report=open_report, budget=budget)
        last_run_date = dt.date.today()

    print(f"حالت روزانه فعال است؛ اجرای بعدی در ساعت {DAILY_RUN_TIME} سیستم انجام می‌شود.")
    while True:
        now = dt.datetime.now()
        if now.hour == hour and now.minute == minute and last_run_date != now.date():
            run_once(base_dir, offline=offline, open_report=open_report, budget=budget)
            last_run_date = now.date()
        time.sleep(20)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="کشف تقاضای واقعی جست‌وجو و شکاف محتوایی")
    parser.add_argument("--offline", action="store_true", help="عدم استفاده از اینترنت")
    parser.add_argument("--daily", action="store_true", help="اجرای مداوم روزانه")
    parser.add_argument("--no-open", action="store_true", help="گزارش HTML را خودکار باز نکن")
    parser.add_argument(
        "--budget",
        type=int,
        default=QUERY_BUDGET_PER_SOURCE,
        help="تعداد queryهای اکتشافی برای هر منبع Autocomplete",
    )
    parser.add_argument(
        "--output-base",
        default="",
        help="پوشه پایه خروجی؛ پیش‌فرض کنار فایل پایتون",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    # parse_known_args برای سازگاری بهتر با Spyder/Jupyter
    args, _unknown = parser.parse_known_args()

    base_dir = Path(args.output_base).expanduser().resolve() if args.output_base else script_directory()
    open_report = OPEN_HTML_REPORT and not args.no_open
    daily = bool(args.daily or RUN_DAILY_LOOP)
    budget = max(4, int(args.budget))

    try:
        if daily:
            run_daily_loop(base_dir, offline=args.offline, open_report=open_report, budget=budget)
        else:
            run_once(base_dir, offline=args.offline, open_report=open_report, budget=budget)
        return 0
    except KeyboardInterrupt:
        print("اجرای برنامه توسط کاربر متوقف شد.")
        return 130
    except Exception as exc:
        print(f"خطای پیش‌بینی‌نشده: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
