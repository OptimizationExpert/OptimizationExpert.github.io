#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO Opportunity Bot v3 for OptimizationExpert.github.io
========================================================

هدف این نسخه:
- پایش مستقیم و روزانه تمام کلمات تأییدشده در APPROVED_KEYWORDS؛
- کشف عبارت‌هایی که کاربران واقعاً در چند منبع بیرونی می‌نویسند؛
- جداکردن «شاهد تقاضا» از «حجم جست‌وجوی ماهانه»؛
- پیدا کردن شکاف محتوایی واقعی نسبت به تمام صفحه‌های سایت؛
- جلوگیری از بالا رفتن مصنوعی امتیاز بر اثر تکرار seedهای مشابه؛
- ساخت صف محتوای روزانه، گزارش HTML/CSV/Markdown و خلاصه تلگرام؛
- اجرای یک‌باره و زمان‌بندی با Windows Task Scheduler.

منابع رایگان پیش‌فرض:
1) Google Search autocomplete
2) YouTube autocomplete
3) Bing autocomplete
4) DuckDuckGo autocomplete
5) Stack Overflow / Operations Research Stack Exchange

منابع اختیاری و قوی‌تر:
6) Google Search Console API یا CSV
7) Google Ads Keyword Planner CSV
8) Serper API برای People Also Ask، Related Searches و برآورد رقابت SERP

نکته مهم:
این برنامه «حجم ماهانه» را حدس نمی‌زند. فقط وقتی Keyword Planner یا داده معتبر
مشابه وجود داشته باشد، عدد ماهانه نشان می‌دهد. در غیر این صورت از عبارت
«شاهد تقاضا» استفاده می‌کند.

اجرای معمولی:
    python seo_opportunity_bot_v2.py

اجرای سریع برای تست:
    python seo_opportunity_bot_v2.py --quick

اجرای آفلاین با CSVها و فایل‌های سایت:
    python seo_opportunity_bot_v2.py --offline

نصب اجرای روزانه در Windows Task Scheduler:
    python seo_opportunity_bot_v2.py --install-task 09:00

حذف Task روزانه:
    python seo_opportunity_bot_v2.py --remove-task
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import difflib
import gzip
import hashlib
import html
import json
import math
import mimetypes
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


# =============================================================================
# تنظیمات و پیکربندی
# =============================================================================

SCRIPT_VERSION = "5.1.0"
DEFAULT_CONFIG: dict[str, Any] = {
    "site_url": "https://optimizationexpert.github.io/",
    "site_name": "Optimization Expert",
    "target_country": "IR",
    "target_language": "fa",
    "target_market": "fa-IR",
    "local_site_folder": "",
    "output_folder": "seo_opportunity_output",
    "open_html_report": True,
    "request_timeout_seconds": 9,
    "request_delay_seconds": 0.18,
    "max_workers": 4,
    "cache_hours": 10,
    "max_site_pages": 250,
    "first_hop_queries": 30,
    "monitor_approved_keywords": True,
    "second_hop_queries": 16,
    "top_opportunities": 40,
    "top_content_briefs": 10,
    "serp_checks_per_run": 12,
    "history_days": 180,
    "recommendation_cooldown_days": 14,
    "minimum_opportunity_score": 42.0,
    "existing_page_threshold": 0.78,
    "related_page_threshold": 0.58,
    "stackexchange_lookback_days": 365,
    "stackexchange_pagesize": 35,
    "serper_api_key": "",
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "telegram_top_n": 8,
    "email_to": "optimizationteamonline@gmail.com",
    "email_top_n": 12,
    "gsc_service_account_file": "",
    "gsc_site_url": "",
    "gsc_days": 56,
    "gsc_data_lag_days": 3,
    "keyword_planner_file": "",
    "gsc_csv_file": "",
}

CONFIG_FILENAME = "seo_bot_config.json"
WINDOWS_TASK_NAME = "OptimizationExpert_SEO_Opportunity_Bot"


# =============================================================================
# نقشه بازار؛ عمداً فراتر از نام دقیق دوره‌ها
# =============================================================================

CLUSTERS: list[dict[str, Any]] = [
    {
        "id": "modeling",
        "name": "مدل‌سازی و تحقیق در عملیات",
        "course_url": "/posts/2026/06/21/optimization-modeling-course/",
        "business_fit": 91,
        "gateway_seeds": [
            "بهینه سازی در پایتون",
            "تحقیق در عملیات با پایتون",
            "مدل سازی ریاضی در پایتون",
            "برنامه ریزی خطی با پایتون",
            "برنامه ریزی عدد صحیح با پایتون",
            "حل مسائل بهینه سازی با پایتون",
            "خطی سازی در بهینه سازی",
            "Big M در بهینه سازی",
            "تابع هدف و قیود",
            "linear programming python",
            "mixed integer programming python",
        ],
        "signals": [
            "بهینه سازی", "بهینه‌سازی", "مدل سازی", "مدلسازی", "تحقیق در عملیات",
            "برنامه ریزی خطی", "برنامه ریزی عدد صحیح", "lp", "milp", "mip", "nlp",
            "minlp", "تابع هدف", "متغیر تصمیم", "قید", "قیود", "خطی سازی", "big m",
            "dual", "دوگان", "shadow price", "قیمت سایه", "حساسیت", "infeasible",
            "iis", "optimization", "operations research", "mathematical programming",
            "linear programming", "integer programming", "formulation",
        ],
        "intent_bonus": {"خطا و نصب": 12, "کدنویسی": 10, "مقایسه": 7, "پروژه": 8},
    },
    {
        "id": "pyomo",
        "name": "Pyomo و Solverها",
        "course_url": "/posts/2026/06/21/optimization-modeling-course/",
        "business_fit": 96,
        "gateway_seeds": [
            "آموزش Pyomo",
            "نصب Pyomo ویندوز",
            "نصب solver برای Pyomo",
            "خطای Pyomo solver",
            "Pyomo HiGHS",
            "Pyomo GLPK",
            "Pyomo IPOPT",
            "Pyomo CBC",
            "Pyomo Gurobi",
            "Pyomo infeasible model",
            "Pyomo dual sensitivity",
            "Pyomo performance",
        ],
        "signals": [
            "pyomo", "پایومو", "solverfactory", "solver", "حل کننده", "حل‌کننده",
            "highs", "appsi", "glpk", "glpsol", "cbc", "ipopt", "gurobi", "cplex",
            "scip", "mindtpy", "pyros", "neos", "no executable found", "could not locate",
            "applicationerror", "termination condition", "infeasible", "unbounded",
            "constraintlist", "concretemodel", "abstractmodel", "value", "duals",
        ],
        "intent_bonus": {"خطا و نصب": 16, "کدنویسی": 12, "مقایسه": 9, "پروژه": 8},
    },
    {
        "id": "vrp",
        "name": "VRP، OR-Tools و لجستیک",
        "course_url": "/posts/2026/06/24/vrp-python-course/",
        "business_fit": 97,
        "gateway_seeds": [
            "آموزش OR-Tools پایتون",
            "نصب OR-Tools پایتون",
            "بهینه سازی مسیر پخش",
            "مسیریابی ناوگان پایتون",
            "مسئله مسیریابی وسایل نقلیه",
            "VRP python",
            "CVRP OR-Tools python",
            "VRPTW OR-Tools python",
            "pickup delivery OR-Tools",
            "multi depot VRP python",
            "distance matrix VRP python",
            "delivery route optimization python",
            "مسیر بهینه توزیع کالا",
        ],
        "signals": [
            "vrp", "cvrp", "vrptw", "cvrptw", "tsp", "vehicle routing",
            "مسیریابی وسایل نقلیه", "مسیریابی خودرو", "مسیریابی ناوگان", "ناوگان",
            "ortools", "or tools", "or-tools", "cp sat", "cp-sat", "routing solver",
            "routingmodel", "routingindexmanager", "addcircuit", "subtour", "زیرتور",
            "پنجره زمانی", "time window", "capacity", "ظرفیت", "pickup", "delivery",
            "تحویل", "توزیع", "لجستیک", "زنجیره تامین", "چندانباره", "multi depot",
            "split delivery", "electric vehicle routing", "inventory routing",
            "distance matrix", "osrm", "openstreetmap", "google maps api",
        ],
        "intent_bonus": {"خطا و نصب": 12, "کدنویسی": 15, "مقایسه": 8, "پروژه": 13},
    },
    {
        "id": "supply_chain",
        "name": "زنجیره تأمین و لجستیک",
        "course_url": "/posts/2026/06/24/vrp-python-course/",
        "business_fit": 95,
        "gateway_seeds": [
            "بهینه سازی زنجیره تامین با پایتون",
            "طراحی شبکه زنجیره تامین با پایتون",
            "بهینه سازی شبکه توزیع با Pyomo",
            "مکان یابی تسهیلات در پایتون",
            "انتخاب تامین کننده با مدل سازی ریاضی",
            "برنامه ریزی تولید با Pyomo",
            "مدیریت موجودی با پایتون",
            "lot sizing Pyomo",
            "inventory routing python",
            "last mile delivery optimization python",
            "green supply chain optimization",
        ],
        "signals": [
            "زنجیره تامین", "زنجیره تأمین", "supply chain", "شبکه توزیع",
            "distribution network", "facility location", "مکان یابی تسهیلات",
            "مکان یابی انبار", "warehouse location", "انتخاب تامین کننده",
            "supplier selection", "برنامه ریزی تولید", "production planning",
            "موجودی", "inventory", "eoq", "safety stock", "lot sizing",
            "inventory routing", "last mile", "آخرین مایل", "reverse logistics",
            "لجستیک معکوس", "warehouse", "انبار", "bin packing", "بارگیری",
            "green supply chain", "زنجیره تامین سبز", "carbon emission",
        ],
        "intent_bonus": {"خطا و نصب": 5, "کدنویسی": 14, "مقایسه": 9, "پروژه": 14},
    },
    {
        "id": "power",
        "name": "بهینه‌سازی سیستم قدرت",
        "course_url": "/posts/2026/06/20/Advanced-Power-System-Course/",
        "business_fit": 96,
        "gateway_seeds": [
            "پخش بار اقتصادی با پایتون",
            "economic dispatch Pyomo",
            "dynamic economic dispatch python",
            "unit commitment Pyomo",
            "آرایش بهینه واحدها پایتون",
            "DC OPF Pyomo",
            "AC OPF Pyomo",
            "optimal power flow python",
            "PTDF LODF python",
            "N-1 security Pyomo",
            "battery storage Pyomo",
            "demand response Pyomo",
            "transmission expansion planning Pyomo",
            "optimal transmission switching Pyomo",
            "volt var optimization python",
        ],
        "signals": [
            "سیستم قدرت", "شبکه برق", "پخش بار اقتصادی", "توزیع بار اقتصادی",
            "economic dispatch", "dynamic economic dispatch", "unit commitment",
            "آرایش بهینه", "در مدار قرار گرفتن", "opf", "optimal power flow",
            "dc opf", "ac opf", "پخش بار بهینه", "load flow", "power flow",
            "ptdf", "lodf", "n-1", "security constrained", "scopf", "lmp",
            "باتری", "ذخیره ساز", "energy storage", "soc", "state of charge",
            "demand response", "مدیریت مصرف", "transmission expansion", "tep",
            "optimal transmission switching", "volt var", "توان راکتیو", "اینورتر",
            "ieee 14", "ieee 30", "ieee 118", "pandapower", "pypower", "matpower",
        ],
        "intent_bonus": {"خطا و نصب": 7, "کدنویسی": 15, "مقایسه": 10, "پروژه": 14},
    },
    {
        "id": "uncertainty",
        "name": "عدم قطعیت و مدیریت ریسک",
        "course_url": "/posts/2026/06/23/uncertainty-modeling-course/",
        "business_fit": 94,
        "gateway_seeds": [
            "بهینه سازی مقاوم در پایتون",
            "robust optimization Pyomo",
            "بهینه سازی تصادفی در پایتون",
            "stochastic programming Pyomo",
            "two stage stochastic programming Pyomo",
            "scenario generation python optimization",
            "scenario reduction python",
            "chance constrained optimization Pyomo",
            "CVaR optimization Pyomo",
            "IGDT optimization python",
            "بهینه سازی فازی پایتون",
            "تفاوت robust stochastic fuzzy IGDT",
        ],
        "signals": [
            "عدم قطعیت", "عدم‌قطعیت", "uncertainty", "robust", "مقاوم", "استوار",
            "stochastic", "تصادفی", "احتمالاتی", "scenario", "سناریو",
            "scenario generation", "scenario reduction", "scenario tree",
            "two stage", "دو مرحله", "first stage", "second stage", "recourse",
            "chance constraint", "chance constrained", "cvar", "value at risk",
            "igdt", "information gap", "فازی", "fuzzy", "membership function",
            "monte carlo", "مونت کارلو", "distributionally robust", "dro",
            "budget of uncertainty", "bert simas", "pyros", "progressive hedging",
        ],
        "intent_bonus": {"خطا و نصب": 6, "کدنویسی": 15, "مقایسه": 12, "پروژه": 13},
    },
]

# این فهرست ثابت در هر اجرای روزانه مستقیماً پایش می‌شود.
# بودجه first_hop_queries فقط برای queryهای اکتشافی اضافه است و این موارد را حذف نمی‌کند.
APPROVED_KEYWORDS: dict[str, tuple[str, ...]] = {
    "modeling": (
        "آموزش Pyomo از صفر", "بهینه سازی در پایتون با Pyomo",
        "برنامه ریزی خطی در پایتون", "برنامه ریزی عدد صحیح در پایتون",
        "مدل سازی MILP با Pyomo", "فرموله سازی مسائل بهینه سازی",
        "تعریف متغیر تصمیم تابع هدف و قید", "آموزش خطی سازی در بهینه سازی",
        "روش Big-M در بهینه سازی", "خطی سازی قدرمطلق در Pyomo",
        "مدل سازی قیود منطقی در Pyomo", "انتخاب Solver مناسب برای Pyomo",
        "نصب Pyomo و HiGHS در ویندوز", "نصب IPOPT برای Pyomo در ویندوز",
        "رفع خطای No executable found for solver", "تشخیص مدل Infeasible در Pyomo",
        "تحلیل حساسیت در Pyomo", "استخراج Dual و Shadow Price در Pyomo",
        "مقایسه Pyomo و PuLP و OR-Tools", "مقایسه Gurobi و CPLEX و HiGHS",
        "بهینه سازی چندهدفه در پایتون", "رسم جبهه پارتو در پایتون",
        "روش اپسیلون قید در Pyomo",
    ),
    "uncertainty": (
        "بهینه سازی مقاوم با Pyomo", "بهینه سازی تصادفی با Pyomo",
        "برنامه ریزی تصادفی دو مرحله ای", "تولید سناریو در پایتون",
        "کاهش سناریو در پایتون", "Budget of Uncertainty در بهینه سازی مقاوم",
        "تفاوت Robust و Stochastic و IGDT",
    ),
    "supply_chain": (
        "بهینه سازی زنجیره تامین با پایتون", "طراحی شبکه زنجیره تامین با پایتون",
        "بهینه سازی شبکه توزیع با Pyomo", "مسئله مکان یابی تسهیلات در پایتون",
        "مکان یابی بهینه انبار با Pyomo", "انتخاب تامین کننده با مدل سازی ریاضی",
        "برنامه ریزی تولید با Pyomo", "برنامه ریزی تولید و توزیع یکپارچه",
        "مسئله حمل و نقل با Pyomo", "مدیریت موجودی با پایتون",
        "مدل EOQ در پایتون", "محاسبه موجودی اطمینان با پایتون",
        "بهینه سازی موجودی چند سطحی", "مسئله Lot Sizing با Pyomo",
        "بهینه سازی تحویل آخرین مایل", "بهینه سازی ناوگان حمل و نقل",
        "بهینه سازی لجستیک معکوس", "مسئله بارگیری خودرو و Bin Packing",
        "بهینه سازی چیدمان کالا در انبار", "بهینه سازی مسیر برداشت کالا در انبار",
        "زنجیره تامین سبز و کاهش انتشار کربن",
    ),
    "vrp": (
        "مسیریابی وسایل نقلیه با OR-Tools", "آموزش CVRP در پایتون",
        "آموزش VRPTW در پایتون", "مسیریابی چند انباره در پایتون",
        "مسئله Pickup and Delivery با OR-Tools", "مسئله Split Delivery VRP",
        "مسیریابی موجودی Inventory Routing", "مسیریابی خودروهای برقی در پایتون",
        "کمینه کردن تعداد خودرو در VRP", "ساخت ماتریس فاصله برای OR-Tools",
        "حذف Subtour در مسائل مسیریابی", "تفاوت AddCircuit و Routing Solver",
        "مسیریابی با پنجره زمانی و زمان سرویس",
        "بهینه سازی جمع آوری و توزیع هم زمان",
    ),
    "power": (
        "پخش بار اقتصادی با Pyomo", "پخش بار اقتصادی دینامیکی با Pyomo",
        "Unit Commitment با Pyomo", "مدل سازی هزینه راه اندازی نیروگاه",
        "قیود حداقل زمان روشن و خاموش واحدها", "مدل سازی Ramp Rate در Pyomo",
        "مدل سازی ذخیره چرخان در Unit Commitment", "DC Optimal Power Flow با Pyomo",
        "AC Optimal Power Flow با Pyomo", "مقایسه DC-OPF و AC-OPF",
        "پخش بار بهینه چند بازه ای", "Security-Constrained OPF با Pyomo",
        "تحلیل امنیت N-1 در سیستم قدرت", "محاسبه PTDF در پایتون",
        "محاسبه LODF در پایتون", "محاسبه LMP با Pyomo",
        "قیمت گذاری مکانی برق در شبکه", "مدیریت ازدحام شبکه انتقال",
        "مدل سازی باتری در Pyomo", "بهینه سازی شارژ و دشارژ باتری",
        "جایابی بهینه باتری در شبکه برق", "تعیین ظرفیت بهینه ذخیره ساز انرژی",
        "مدیریت مصرف با Pyomo", "بهینه سازی پاسخگویی بار",
        "برنامه ریزی توسعه شبکه انتقال", "سوئیچینگ بهینه خطوط انتقال",
        "بهینه سازی توان راکتیو در شبکه توزیع", "کنترل Volt VAR با اینورتر خورشیدی",
        "جایابی بهینه خازن در شبکه توزیع", "بازآرایی بهینه شبکه توزیع",
        "مدیریت انرژی ریزشبکه با Pyomo", "بهینه سازی هاب انرژی",
        "برنامه ریزی شارژ خودروهای برقی", "Stochastic Unit Commitment با Pyomo",
        "مدل سازی عدم قطعیت باد و خورشید", "کاهش Curtailment انرژی تجدیدپذیر",
        "بهینه سازی نیروگاه مجازی", "تسویه بازار برق با Pyomo",
        "پخش بار اقتصادی چندهدفه", "بهینه سازی هم زمان هزینه و انتشار آلاینده ها",
    ),
}

CLUSTER_BY_ID = {cluster["id"]: cluster for cluster in CLUSTERS}

PERSIAN_TEMPLATES = (
    "{root}",
    "آموزش {root}",
    "{root} چیست",
    "{root} با پایتون",
    "{root} مثال",
    "{root} کد",
    "{root} پروژه",
    "{root} خطا",
    "نصب {root}",
    "تفاوت {root}",
    "بهترین روش {root}",
)

ENGLISH_TEMPLATES = (
    "{root}",
    "{root} python",
    "{root} tutorial",
    "{root} example",
    "{root} code",
    "{root} error",
    "{root} installation windows",
    "{root} vs",
    "how to {root}",
    "best way to {root}",
)

PERSIAN_ALPHABET = tuple("ابتپثجچحخدذرزژسشصضطظعغفقکگلمنوهی")
ENGLISH_ALPHABET = tuple("abcdefghijklmnopqrstuvwxyz")

NEGATIVE_PATTERNS = (
    "دانلود آهنگ", "متن آهنگ", "فیلم کامل", "سریال", "بازی آنلاین", "مسیریاب نشان",
    "مسیریاب بلد", "نقشه آنلاین", "مسیر یاب گوشی", "قیمت خودرو", "خرید خودرو",
    "اینستاگرام", "هک", "کرک", "serial key", "casino", "betting", "پورن",
    "رژیم غذایی", "بهینه سازی سایت", "سئو سایت", "بهینه سازی عکس", "بهینه سازی گوشی",
    "optimizer android", "route directions", "google maps directions",
)

GENERIC_WORDS = {
    "آموزش", "راهنما", "مثال", "کد", "پایتون", "python", "پروژه", "کامل",
    "جامع", "رایگان", "چیست", "چگونه", "چطور", "روش", "بهترین", "حل", "مسئله",
    "مسائل", "با", "در", "برای", "از", "و", "یا", "the", "a", "an", "of",
    "with", "in", "to", "for", "how", "tutorial", "example", "code", "guide",
}

FA_STOPWORDS = {
    "از", "به", "در", "با", "برای", "و", "یا", "که", "را", "یک", "این", "آن",
    "روی", "بر", "تا", "های", "است", "می", "شود", "شد", "چه", "چگونه", "چطور",
    "the", "a", "an", "of", "for", "with", "in", "to", "and", "is", "are",
}

INTENT_RULES: dict[str, tuple[str, ...]] = {
    "خطا و نصب": (
        "خطا", "ارور", "رفع", "نصب", "مشکل", "پیدا نمی", "اجرا نمی", "error",
        "fix", "install", "installation", "no executable", "could not locate",
        "not found", "unavailable", "infeasible", "unbounded",
    ),
    "مقایسه": ("تفاوت", "مقایسه", "بهتر", "کدام", " vs ", "versus", "compare"),
    "کدنویسی": ("آموزش", "مثال", "کد", "پیاده سازی", "پیاده‌سازی", "python", "pyomo", "ortools", "tutorial", "example", "code"),
    "پروژه": ("پروژه", "پایان نامه", "پایان‌نامه", "case study", "thesis", "dataset", "داده"),
    "تعریف و مفهوم": ("چیست", "چرا", "what is", "definition", "مفهوم"),
}

STRONG_SERP_DOMAINS = {
    "faradars.org", "maktabkhooneh.org", "wikipedia.org", "developers.google.com",
    "pyomo.readthedocs.io", "pyomo.org", "github.com", "stackoverflow.com",
    "or.stackexchange.com", "aparat.com", "civilica.com", "sciencedirect.com",
    "ieeexplore.ieee.org", "medium.com", "donyad.com", "udemy.com",
}

STRONG_CLUSTER_ANCHORS: dict[str, tuple[str, ...]] = {
    "vrp": (
        "vehicle routing", "vrp", "cvrp", "vrptw", "tsp", "pickup delivery",
        "multi depot", "split delivery", "inventory routing", "مسیریابی وسایل نقلیه",
        "مسیریابی ناوگان", "پنجره زمانی",
    ),
    "power": (
        "economic dispatch", "پخش بار اقتصادی", "dynamic economic dispatch",
        "unit commitment", "آرایش بهینه واحدها", "optimal power flow", "dc opf",
        "ac opf", "ptdf", "lodf", "n-1", "scopf", "battery storage",
        "demand response", "transmission expansion", "optimal transmission switching",
        "volt var", "سیستم قدرت", "شبکه برق",
    ),
    "uncertainty": (
        "robust optimization", "بهینه سازی مقاوم", "stochastic optimization",
        "stochastic programming", "بهینه سازی تصادفی", "scenario generation",
        "scenario reduction", "chance constraint", "cvar", "igdt",
        "بهینه سازی فازی", "عدم قطعیت",
    ),
    "pyomo": (
        "solverfactory", "no executable found", "could not locate", "pyomo install",
        "نصب pyomo", "pyomo highs", "pyomo glpk", "pyomo ipopt", "pyomo cbc",
        "pyomo infeasible", "pyomo error", "خطای pyomo",
    ),
}

KEYWORD_PLANNER_CSV_NAMES = (
    "keyword_planner.csv", "keyword-planner.csv", "Keyword Planner.csv",
    "keyword_ideas.csv", "Keyword ideas.csv",
)

GSC_CSV_NAMES = (
    "gsc_export.csv", "search_console.csv", "Queries.csv", "queries.csv",
)


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
class Observation:
    source: str
    query: str = ""
    family: str = ""
    rank: int = 0
    url: str = ""
    date: str = ""
    value: float = 0.0
    note: str = ""


@dataclass
class Candidate:
    keyword: str
    observations: list[Observation] = field(default_factory=list)
    cluster_votes: Counter[str] = field(default_factory=Counter)

    cluster_id: str = ""
    cluster_name: str = ""
    course_url: str = ""
    intent: str = ""
    funnel: str = ""
    suggested_title: str = ""
    suggested_slug: str = ""

    monthly_searches: float = 0.0
    monthly_searches_raw: str = ""
    competition_raw: str = ""
    planner_change: str = ""

    gsc_impressions: float = 0.0
    gsc_clicks: float = 0.0
    gsc_position: float = 0.0
    gsc_previous_impressions: float = 0.0
    gsc_page: str = ""

    stack_views: float = 0.0
    stack_score: float = 0.0
    stack_questions: int = 0

    serp_checked: bool = False
    serp_exact_titles: int = 0
    serp_strong_domains: int = 0
    serp_user_domain_rank: int = 0
    serp_competition_score: float | None = None
    serp_top_titles: list[str] = field(default_factory=list)

    existing_similarity: float = 0.0
    existing_title: str = ""
    existing_url: str = ""
    mentioned_in_body: bool = False
    coverage_action: str = "محتوای جدید"

    first_seen: str = ""
    seen_days: int = 1
    trend_label: str = "جدید"
    trend_score: float = 0.0
    cooldown_penalty: float = 0.0

    demand_score: float = 0.0
    gap_score: float = 0.0
    business_fit_score: float = 0.0
    freshness_score: float = 0.0
    opportunity_score: float = 0.0
    confidence: str = "کم"
    reason: str = ""

    def add_observation(self, observation: Observation) -> None:
        key = (
            observation.source,
            normalise(observation.query),
            normalise(observation.family),
            observation.rank,
            observation.url,
            observation.note,
        )
        for current in self.observations:
            current_key = (
                current.source,
                normalise(current.query),
                normalise(current.family),
                current.rank,
                current.url,
                current.note,
            )
            if current_key == key:
                current.value = max(current.value, observation.value)
                return
        self.observations.append(observation)

    @property
    def sources(self) -> set[str]:
        return {observation.source for observation in self.observations}

    @property
    def autocomplete_sources(self) -> set[str]:
        return {
            source for source in self.sources
            if source in {
                "Google Search Autocomplete", "YouTube Autocomplete",
                "Bing Autocomplete", "DuckDuckGo Autocomplete",
                "Google SERP Related", "Google SERP PAA",
            }
        }

    @property
    def unique_families(self) -> set[str]:
        return {normalise(obs.family) for obs in self.observations if obs.family}

    @property
    def best_rank(self) -> int:
        ranks = [obs.rank for obs in self.observations if obs.rank > 0]
        return min(ranks) if ranks else 0

    @property
    def gsc_ctr(self) -> float:
        return self.gsc_clicks / self.gsc_impressions if self.gsc_impressions > 0 else 0.0


# =============================================================================
# متن، اعداد و فایل‌ها
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
    value = re.sub(r"[^0-9a-z\u0600-\u06ff+.#/-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    aliases = (
        ("or tools", "ortools"),
        ("or-tools", "ortools"),
        ("cp sat", "cpsat"),
        ("cp-sat", "cpsat"),
        ("vehicle routing problem", "vrp"),
        ("capacitated vehicle routing problem", "cvrp"),
        ("vehicle routing problem with time windows", "vrptw"),
        ("python", "پایتون"),
        ("پایومو", "pyomo"),
        ("مدل سازی", "مدلسازی"),
        ("بهینه سازی", "بهینهسازی"),
        ("عدم قطعیت", "عدمقطعیت"),
        ("حل کننده", "solver"),
        ("حل‌کننده", "solver"),
        ("سيستم", "سیستم"),
    )
    for old, new in aliases:
        value = value.replace(old, new)
    return re.sub(r"\s+", " ", value).strip()


def contains_persian(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06ff]", text))


def token_set(text: Any, remove_generic: bool = False) -> set[str]:
    values = {
        token for token in normalise(text).split()
        if len(token) > 1 and token not in FA_STOPWORDS
    }
    if remove_generic:
        generic = {normalise(word) for word in GENERIC_WORDS}
        values = {token for token in values if token not in generic}
    return values


def canonical_header(value: str) -> str:
    return normalise(value).replace(" ", "").replace(".", "")


def choose_column(fieldnames: Iterable[str], aliases: Iterable[str]) -> str | None:
    mapping = {canonical_header(name): name for name in fieldnames if name}
    for alias in aliases:
        key = canonical_header(alias)
        if key in mapping:
            return mapping[key]
    return None


def safe_float(value: Any, default: float = 0.0) -> float:
    text = display_clean(value).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    text = text.replace(",", "").replace("٬", "").replace("٪", "%")
    if not text:
        return default
    try:
        if text.endswith("%"):
            return float(text[:-1]) / 100.0
        return float(text)
    except ValueError:
        return default


def parse_human_number(value: Any) -> float:
    text = display_clean(value).lower().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    text = text.replace("٬", "").replace(",", "").replace("–", "-").replace("—", "-")
    if not text:
        return 0.0

    def parse_one(part: str) -> float:
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
    numbers = [parse_one(part) for part in parts]
    numbers = [number for number in numbers if number >= 0]
    if not numbers:
        return 0.0
    return sum(numbers[:2]) / min(len(numbers), 2)


def read_text_file_flexible(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    encodings: list[str] = []
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or raw[:200].count(b"\x00") > 10:
        encodings.extend(["utf-16", "utf-16-le", "utf-16-be"])
    encodings.extend(["utf-8-sig", "utf-8", "cp1256", "latin-1"])
    for encoding in encodings:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def html_escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def slugify(text: str) -> str:
    value = normalise(text)
    value = value.replace("پایتون", "python").replace("بهینهسازی", "optimization")
    value = re.sub(r"[^0-9a-z\u0600-\u06ff]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:90] or "seo-topic"


def absolute_url(site_url: str, path_or_url: str) -> str:
    return urllib.parse.urljoin(site_url.rstrip("/") + "/", path_or_url)


def domain_from_url(url: str) -> str:
    try:
        host = urllib.parse.urlparse(url).hostname or ""
        return host.lower().removeprefix("www.")
    except Exception:
        return ""


def is_negative_keyword(keyword: str) -> bool:
    value = normalise(keyword)
    return any(normalise(pattern) in value for pattern in NEGATIVE_PATTERNS)


def keyword_key(keyword: str) -> str:
    return normalise(keyword)


def query_family_key(root: str) -> str:
    return normalise(root)


def date_from_timestamp(value: int | float) -> dt.date:
    try:
        return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc).date()
    except Exception:
        return dt.date.today()


def merge_config(defaults: dict[str, Any], custom: dict[str, Any]) -> dict[str, Any]:
    result = dict(defaults)
    for key, value in custom.items():
        if key in result:
            result[key] = value
    return result


def load_config(base_dir: Path) -> tuple[dict[str, Any], Path]:
    path = base_dir / CONFIG_FILENAME
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
        config = dict(DEFAULT_CONFIG)
    else:
        try:
            custom = json.loads(path.read_text(encoding="utf-8"))
            config = merge_config(DEFAULT_CONFIG, custom if isinstance(custom, dict) else {})
        except (OSError, json.JSONDecodeError):
            config = dict(DEFAULT_CONFIG)

    environment_map = {
        "SERPER_API_KEY": "serper_api_key",
        "TELEGRAM_BOT_TOKEN": "telegram_bot_token",
        "TELEGRAM_CHAT_ID": "telegram_chat_id",
        "GSC_SERVICE_ACCOUNT_FILE": "gsc_service_account_file",
        "GSC_SITE_URL": "gsc_site_url",
    }
    for env_name, config_key in environment_map.items():
        if os.environ.get(env_name):
            config[config_key] = os.environ[env_name]
    return config, path


def find_file(base_dir: Path, configured: str, names: Iterable[str]) -> Path | None:
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    for name in names:
        candidate = base_dir / name
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    lower_names = {name.lower() for name in names}
    for candidate in base_dir.glob("*.csv"):
        if candidate.name.lower() in lower_names:
            return candidate.resolve()
    return None


# =============================================================================
# شبکه و Cache
# =============================================================================

def cache_path_for(cache_dir: Path, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.cache"


def http_request(
    url: str,
    *,
    cache_dir: Path | None = None,
    cache_hours: int = 10,
    timeout: int = 9,
    attempts: int = 2,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    method: str | None = None,
) -> bytes:
    cache_key = url if data is None else f"{url}|{hashlib.sha256(data).hexdigest()}"
    cache_path: Path | None = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_path_for(cache_dir, cache_key)
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age <= max(0, cache_hours) * 3600:
                return cache_path.read_bytes()

    request_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/142 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.7",
        "Accept-Encoding": "gzip",
    }
    if headers:
        request_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        request = urllib.request.Request(
            url,
            data=data,
            headers=request_headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                if response.headers.get("Content-Encoding", "").lower() == "gzip":
                    raw = gzip.decompress(raw)
            if cache_path is not None:
                try:
                    cache_path.write_bytes(raw)
                except OSError:
                    pass
            return raw
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                break
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            last_error = exc
        if attempt + 1 < attempts:
            time.sleep(0.8 + attempt * 1.0 + random.random() * 0.3)

    if last_error is not None:
        raise last_error
    raise RuntimeError("HTTP request failed")


def json_request(*args: Any, **kwargs: Any) -> Any:
    raw = http_request(*args, **kwargs)
    return json.loads(raw.decode("utf-8", errors="replace"))


# =============================================================================
# صفحات سایت
# =============================================================================

class PageParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "svg", "template"}

    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.current_heading_tag = ""
        self.skip_depth = 0
        self.title_parts: list[str] = []
        self.current_heading_parts: list[str] = []
        self.headings: list[str] = []
        self.description = ""
        self.body_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {str(key).lower(): (value or "") for key, value in attrs}
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if tag == "title":
            self.in_title = True
        elif tag in {"h1", "h2", "h3"}:
            self.current_heading_tag = tag
            self.current_heading_parts = []
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
        elif tag in {"h1", "h2", "h3"} and tag == self.current_heading_tag:
            heading = display_clean(" ".join(self.current_heading_parts))
            if heading:
                self.headings.append(heading)
            self.current_heading_tag = ""
            self.current_heading_parts = []

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        clean = display_clean(data)
        if not clean:
            return
        if self.in_title:
            self.title_parts.append(clean)
        if self.current_heading_tag:
            self.current_heading_parts.append(clean)
        self.body_parts.append(clean)

    @property
    def title(self) -> str:
        value = display_clean(" ".join(self.title_parts))
        value = re.sub(r"\s*[|–—-]\s*Optimization Expert\s*$", "", value, flags=re.I)
        return value

    @property
    def body_text(self) -> str:
        return display_clean(" ".join(self.body_parts))[:50000]


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
        if key in {"title", "seo_title", "description", "permalink", "keywords"}:
            values[key] = value
    return values, text[match.end():]


def markdown_to_plain(text: str) -> tuple[list[str], str]:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    headings = [display_clean(match.group(2)) for match in re.finditer(r"^(#{1,3})\s+(.+)$", text, flags=re.M)]
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[#*_>`~]", " ", text)
    return headings, display_clean(text)[:50000]


def detect_local_site_root(base_dir: Path, configured: str) -> Path | None:
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()

    if (base_dir / "_config.yml").exists() or (base_dir / "_posts").exists():
        return base_dir.resolve()

    candidates = [
        base_dir / "OptimizationExpert.github.io",
        base_dir / "OptimizationExpert.github.io (2)",
        base_dir.parent / "OptimizationExpert.github.io",
        Path.cwd() / "OptimizationExpert.github.io",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    return None


def collect_local_pages(root: Path, site_url: str, status: dict[str, str]) -> list[ExistingPage]:
    excluded = {".git", "_site", "vendor", "node_modules", "seo_opportunity_output", ".jekyll-cache", ".venv", "venv"}
    pages: list[ExistingPage] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".markdown", ".html", ".htm"}:
            continue
        if any(part in excluded for part in path.parts):
            continue
        try:
            text, _encoding = read_text_file_flexible(path)
        except OSError:
            continue
        front, body = parse_front_matter(text)
        title = display_clean(front.get("seo_title") or front.get("title", ""))
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
            description = description or parser.description
            headings = parser.headings
            body_text = parser.body_text
        else:
            headings, body_text = markdown_to_plain(body)
            if not title and headings:
                title = headings[0]
        if front.get("keywords"):
            body_text = f"{front['keywords']} {body_text}"
        if not title:
            continue
        relative = path.relative_to(root).as_posix()
        permalink = front.get("permalink", "")
        url = absolute_url(site_url, permalink) if permalink else f"local://{relative}"
        pages.append(ExistingPage(title, url, headings, description, body_text, "local"))
    status["فایل‌های محلی سایت"] = f"{len(pages)} صفحه از {root}"
    return pages


def fetch_sitemap_urls(
    sitemap_url: str,
    site_url: str,
    cache_dir: Path,
    config: dict[str, Any],
    seen: set[str] | None = None,
) -> list[str]:
    seen = seen or set()
    if sitemap_url in seen:
        return []
    seen.add(sitemap_url)
    raw = http_request(
        sitemap_url,
        cache_dir=cache_dir,
        cache_hours=4,
        timeout=int(config["request_timeout_seconds"]),
        attempts=2,
        headers={"Accept": "application/xml,text/xml,*/*;q=0.5"},
    )
    root = ET.fromstring(raw)
    locations = [display_clean(element.text) for element in root.iter() if element.tag.lower().endswith("loc") and element.text]
    urls: list[str] = []
    if root.tag.lower().endswith("sitemapindex"):
        for child in locations[:20]:
            try:
                urls.extend(fetch_sitemap_urls(child, site_url, cache_dir, config, seen))
            except Exception:
                continue
    else:
        site_host = domain_from_url(site_url)
        for location in locations:
            if domain_from_url(location) == site_host:
                urls.append(location)
    return list(dict.fromkeys(urls))


def fetch_live_page(url: str, cache_dir: Path, config: dict[str, Any]) -> ExistingPage | None:
    try:
        raw = http_request(
            url,
            cache_dir=cache_dir,
            cache_hours=8,
            timeout=int(config["request_timeout_seconds"]),
            attempts=1,
            headers={"Accept": "text/html,application/xhtml+xml"},
        )
        parser = PageParser()
        parser.feed(raw.decode("utf-8", errors="replace"))
        if not parser.title:
            return None
        return ExistingPage(parser.title, url, parser.headings, parser.description, parser.body_text, "live")
    except Exception:
        return None


def collect_existing_pages(
    base_dir: Path,
    cache_dir: Path,
    config: dict[str, Any],
    offline: bool,
    status: dict[str, str],
) -> list[ExistingPage]:
    site_url = str(config["site_url"])
    pages: list[ExistingPage] = []
    local_root = detect_local_site_root(base_dir, str(config.get("local_site_folder", "")))
    if local_root:
        pages.extend(collect_local_pages(local_root, site_url, status))
    else:
        status["فایل‌های محلی سایت"] = "مخزن محلی پیدا نشد"

    if offline:
        status["صفحات زنده سایت"] = "حالت آفلاین"
    else:
        sitemap_url = absolute_url(site_url, "/sitemap.xml")
        try:
            urls = fetch_sitemap_urls(sitemap_url, site_url, cache_dir, config)
            urls = urls[: int(config["max_site_pages"])]
            status["Sitemap"] = f"{len(urls)} نشانی"
            live_pages: list[ExistingPage] = []
            with ThreadPoolExecutor(max_workers=int(config["max_workers"])) as executor:
                futures = [executor.submit(fetch_live_page, url, cache_dir, config) for url in urls]
                for future in as_completed(futures):
                    page = future.result()
                    if page:
                        live_pages.append(page)
            pages.extend(live_pages)
            status["صفحات زنده سایت"] = f"{len(live_pages)} صفحه خوانده شد"
        except Exception as exc:
            status["صفحات زنده سایت"] = f"خطا: {type(exc).__name__}"

    deduped: dict[str, ExistingPage] = {}
    for page in pages:
        key = normalise(page.title)
        if not key:
            continue
        current = deduped.get(key)
        if current is None or (current.origin == "live" and page.origin == "local"):
            deduped[key] = page
    result = list(deduped.values())
    status["کل صفحات برای مقایسه"] = str(len(result))
    return result

# =============================================================================
# سنجش پوشش موجود سایت
# =============================================================================

def phrase_similarity(left: str, right: str) -> float:
    left_norm = normalise(left)
    right_norm = normalise(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0

    left_tokens = token_set(left, remove_generic=True)
    right_tokens = token_set(right, remove_generic=True)
    if not left_tokens or not right_tokens:
        return difflib.SequenceMatcher(None, left_norm, right_norm).ratio() * 0.6

    intersection = left_tokens & right_tokens
    union = left_tokens | right_tokens
    jaccard = len(intersection) / len(union) if union else 0.0
    containment = len(intersection) / min(len(left_tokens), len(right_tokens))
    target_coverage = len(intersection) / len(left_tokens)
    sequence = difflib.SequenceMatcher(None, left_norm, right_norm).ratio()

    score = 0.30 * sequence + 0.28 * jaccard + 0.28 * containment + 0.14 * target_coverage
    if len(left_tokens) >= 2 and left_norm in right_norm:
        score = max(score, 0.94)
    if len(right_tokens) >= 2 and right_norm in left_norm:
        score = max(score, 0.88)
    if len(left_tokens) >= 3 and target_coverage >= 0.85:
        score = max(score, 0.89)
    elif len(left_tokens) >= 4 and target_coverage >= 0.70:
        score = max(score, 0.78)
    return min(score, 1.0)


def focus_similarity(keyword: str, page: ExistingPage) -> tuple[float, bool]:
    values = [page.title] + page.headings[:7]
    best = max((phrase_similarity(keyword, value) for value in values if value), default=0.0)
    if page.description:
        best = max(best, phrase_similarity(keyword, page.description) * 0.76)

    keyword_norm = normalise(keyword)
    keyword_tokens = token_set(keyword, remove_generic=True)
    body_norm = normalise(page.body_text)
    mentioned = False
    if keyword_norm and len(keyword_tokens) >= 2:
        mentioned = keyword_norm in body_norm
        if not mentioned:
            body_tokens = token_set(page.body_text, remove_generic=True)
            coverage = len(keyword_tokens & body_tokens) / len(keyword_tokens)
            mentioned = coverage >= 0.80
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
# خوشه‌بندی، نیت و عنوان پیشنهادی
# =============================================================================

def map_cluster(keyword: str, votes: Counter[str] | None = None, context_cluster: str = "") -> tuple[dict[str, Any], float]:
    keyword_norm = normalise(keyword)
    keyword_tokens = token_set(keyword)
    best_cluster = CLUSTERS[0]
    best_score = -1.0

    for cluster in CLUSTERS:
        score = 0.0
        if votes:
            score += float(votes.get(cluster["id"], 0)) * 6.0
        if context_cluster == cluster["id"]:
            score += 4.0

        # عبارت‌های تخصصی باید بر نام ابزار غلبه کنند؛ مثلاً
        # «unit commitment pyomo» متعلق به خوشه سیستم قدرت است، نه صرفاً Pyomo.
        for anchor in STRONG_CLUSTER_ANCHORS.get(cluster["id"], ()):
            anchor_norm = normalise(anchor)
            if anchor_norm and anchor_norm in keyword_norm:
                score += 24.0 + min(len(token_set(anchor)), 4)

        for signal in cluster["signals"]:
            signal_norm = normalise(signal)
            signal_tokens = token_set(signal)
            if signal_norm and signal_norm in keyword_norm:
                score += 5.0 + min(len(signal_tokens), 3)
            elif signal_tokens:
                overlap = keyword_tokens & signal_tokens
                score += len(overlap) * 1.15

        for seed in cluster["gateway_seeds"]:
            score += len(keyword_tokens & token_set(seed)) * 0.25

        if score > best_score:
            best_score = score
            best_cluster = cluster
    return best_cluster, best_score


def infer_intent(keyword: str) -> str:
    value = f" {normalise(keyword)} "
    scores: dict[str, int] = {}
    for intent, terms in INTENT_RULES.items():
        scores[intent] = sum(1 for term in terms if normalise(term) in value)
    if max(scores.values(), default=0) <= 0:
        return "کدنویسی"
    return max(scores, key=scores.get)


def infer_funnel(intent: str, keyword: str) -> str:
    value = normalise(keyword)
    if any(term in value for term in ("دوره", "کلاس", "ثبت نام", "قیمت", "هزینه", "پروژه آماده", "خرید")):
        return "تصمیم/خرید"
    if intent in {"خطا و نصب", "کدنویسی", "مقایسه", "پروژه"}:
        return "بررسی راه‌حل"
    return "آگاهی"


def suggest_title(candidate: Candidate) -> str:
    keyword = display_clean(candidate.keyword)
    norm = normalise(keyword)
    if candidate.intent == "خطا و نصب":
        if any(term in norm for term in ("خطا", "error", "رفع", "fix")):
            return f"{keyword}: علت و راه‌حل مرحله‌به‌مرحله در ویندوز"
        if "نصب" in norm or "install" in norm:
            return f"{keyword}: راهنمای کامل نصب و تست اجرا"
        return f"رفع مشکل {keyword}: چک‌لیست تشخیص و راه‌حل"
    if candidate.intent == "مقایسه":
        return f"{keyword}: تفاوت‌ها، مزایا و انتخاب مناسب"
    if candidate.intent == "تعریف و مفهوم":
        return f"{keyword}؛ تعریف ساده، مدل ریاضی و مثال کاربردی"
    if candidate.intent == "پروژه":
        return f"{keyword}: مدل، کد کامل و تحلیل نتایج"
    if "آموزش" in norm:
        return keyword
    if candidate.cluster_id == "vrp":
        return f"آموزش {keyword} با OR-Tools؛ مدل، کد و ترسیم مسیر"
    if candidate.cluster_id in {"power", "uncertainty", "pyomo", "modeling"}:
        return f"آموزش {keyword} با Python/Pyomo؛ از مدل تا کد"
    return f"آموزش {keyword} با مثال عملی"


def outline_for(candidate: Candidate) -> list[str]:
    keyword = candidate.keyword
    if candidate.intent == "خطا و نصب":
        return [
            f"نشانه‌ها و متن دقیق خطای «{keyword}»",
            "تفاوت نصب پکیج Python با نصب فایل اجرایی Solver",
            "روش تشخیص محیط Python و مسیر اجرایی روی Windows",
            "راه‌حل پیشنهادی و کد تست خودکار",
            "خطاهای مشابه، نسخه‌ها و روش جلوگیری از تکرار",
            "دعوت به دوره مرتبط با یک مثال واقعی",
        ]
    if candidate.intent == "مقایسه":
        return [
            f"تعریف گزینه‌های موجود در «{keyword}»",
            "مقایسه نوع مسئله، سرعت، مجوز و پیچیدگی نصب",
            "حل یک مثال مشترک با هر گزینه",
            "جدول تصمیم‌گیری بر اساس نوع پروژه",
            "جمع‌بندی و مسیر یادگیری پیشنهادی",
        ]
    if candidate.cluster_id == "vrp":
        return [
            f"تعریف مسئله و کاربرد صنعتی {keyword}",
            "داده‌ها: مشتری، انبار، ناوگان، فاصله و محدودیت‌ها",
            "مدل ریاضی و توضیح حذف زیرتور",
            "پیاده‌سازی مرحله‌به‌مرحله با OR-Tools",
            "ترسیم مسیرها و کنترل ظرفیت/زمان",
            "توسعه مدل و لینک به دوره VRP",
        ]
    if candidate.cluster_id == "power":
        return [
            f"جایگاه {keyword} در بهره‌برداری یا برنامه‌ریزی شبکه",
            "مجموعه‌ها، پارامترها، متغیرها، هدف و قیود",
            "داده نمونه و ساخت مدل در Pyomo",
            "انتخاب Solver و تنظیمات حل",
            "نمودارها و اعتبارسنجی نتیجه",
            "توسعه برای شبکه IEEE و لینک به دوره سیستم قدرت",
        ]
    if candidate.cluster_id == "uncertainty":
        return [
            f"چه نوع عدم قطعیتی در {keyword} مدل می‌شود؟",
            "فرض‌ها و داده لازم",
            "فرمول‌بندی کوچک و قابل‌فهم",
            "کد Python/Pyomo و ساخت سناریو",
            "تحلیل ریسک، محافظه‌کاری و حساسیت",
            "مقایسه با روش‌های جایگزین و لینک به دوره عدم قطعیت",
        ]
    return [
        f"مسئله واقعی و هدف {keyword}",
        "متغیر تصمیم، تابع هدف و قیود",
        "پیاده‌سازی مرحله‌به‌مرحله در Python/Pyomo",
        "انتخاب Solver و کنترل وضعیت حل",
        "تحلیل و تصویرسازی خروجی",
        "تمرین توسعه‌ای و لینک به دوره مرتبط",
    ]


# =============================================================================
# ساخت queryهای اکتشافی
# =============================================================================

@dataclass(frozen=True)
class Probe:
    cluster_id: str
    root: str
    query: str
    family: str
    hop: int = 1


def make_probe_pool(run_date: dt.date) -> list[Probe]:
    base: list[Probe] = []
    expanded: list[Probe] = []
    for cluster in CLUSTERS:
        for root_index, root in enumerate(cluster["gateway_seeds"]):
            family = query_family_key(root)
            base.append(Probe(cluster["id"], root, root, family, 1))
            templates = PERSIAN_TEMPLATES if contains_persian(root) else ENGLISH_TEMPLATES
            for template in templates[1:]:
                query = display_clean(template.format(root=root))
                expanded.append(Probe(cluster["id"], root, query, family, 1))

            alphabet = PERSIAN_ALPHABET if contains_persian(root) else ENGLISH_ALPHABET
            start = (run_date.toordinal() + root_index * 5 + len(cluster["id"])) % len(alphabet)
            for offset in range(2):
                letter = alphabet[(start + offset) % len(alphabet)]
                expanded.append(Probe(cluster["id"], root, f"{root} {letter}", family, 1))

    def daily_key(probe: Probe) -> str:
        payload = f"{run_date.isoformat()}|{probe.cluster_id}|{normalise(probe.query)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    expanded.sort(key=daily_key)
    seen: set[str] = set()
    result: list[Probe] = []
    for probe in base + expanded:
        key = f"{probe.cluster_id}|{normalise(probe.query)}"
        if key in seen or not normalise(probe.query):
            continue
        seen.add(key)
        result.append(probe)
    return result


def approved_keyword_probes() -> list[Probe]:
    """تمام کلمات تأییدشده را بدون چرخش یا محدودیت بودجه برمی‌گرداند."""
    probes: list[Probe] = []
    seen: set[str] = set()
    for cluster_id, keywords in APPROVED_KEYWORDS.items():
        for keyword in keywords:
            key = f"{cluster_id}|{normalise(keyword)}"
            if not normalise(keyword) or key in seen:
                continue
            seen.add(key)
            probes.append(Probe(cluster_id, keyword, keyword, query_family_key(keyword), 0))
    return probes


def choose_first_hop_probes(run_date: dt.date, budget: int, monitor_approved: bool = True) -> list[Probe]:
    """فهرست ثابت + تعداد محدودی query اکتشافی روزانه.

    budget فقط تعداد queryهای اکتشافی را تعیین می‌کند. کلمات APPROVED_KEYWORDS
    هر روز همگی و به صورت مستقیم پایش می‌شوند.
    """
    selected = approved_keyword_probes() if monitor_approved else []
    selected_keys = {f"{p.cluster_id}|{normalise(p.query)}" for p in selected}
    if budget <= 0:
        return selected

    pool = make_probe_pool(run_date)
    exploratory_added = 0
    # ابتدا از هر خوشه حداقل یک query تازه انتخاب شود.
    for cluster in CLUSTERS:
        for probe in pool:
            key = f"{probe.cluster_id}|{normalise(probe.query)}"
            if probe.cluster_id == cluster["id"] and key not in selected_keys:
                selected.append(probe)
                selected_keys.add(key)
                exploratory_added += 1
                break
            if exploratory_added >= budget:
                return selected
    for probe in pool:
        if exploratory_added >= budget:
            break
        key = f"{probe.cluster_id}|{normalise(probe.query)}"
        if key in selected_keys:
            continue
        selected.append(probe)
        selected_keys.add(key)
        exploratory_added += 1
    return selected


def build_second_hop_probes(store: dict[str, Candidate], budget: int, run_date: dt.date) -> list[Probe]:
    candidates: list[tuple[float, Candidate]] = []
    for candidate in store.values():
        if len(candidate.autocomplete_sources) < 1:
            continue
        if len(normalise(candidate.keyword).split()) < 2:
            continue
        cluster, relevance = map_cluster(candidate.keyword, candidate.cluster_votes)
        if relevance < 3.0:
            continue
        source_bonus = len(candidate.autocomplete_sources) * 8
        rank_bonus = max(0, 11 - (candidate.best_rank or 10))
        family_bonus = min(len(candidate.unique_families), 4) * 2
        score = source_bonus + rank_bonus + family_bonus + relevance
        candidates.append((score, candidate))

    candidates.sort(key=lambda item: (-item[0], normalise(item[1].keyword)))
    result: list[Probe] = []
    seen: set[str] = set()
    for _score, candidate in candidates:
        cluster, _ = map_cluster(candidate.keyword, candidate.cluster_votes)
        keyword = display_clean(candidate.keyword)
        variants = [keyword]
        if contains_persian(keyword):
            variants.extend([f"{keyword} چگونه", f"{keyword} مثال", f"{keyword} خطا"])
        else:
            variants.extend([f"{keyword} example", f"{keyword} error", f"how to {keyword}"])
        variants.sort(key=lambda value: hashlib.sha256(f"{run_date}|{value}".encode()).hexdigest())
        for query in variants[:2]:
            key = normalise(query)
            if key in seen:
                continue
            seen.add(key)
            result.append(Probe(cluster["id"], keyword, query, normalise(keyword), 2))
            if len(result) >= budget:
                return result
    return result


# =============================================================================
# منابع autocomplete
# =============================================================================

def fetch_google_suggest(query: str, cache_dir: Path, config: dict[str, Any], youtube: bool = False) -> list[str]:
    params = {
        "client": "firefox",
        "hl": str(config["target_language"]),
        "gl": str(config["target_country"]).lower(),
        "q": query,
    }
    if youtube:
        params["ds"] = "yt"
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(params)
    data = json_request(
        url,
        cache_dir=cache_dir,
        cache_hours=int(config["cache_hours"]),
        timeout=int(config["request_timeout_seconds"]),
        attempts=1,
        headers={"Accept": "application/json,text/javascript,*/*;q=0.5"},
    )
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


def fetch_bing_suggest(query: str, cache_dir: Path, config: dict[str, Any]) -> list[str]:
    params = {"query": query, "market": str(config["target_market"])}
    url = "https://api.bing.com/osjson.aspx?" + urllib.parse.urlencode(params)
    data = json_request(
        url,
        cache_dir=cache_dir,
        cache_hours=int(config["cache_hours"]),
        timeout=int(config["request_timeout_seconds"]),
        attempts=1,
    )
    raw_values = data[1] if isinstance(data, list) and len(data) > 1 else []
    return [display_clean(value) for value in raw_values if display_clean(value)]


def fetch_duckduckgo_suggest(query: str, cache_dir: Path, config: dict[str, Any]) -> list[str]:
    url = "https://duckduckgo.com/ac/?" + urllib.parse.urlencode({"q": query, "type": "list"})
    data = json_request(
        url,
        cache_dir=cache_dir,
        cache_hours=int(config["cache_hours"]),
        timeout=int(config["request_timeout_seconds"]),
        attempts=1,
    )
    values: list[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                value = display_clean(item.get("phrase") or item.get("value") or "")
            else:
                value = display_clean(item)
            if value:
                values.append(value)
    return values


SOURCE_FETCHERS = {
    "Google Search Autocomplete": lambda query, cache, config: fetch_google_suggest(query, cache, config, False),
    "YouTube Autocomplete": lambda query, cache, config: fetch_google_suggest(query, cache, config, True),
    "Bing Autocomplete": fetch_bing_suggest,
    "DuckDuckGo Autocomplete": fetch_duckduckgo_suggest,
}


def add_candidate(
    store: dict[str, Candidate],
    keyword: str,
    observation: Observation,
    cluster_id: str = "",
) -> Candidate | None:
    keyword = display_clean(keyword)
    key = keyword_key(keyword)
    if len(key) < 3 or len(key) > 220:
        return None
    if len(key.split()) > 22 or is_negative_keyword(keyword):
        return None
    candidate = store.setdefault(key, Candidate(keyword=keyword))
    candidate.add_observation(observation)
    if cluster_id:
        candidate.cluster_votes[cluster_id] += 1
    return candidate


def candidate_relevance(keyword: str, context_cluster_id: str, query: str) -> float:
    cluster, score = map_cluster(keyword, context_cluster=context_cluster_id)
    query_tokens = token_set(query, remove_generic=True)
    keyword_tokens = token_set(keyword, remove_generic=True)
    overlap = len(query_tokens & keyword_tokens)
    if cluster["id"] == context_cluster_id:
        score += 2.5
    score += min(overlap, 4) * 0.7
    return score


def collect_autocomplete_source(
    store: dict[str, Candidate],
    probes: list[Probe],
    source: str,
    cache_dir: Path,
    config: dict[str, Any],
    status: dict[str, str],
    run_date: dt.date,
) -> None:
    fetcher = SOURCE_FETCHERS[source]
    if not probes:
        status[source] = "بدون query"
        return

    try:
        fetcher(probes[0].query, cache_dir, config)
    except Exception as exc:
        status[source] = f"در دسترس نبود: {type(exc).__name__}"
        return

    success = 0
    failed = 0
    accepted = 0
    lock_store: list[tuple[str, Observation, str]] = []

    def task(probe: Probe) -> tuple[Probe, list[str]]:
        time.sleep(float(config["request_delay_seconds"]) + random.random() * 0.10)
        return probe, fetcher(probe.query, cache_dir, config)

    with ThreadPoolExecutor(max_workers=int(config["max_workers"])) as executor:
        futures = [executor.submit(task, probe) for probe in probes]
        for future in as_completed(futures):
            try:
                probe, suggestions = future.result()
                success += 1
            except Exception:
                failed += 1
                continue
            query_norm = normalise(probe.query)
            for rank, suggestion in enumerate(suggestions, start=1):
                if normalise(suggestion) == query_norm:
                    continue
                relevance = candidate_relevance(suggestion, probe.cluster_id, probe.query)
                if relevance < 3.0:
                    continue
                observation = Observation(
                    source=source,
                    query=probe.query,
                    family=probe.family,
                    rank=rank,
                    date=run_date.isoformat(),
                    note=f"hop={probe.hop}",
                )
                lock_store.append((suggestion, observation, probe.cluster_id))

    for suggestion, observation, cluster_id in lock_store:
        if add_candidate(store, suggestion, observation, cluster_id):
            accepted += 1
    status[source] = f"{success} query موفق، {failed} ناموفق، {accepted} مشاهده"


def collect_all_autocomplete(
    store: dict[str, Candidate],
    probes: list[Probe],
    cache_dir: Path,
    config: dict[str, Any],
    status: dict[str, str],
    run_date: dt.date,
) -> None:
    for source in SOURCE_FETCHERS:
        collect_autocomplete_source(store, probes, source, cache_dir, config, status, run_date)


# =============================================================================
# Stack Exchange: سیگنال سؤال و درد واقعی
# =============================================================================

STACK_QUERIES: list[tuple[str, str, str]] = [
    ("stackoverflow", "pyomo solver", "pyomo"),
    ("stackoverflow", "ortools vehicle routing", "vrp"),
    ("stackoverflow", "cvrp vrptw python", "vrp"),
    ("or", "robust optimization pyomo", "uncertainty"),
    ("or", "stochastic programming scenario", "uncertainty"),
    ("or", "unit commitment optimal power flow", "power"),
]


def collect_stackexchange(
    store: dict[str, Candidate],
    cache_dir: Path,
    config: dict[str, Any],
    status: dict[str, str],
    run_date: dt.date,
) -> None:
    from_date = int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=int(config["stackexchange_lookback_days"]))).timestamp())
    accepted = 0
    failed = 0
    total = 0

    for site, query, context_cluster in STACK_QUERIES:
        params = {
            "site": site,
            "q": query,
            "fromdate": str(from_date),
            "order": "desc",
            "sort": "activity",
            "pagesize": str(int(config["stackexchange_pagesize"])),
            "filter": "default",
        }
        url = "https://api.stackexchange.com/2.3/search/advanced?" + urllib.parse.urlencode(params)
        try:
            data = json_request(
                url,
                cache_dir=cache_dir,
                cache_hours=8,
                timeout=int(config["request_timeout_seconds"]),
                attempts=1,
            )
        except Exception:
            failed += 1
            continue
        items = data.get("items", []) if isinstance(data, dict) else []
        total += len(items)
        for item in items:
            title = display_clean(item.get("title", ""))
            if not title or is_negative_keyword(title):
                continue
            cluster, relevance = map_cluster(title, context_cluster=context_cluster)
            if relevance < 3.0:
                continue
            views = safe_float(item.get("view_count", 0))
            score = safe_float(item.get("score", 0))
            observation = Observation(
                source="Stack Exchange Questions",
                query=query,
                family=query,
                rank=0,
                url=display_clean(item.get("link", "")),
                date=date_from_timestamp(item.get("creation_date", 0)).isoformat(),
                value=views,
                note=f"site={site}; score={score:g}",
            )
            candidate = add_candidate(store, title, observation, cluster["id"])
            if candidate:
                candidate.stack_views += views
                candidate.stack_score += score
                candidate.stack_questions += 1
                accepted += 1
    status["Stack Exchange"] = f"{accepted} سؤال مرتبط از {total} نتیجه؛ {failed} query ناموفق"


# =============================================================================
# Google Search Console CSV و API اختیاری
# =============================================================================

def detect_table_start(text: str, header_aliases: Iterable[str]) -> tuple[int, str]:
    lines = text.splitlines()
    aliases = tuple(normalise(alias) for alias in header_aliases)
    for index, line in enumerate(lines[:50]):
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


def load_gsc_csv(path: Path, store: dict[str, Candidate], status: dict[str, str], run_date: dt.date) -> None:
    try:
        text, encoding = read_text_file_flexible(path)
    except OSError as exc:
        status["Search Console CSV"] = f"خطا: {exc}"
        return
    start, delimiter = detect_table_start(text, ("Top queries", "Query", "Queries", "عبارت جستجو", "کوئری"))
    reader = csv.DictReader(text.splitlines()[start:], delimiter=delimiter)
    fields = reader.fieldnames or []
    query_col = choose_column(fields, ("Top queries", "Query", "Queries", "Keyword", "کلمه کلیدی", "عبارت جستجو", "کوئری"))
    clicks_col = choose_column(fields, ("Clicks", "Click", "کلیک", "کلیک‌ها"))
    impressions_col = choose_column(fields, ("Impressions", "نمایش", "نمایش‌ها"))
    position_col = choose_column(fields, ("Position", "Average position", "میانگین موقعیت", "رتبه"))
    page_col = choose_column(fields, ("Page", "Pages", "صفحه"))
    if not query_col:
        status["Search Console CSV"] = "ستون Query پیدا نشد"
        return

    accepted = 0
    rows = 0
    for row in reader:
        rows += 1
        keyword = display_clean(row.get(query_col, ""))
        impressions = safe_float(row.get(impressions_col, 0)) if impressions_col else 0.0
        if not keyword or impressions <= 0:
            continue
        cluster, relevance = map_cluster(keyword)
        if relevance < 2.5:
            continue
        observation = Observation(
            source="Google Search Console",
            family="gsc",
            date=run_date.isoformat(),
            value=impressions,
            note="CSV",
        )
        candidate = add_candidate(store, keyword, observation, cluster["id"])
        if not candidate:
            continue
        candidate.gsc_impressions += impressions
        candidate.gsc_clicks += safe_float(row.get(clicks_col, 0)) if clicks_col else 0.0
        position = safe_float(row.get(position_col, 0)) if position_col else 0.0
        if position > 0:
            if candidate.gsc_position <= 0:
                candidate.gsc_position = position
            else:
                candidate.gsc_position = (candidate.gsc_position + position) / 2.0
        if page_col and not candidate.gsc_page:
            candidate.gsc_page = display_clean(row.get(page_col, ""))
        accepted += 1
    status["Search Console CSV"] = f"{accepted} عبارت از {rows} ردیف؛ {path.name}; {encoding}"


def _gsc_query_rows(service: Any, site_url: str, start_date: dt.date, end_date: dt.date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start_row = 0
    page_size = 25000
    while True:
        body = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["query", "page"],
            "rowLimit": page_size,
            "startRow": start_row,
            "dataState": "final",
        }
        response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
        batch = response.get("rows", [])
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start_row += page_size
        if start_row >= 100000:
            break
    return rows


def collect_gsc_api(
    store: dict[str, Candidate],
    config: dict[str, Any],
    status: dict[str, str],
    run_date: dt.date,
) -> None:
    credentials_file = display_clean(config.get("gsc_service_account_file", ""))
    site_url = display_clean(config.get("gsc_site_url", ""))
    if not credentials_file or not site_url:
        status["Search Console API"] = "تنظیم نشده"
        return
    path = Path(credentials_file).expanduser()
    if not path.is_absolute():
        path = Path(str(config.get("_base_dir", "."))) / path
    path = path.resolve()
    if not path.exists():
        status["Search Console API"] = f"فایل credential پیدا نشد: {path}"
        return
    try:
        from google.oauth2 import service_account  # type: ignore
        from googleapiclient.discovery import build  # type: ignore
    except ImportError:
        status["Search Console API"] = "پکیج‌های google-api-python-client و google-auth نصب نیست"
        return

    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(path),
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        service = build("searchconsole", "v1", credentials=credentials, cache_discovery=False)
        lag = int(config["gsc_data_lag_days"])
        days = int(config["gsc_days"])
        end_current = run_date - dt.timedelta(days=lag)
        start_current = end_current - dt.timedelta(days=days - 1)
        end_previous = start_current - dt.timedelta(days=1)
        start_previous = end_previous - dt.timedelta(days=days - 1)
        current_rows = _gsc_query_rows(service, site_url, start_current, end_current)
        previous_rows = _gsc_query_rows(service, site_url, start_previous, end_previous)
    except Exception as exc:
        status["Search Console API"] = f"خطا: {type(exc).__name__}: {exc}"
        return

    previous_by_query: dict[str, float] = defaultdict(float)
    for row in previous_rows:
        keys = row.get("keys", [])
        if keys:
            previous_by_query[normalise(keys[0])] += safe_float(row.get("impressions", 0))

    accepted = 0
    for row in current_rows:
        keys = row.get("keys", [])
        if not keys:
            continue
        keyword = display_clean(keys[0])
        page = display_clean(keys[1]) if len(keys) > 1 else ""
        impressions = safe_float(row.get("impressions", 0))
        if not keyword or impressions <= 0:
            continue
        cluster, relevance = map_cluster(keyword)
        if relevance < 2.5:
            continue
        observation = Observation(
            source="Google Search Console",
            family="gsc-api",
            date=run_date.isoformat(),
            value=impressions,
            note=f"{start_current}..{end_current}",
        )
        candidate = add_candidate(store, keyword, observation, cluster["id"])
        if not candidate:
            continue
        candidate.gsc_impressions += impressions
        candidate.gsc_clicks += safe_float(row.get("clicks", 0))
        candidate.gsc_position = safe_float(row.get("position", 0))
        candidate.gsc_previous_impressions += previous_by_query.get(normalise(keyword), 0.0)
        candidate.gsc_page = page or candidate.gsc_page
        accepted += 1
    status["Search Console API"] = f"{accepted} عبارت؛ بازه {start_current} تا {end_current}"


# =============================================================================
# Google Ads Keyword Planner CSV
# =============================================================================

def load_keyword_planner_csv(path: Path, store: dict[str, Candidate], status: dict[str, str], run_date: dt.date) -> None:
    try:
        text, encoding = read_text_file_flexible(path)
    except OSError as exc:
        status["Keyword Planner"] = f"خطا: {exc}"
        return
    start, delimiter = detect_table_start(text, (
        "Keyword", "Keywords", "کلمه کلیدی", "عبارت کلیدی", "Avg. monthly searches",
    ))
    reader = csv.DictReader(text.splitlines()[start:], delimiter=delimiter)
    fields = reader.fieldnames or []
    keyword_col = choose_column(fields, ("Keyword", "Keywords", "کلمه کلیدی", "عبارت کلیدی"))
    volume_col = choose_column(fields, (
        "Avg. monthly searches", "Average monthly searches", "Avg monthly searches",
        "میانگین جستجوهای ماهانه", "میانگین جستجوی ماهانه", "حجم جستجو",
    ))
    competition_col = choose_column(fields, ("Competition", "رقابت", "Competition (indexed value)"))
    change_col = choose_column(fields, (
        "Three month change", "YoY change", "Year over year change", "تغییر سه ماهه", "تغییر سالانه",
    ))
    if not keyword_col:
        status["Keyword Planner"] = "ستون Keyword پیدا نشد"
        return

    accepted = 0
    rows = 0
    for row in reader:
        rows += 1
        keyword = display_clean(row.get(keyword_col, ""))
        if not keyword:
            continue
        cluster, relevance = map_cluster(keyword)
        if relevance < 2.5:
            continue
        observation = Observation(
            source="Google Ads Keyword Planner",
            family="keyword-planner",
            date=run_date.isoformat(),
            note="CSV",
        )
        candidate = add_candidate(store, keyword, observation, cluster["id"])
        if not candidate:
            continue
        raw_volume = display_clean(row.get(volume_col, "")) if volume_col else ""
        volume = parse_human_number(raw_volume)
        if volume > candidate.monthly_searches:
            candidate.monthly_searches = volume
            candidate.monthly_searches_raw = raw_volume
        if competition_col and not candidate.competition_raw:
            candidate.competition_raw = display_clean(row.get(competition_col, ""))
        if change_col and not candidate.planner_change:
            candidate.planner_change = display_clean(row.get(change_col, ""))
        accepted += 1
    status["Keyword Planner"] = f"{accepted} عبارت از {rows} ردیف؛ {path.name}; {encoding}"

# =============================================================================
# Serper API اختیاری: PAA، Related Searches و رقابت SERP
# =============================================================================

def serp_title_match(keyword: str, title: str) -> bool:
    score = phrase_similarity(keyword, title)
    target_tokens = token_set(keyword, remove_generic=True)
    title_tokens = token_set(title, remove_generic=True)
    coverage = len(target_tokens & title_tokens) / len(target_tokens) if target_tokens else 0.0
    return score >= 0.72 or (len(target_tokens) >= 2 and coverage >= 0.82)


def serp_competition_from_results(keyword: str, organic: list[dict[str, Any]], site_domain: str) -> tuple[int, int, int, list[str], float]:
    exact_titles = 0
    strong_domains = 0
    user_rank = 0
    titles: list[str] = []
    for rank, item in enumerate(organic[:10], start=1):
        title = display_clean(item.get("title", ""))
        link = display_clean(item.get("link", ""))
        domain = domain_from_url(link)
        if title:
            titles.append(title)
        if serp_title_match(keyword, title):
            exact_titles += 1
        if domain in STRONG_SERP_DOMAINS or any(domain.endswith("." + strong) for strong in STRONG_SERP_DOMAINS):
            strong_domains += 1
        if domain == site_domain and user_rank == 0:
            user_rank = rank

    competition = exact_titles * 11 + strong_domains * 7
    if organic:
        top3_strong = 0
        for item in organic[:3]:
            domain = domain_from_url(display_clean(item.get("link", "")))
            if domain in STRONG_SERP_DOMAINS or any(domain.endswith("." + strong) for strong in STRONG_SERP_DOMAINS):
                top3_strong += 1
        competition += top3_strong * 6
    if user_rank and user_rank <= 5:
        competition -= 12
    return exact_titles, strong_domains, user_rank, titles[:5], max(0.0, min(100.0, float(competition)))


def serper_search(keyword: str, cache_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    api_key = display_clean(config.get("serper_api_key", ""))
    if not api_key:
        raise RuntimeError("SERPER_API_KEY is not configured")
    payload = json.dumps({
        "q": keyword,
        "gl": str(config["target_country"]).lower(),
        "hl": str(config["target_language"]),
        "num": 10,
    }, ensure_ascii=False).encode("utf-8")
    return json_request(
        "https://google.serper.dev/search",
        cache_dir=cache_dir,
        cache_hours=12,
        timeout=int(config["request_timeout_seconds"]),
        attempts=2,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        data=payload,
        method="POST",
    )


def preliminary_priority(candidate: Candidate) -> float:
    source_score = len(candidate.autocomplete_sources) * 12
    rank_score = max(0, 11 - (candidate.best_rank or 10)) * 2
    family_score = min(len(candidate.unique_families), 5) * 4
    gsc_score = min(math.log1p(candidate.gsc_impressions) * 5, 30)
    volume_score = min(math.log10(candidate.monthly_searches + 1) * 12, 36) if candidate.monthly_searches > 0 else 0
    stack_score = min(math.log1p(candidate.stack_views) * 3, 20)
    gap = 100 * (1.0 - candidate.existing_similarity)
    return source_score + rank_score + family_score + gsc_score + volume_score + stack_score + gap * 0.25


def enrich_with_serper(
    store: dict[str, Candidate],
    pages: list[ExistingPage],
    cache_dir: Path,
    config: dict[str, Any],
    status: dict[str, str],
    run_date: dt.date,
) -> None:
    if not display_clean(config.get("serper_api_key", "")):
        status["Serper / Google SERP"] = "تنظیم نشده؛ رقابت SERP و PAA اندازه‌گیری نشد"
        return

    # ابتدا یک بررسی موقت پوشش برای انتخاب کاندیداهای ارزشمند انجام می‌دهیم.
    for candidate in store.values():
        page, similarity, mentioned = closest_existing_page(candidate.keyword, pages)
        candidate.existing_similarity = similarity
        candidate.mentioned_in_body = mentioned
        if page:
            candidate.existing_title = page.title
            candidate.existing_url = page.url

    candidates = [candidate for candidate in store.values() if candidate.existing_similarity < float(config["existing_page_threshold"])]
    candidates.sort(key=lambda item: (-preliminary_priority(item), normalise(item.keyword)))
    selected = candidates[: int(config["serp_checks_per_run"])]
    site_domain = domain_from_url(str(config["site_url"]))

    checked = 0
    failed = 0
    added = 0
    for candidate in selected:
        try:
            data = serper_search(candidate.keyword, cache_dir, config)
        except Exception:
            failed += 1
            continue
        checked += 1
        organic = data.get("organic", []) if isinstance(data, dict) else []
        exact, strong, user_rank, titles, difficulty = serp_competition_from_results(
            candidate.keyword,
            organic if isinstance(organic, list) else [],
            site_domain,
        )
        candidate.serp_checked = True
        candidate.serp_exact_titles = exact
        candidate.serp_strong_domains = strong
        candidate.serp_user_domain_rank = user_rank
        candidate.serp_top_titles = titles
        candidate.serp_competition_score = difficulty
        candidate.add_observation(Observation(
            source="Google SERP Check",
            family="serp",
            date=run_date.isoformat(),
            value=difficulty,
            note=f"exact={exact}; strong={strong}; rank={user_rank}",
        ))

        cluster, _ = map_cluster(candidate.keyword, candidate.cluster_votes)
        for item in data.get("peopleAlsoAsk", []) if isinstance(data, dict) else []:
            question = display_clean(item.get("question", "")) if isinstance(item, dict) else ""
            if not question or normalise(question) == normalise(candidate.keyword):
                continue
            relevance = candidate_relevance(question, cluster["id"], candidate.keyword)
            if relevance < 3.0:
                continue
            observation = Observation(
                source="Google SERP PAA",
                query=candidate.keyword,
                family=normalise(candidate.keyword),
                date=run_date.isoformat(),
                url=display_clean(item.get("link", "")) if isinstance(item, dict) else "",
                note="People Also Ask",
            )
            if add_candidate(store, question, observation, cluster["id"]):
                added += 1

        for item in data.get("relatedSearches", []) if isinstance(data, dict) else []:
            query = display_clean(item.get("query", "")) if isinstance(item, dict) else display_clean(item)
            if not query or normalise(query) == normalise(candidate.keyword):
                continue
            relevance = candidate_relevance(query, cluster["id"], candidate.keyword)
            if relevance < 3.0:
                continue
            observation = Observation(
                source="Google SERP Related",
                query=candidate.keyword,
                family=normalise(candidate.keyword),
                date=run_date.isoformat(),
                note="Related Search",
            )
            if add_candidate(store, query, observation, cluster["id"]):
                added += 1
    status["Serper / Google SERP"] = f"{checked} عبارت بررسی شد؛ {failed} خطا؛ {added} PAA/Related اضافه شد"


# =============================================================================
# تاریخچه معتبرتر: مقایسه فقط در context یکسان
# =============================================================================

def load_history(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 3, "keywords": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 3, "keywords": {}}
    if not isinstance(data, dict) or not isinstance(data.get("keywords"), dict):
        return {"version": 3, "keywords": {}}
    return data


def current_context_ranks(candidate: Candidate) -> dict[str, int]:
    values: dict[str, int] = {}
    for observation in candidate.observations:
        if observation.rank <= 0 or not observation.family:
            continue
        context = f"{observation.source}|{normalise(observation.family)}"
        current = values.get(context)
        if current is None or observation.rank < current:
            values[context] = observation.rank
    return values


def apply_history(candidate: Candidate, history: dict[str, Any], run_date: dt.date, config: dict[str, Any]) -> None:
    key = keyword_key(candidate.keyword)
    previous = history.get("keywords", {}).get(key)
    if not isinstance(previous, dict):
        candidate.first_seen = run_date.isoformat()
        candidate.seen_days = 1
        candidate.trend_label = "جدید امروز"
        candidate.trend_score = 8.0
        return

    candidate.first_seen = str(previous.get("first_seen", run_date.isoformat()))
    seen_dates = [str(value) for value in previous.get("seen_dates", []) if isinstance(value, str)]
    candidate.seen_days = len(set(seen_dates + [run_date.isoformat()]))

    previous_ranks = previous.get("context_ranks", {}) if isinstance(previous.get("context_ranks"), dict) else {}
    current_ranks = current_context_ranks(candidate)
    improvements: list[int] = []
    for context, current_rank in current_ranks.items():
        previous_rank = int(previous_ranks.get(context, 0) or 0)
        if previous_rank > 0:
            improvements.append(previous_rank - current_rank)

    gsc_previous = candidate.gsc_previous_impressions
    gsc_current = candidate.gsc_impressions
    gsc_growth = 0.0
    if gsc_previous > 0:
        gsc_growth = (gsc_current - gsc_previous) / gsc_previous

    if (improvements and sum(1 for value in improvements if value >= 2) >= 2) or gsc_growth >= 0.25:
        candidate.trend_label = "رو‌به‌رشد"
        candidate.trend_score = 12.0
    elif improvements and sum(1 for value in improvements if value <= -3) >= 2:
        candidate.trend_label = "نزولی"
        candidate.trend_score = -5.0
    elif candidate.seen_days >= 4:
        candidate.trend_label = "تقاضای پایدار"
        candidate.trend_score = 8.0
    else:
        candidate.trend_label = "تکرار مشاهده"
        candidate.trend_score = 3.0

    selected_dates: list[dt.date] = []
    for value in previous.get("selected_dates", []):
        try:
            selected_dates.append(dt.date.fromisoformat(str(value)))
        except ValueError:
            continue
    if selected_dates:
        days_since = (run_date - max(selected_dates)).days
        cooldown = int(config["recommendation_cooldown_days"])
        if 0 <= days_since <= cooldown:
            candidate.cooldown_penalty = 7.0 if candidate.trend_label == "رو‌به‌رشد" else 18.0


def update_history(
    history: dict[str, Any],
    all_candidates: list[Candidate],
    selected: list[Candidate],
    run_date: dt.date,
    config: dict[str, Any],
    path: Path,
) -> None:
    keywords = history.setdefault("keywords", {})
    selected_keys = {keyword_key(candidate.keyword) for candidate in selected}
    cutoff = run_date - dt.timedelta(days=int(config["history_days"]))

    for candidate in all_candidates:
        key = keyword_key(candidate.keyword)
        entry = keywords.setdefault(key, {
            "keyword": candidate.keyword,
            "first_seen": run_date.isoformat(),
            "seen_dates": [],
            "selected_dates": [],
            "context_ranks": {},
        })
        entry["keyword"] = candidate.keyword
        entry.setdefault("first_seen", run_date.isoformat())

        valid_seen: list[str] = []
        for value in entry.get("seen_dates", []):
            try:
                date_value = dt.date.fromisoformat(str(value))
            except ValueError:
                continue
            if date_value >= cutoff:
                valid_seen.append(date_value.isoformat())
        valid_seen.append(run_date.isoformat())
        entry["seen_dates"] = sorted(set(valid_seen))

        valid_selected: list[str] = []
        for value in entry.get("selected_dates", []):
            try:
                date_value = dt.date.fromisoformat(str(value))
            except ValueError:
                continue
            if date_value >= cutoff:
                valid_selected.append(date_value.isoformat())
        if key in selected_keys:
            valid_selected.append(run_date.isoformat())
        entry["selected_dates"] = sorted(set(valid_selected))

        entry["context_ranks"] = current_context_ranks(candidate)
        entry["last_seen"] = run_date.isoformat()
        entry["last_sources"] = sorted(candidate.sources)
        entry["last_demand_score"] = candidate.demand_score
        entry["last_opportunity_score"] = candidate.opportunity_score
        entry["last_gsc_impressions"] = candidate.gsc_impressions
        entry["last_monthly_searches"] = candidate.monthly_searches

    for key in list(keywords):
        entry = keywords[key]
        try:
            last_seen = dt.date.fromisoformat(str(entry.get("last_seen", "")))
        except ValueError:
            last_seen = cutoff
        if last_seen < cutoff:
            del keywords[key]

    history["version"] = 3
    history["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


# =============================================================================
# امتیازدهی شفاف
# =============================================================================

def rank_signal(best_rank: int) -> float:
    if best_rank <= 0:
        return 0.0
    return max(0.0, 11.0 - best_rank) / 10.0


def compute_demand_score(candidate: Candidate) -> float:
    score = 0.0

    if candidate.monthly_searches > 0:
        score += 18.0 + min(math.log10(candidate.monthly_searches + 1) * 10.0, 32.0)

    if candidate.gsc_impressions > 0:
        score += 16.0 + min(math.log1p(candidate.gsc_impressions) * 3.8, 28.0)
        if 4.0 <= candidate.gsc_position <= 20.0:
            score += 6.0

    source_caps = {
        "Google Search Autocomplete": 14.0,
        "YouTube Autocomplete": 11.0,
        "Bing Autocomplete": 10.0,
        "DuckDuckGo Autocomplete": 7.0,
        "Google SERP Related": 9.0,
        "Google SERP PAA": 9.0,
    }
    for source, cap in source_caps.items():
        observations = [obs for obs in candidate.observations if obs.source == source]
        if not observations:
            continue
        best = min((obs.rank for obs in observations if obs.rank > 0), default=0)
        score += cap * (0.55 + 0.45 * rank_signal(best))

    source_diversity = len(candidate.autocomplete_sources)
    if source_diversity > 1:
        score += min((source_diversity - 1) * 5.0, 15.0)

    # تعداد خانواده query مستقل، نه تعداد modifierهای تکراری.
    score += min(len(candidate.unique_families) * 2.0, 10.0)

    if candidate.stack_views > 0:
        score += min(math.log1p(candidate.stack_views) * 2.4, 17.0)
        score += min(max(candidate.stack_score, 0) * 0.7, 5.0)

    score += candidate.trend_score
    return max(0.0, min(100.0, score))


def compute_confidence(candidate: Candidate) -> str:
    hard_sources = int(candidate.monthly_searches > 0) + int(candidate.gsc_impressions > 0)
    independent = len(candidate.autocomplete_sources) + hard_sources + int(candidate.stack_views > 0)
    if hard_sources >= 1 and independent >= 3:
        return "خیلی بالا"
    if hard_sources >= 1 or independent >= 4 or (candidate.seen_days >= 4 and independent >= 2):
        return "بالا"
    if independent >= 2 or candidate.seen_days >= 3:
        return "متوسط"
    return "کم"


def compute_business_fit(candidate: Candidate, cluster: dict[str, Any]) -> float:
    score = float(cluster.get("business_fit", 80))
    score += float(cluster.get("intent_bonus", {}).get(candidate.intent, 0))
    if candidate.funnel == "تصمیم/خرید":
        score += 7.0
    elif candidate.funnel == "بررسی راه‌حل":
        score += 4.0
    if candidate.cluster_id in {"pyomo", "vrp", "power", "uncertainty"} and candidate.intent in {"کدنویسی", "خطا و نصب", "پروژه"}:
        score += 4.0
    return max(0.0, min(100.0, score))


def build_reason(candidate: Candidate) -> str:
    reasons: list[str] = []
    source_labels = {
        "Google Search Autocomplete": "Google Search",
        "YouTube Autocomplete": "YouTube",
        "Bing Autocomplete": "Bing",
        "DuckDuckGo Autocomplete": "DuckDuckGo",
        "Google SERP Related": "Related Searches",
        "Google SERP PAA": "People Also Ask",
    }
    autocomplete = [source_labels[source] for source in source_labels if source in candidate.sources]
    if autocomplete:
        reasons.append("سیگنال در " + "، ".join(autocomplete))
    if candidate.monthly_searches > 0:
        reasons.append(f"حجم ماهانه گزارش‌شده ≈ {candidate.monthly_searches:,.0f}")
    if candidate.gsc_impressions > 0:
        reasons.append(f"Search Console: {candidate.gsc_impressions:,.0f} نمایش و رتبه {candidate.gsc_position:.1f}")
    if candidate.stack_views > 0:
        reasons.append(f"سؤال‌های فنی مرتبط با مجموع {candidate.stack_views:,.0f} بازدید")
    if candidate.trend_label:
        reasons.append(candidate.trend_label)
    if candidate.serp_competition_score is not None:
        reasons.append(f"رقابت تقریبی SERP {candidate.serp_competition_score:.0f}/100")
    else:
        reasons.append("رقابت SERP اندازه‌گیری نشده")
    if candidate.coverage_action == "قبلاً صفحه متمرکز دارد":
        reasons.append(f"نزدیک به صفحه «{candidate.existing_title}»")
    elif candidate.coverage_action == "صفحه مکمل لازم است":
        reasons.append(f"صفحه نزدیک وجود دارد، اما نیت دقیق پوشش کامل ندارد")
    elif candidate.mentioned_in_body:
        reasons.append("فقط در متن سایت اشاره شده و صفحه متمرکز ندارد")
    else:
        reasons.append("صفحه متمرکز مشابه پیدا نشد")
    return "؛ ".join(reasons)


def finalise_candidates(
    store: dict[str, Candidate],
    pages: list[ExistingPage],
    history: dict[str, Any],
    run_date: dt.date,
    config: dict[str, Any],
) -> tuple[list[Candidate], list[Candidate], list[Candidate]]:
    processed: list[Candidate] = []
    existing_threshold = float(config["existing_page_threshold"])
    related_threshold = float(config["related_page_threshold"])

    for candidate in store.values():
        if not candidate.sources:
            continue
        cluster, relevance = map_cluster(candidate.keyword, candidate.cluster_votes)
        if relevance < 2.5:
            continue

        candidate.cluster_id = cluster["id"]
        candidate.cluster_name = cluster["name"]
        candidate.course_url = absolute_url(str(config["site_url"]), cluster["course_url"])
        candidate.intent = infer_intent(candidate.keyword)
        candidate.funnel = infer_funnel(candidate.intent, candidate.keyword)
        candidate.suggested_title = suggest_title(candidate)
        candidate.suggested_slug = slugify(candidate.keyword)

        page, similarity, mentioned = closest_existing_page(candidate.keyword, pages)
        candidate.existing_similarity = similarity
        candidate.mentioned_in_body = mentioned
        if page:
            candidate.existing_title = page.title
            candidate.existing_url = page.url

        if similarity >= existing_threshold:
            candidate.coverage_action = "قبلاً صفحه متمرکز دارد"
        elif similarity >= related_threshold:
            candidate.coverage_action = "صفحه مکمل لازم است"
        else:
            candidate.coverage_action = "محتوای جدید"

        apply_history(candidate, history, run_date, config)
        candidate.demand_score = round(compute_demand_score(candidate), 1)
        candidate.gap_score = round(max(0.0, min(100.0, (1.0 - similarity) * 100.0)), 1)
        if candidate.mentioned_in_body and candidate.gap_score > 15:
            candidate.gap_score = max(0.0, candidate.gap_score - 7.0)
        candidate.business_fit_score = round(compute_business_fit(candidate, cluster), 1)
        candidate.freshness_score = 100.0 if candidate.first_seen == run_date.isoformat() else min(100.0, 40.0 + candidate.seen_days * 8.0)

        competition_relief = 50.0
        if candidate.serp_competition_score is not None:
            competition_relief = 100.0 - candidate.serp_competition_score

        if candidate.serp_competition_score is None:
            opportunity = (
                0.48 * candidate.demand_score
                + 0.32 * candidate.gap_score
                + 0.20 * candidate.business_fit_score
            )
        else:
            opportunity = (
                0.42 * candidate.demand_score
                + 0.28 * candidate.gap_score
                + 0.18 * candidate.business_fit_score
                + 0.12 * competition_relief
            )
        if candidate.coverage_action == "قبلاً صفحه متمرکز دارد":
            opportunity -= 22.0
        elif candidate.coverage_action == "صفحه مکمل لازم است":
            opportunity -= 5.0
        opportunity -= candidate.cooldown_penalty
        candidate.opportunity_score = round(max(0.0, min(100.0, opportunity)), 1)
        candidate.confidence = compute_confidence(candidate)
        candidate.reason = build_reason(candidate)
        processed.append(candidate)

    processed.sort(key=lambda item: (
        -item.opportunity_score,
        -item.demand_score,
        -item.monthly_searches,
        -item.gsc_impressions,
        item.best_rank if item.best_rank else 99,
        normalise(item.keyword),
    ))

    opportunities = [
        candidate for candidate in processed
        if candidate.coverage_action != "قبلاً صفحه متمرکز دارد"
        and candidate.opportunity_score >= float(config["minimum_opportunity_score"])
    ]
    covered = [candidate for candidate in processed if candidate.coverage_action == "قبلاً صفحه متمرکز دارد"]
    opportunities = deduplicate_candidates(opportunities, int(config["top_opportunities"]))
    covered = deduplicate_candidates(covered, 30)
    return opportunities, covered, processed


def candidate_signature(text: str) -> str:
    tokens = [token for token in normalise(text).split() if token not in {normalise(word) for word in GENERIC_WORDS}]
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
            seq = difflib.SequenceMatcher(None, left, right).ratio()
            left_tokens = token_set(candidate.keyword, remove_generic=True)
            right_tokens = token_set(previous.keyword, remove_generic=True)
            union = left_tokens | right_tokens
            jaccard = len(left_tokens & right_tokens) / len(union) if union else 0.0
            if seq >= 0.91 or jaccard >= 0.85:
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


# =============================================================================
# گزارش‌ها و خروجی‌ها
# =============================================================================

SOURCE_LABELS: dict[str, str] = {
    "Google Search Autocomplete": "Google Search",
    "YouTube Autocomplete": "YouTube",
    "Bing Autocomplete": "Bing",
    "DuckDuckGo Autocomplete": "DuckDuckGo",
    "Google Search Console": "Search Console",
    "Google Ads Keyword Planner": "Keyword Planner",
    "Stack Exchange Questions": "Stack Exchange",
    "Google SERP Check": "SERP Check",
    "Google SERP Related": "Related Searches",
    "Google SERP PAA": "People Also Ask",
}


def source_label(candidate: Candidate) -> str:
    order = [
        "Google Search Console",
        "Google Ads Keyword Planner",
        "Google Search Autocomplete",
        "YouTube Autocomplete",
        "Bing Autocomplete",
        "DuckDuckGo Autocomplete",
        "Google SERP PAA",
        "Google SERP Related",
        "Stack Exchange Questions",
        "Google SERP Check",
    ]
    labels = [SOURCE_LABELS[source] for source in order if source in candidate.sources]
    extras = sorted(source for source in candidate.sources if source not in SOURCE_LABELS)
    labels.extend(extras)
    return "، ".join(labels)


def observation_queries(candidate: Candidate, limit: int = 10) -> str:
    values: list[str] = []
    seen: set[str] = set()
    for observation in sorted(candidate.observations, key=lambda item: (item.source, item.rank or 999, normalise(item.query))):
        if not observation.query:
            continue
        text = f"{SOURCE_LABELS.get(observation.source, observation.source)}: {display_clean(observation.query)}"
        key = normalise(text)
        if key in seen:
            continue
        seen.add(key)
        values.append(text)
        if len(values) >= limit:
            break
    return " | ".join(values)


def monthly_search_display(candidate: Candidate) -> str:
    if candidate.monthly_searches > 0:
        return f"{candidate.monthly_searches:,.0f}"
    return "—"


def serp_difficulty_display(candidate: Candidate) -> str:
    if candidate.serp_competition_score is None:
        return "اندازه‌گیری نشده"
    return f"{candidate.serp_competition_score:.0f}/100"


def write_opportunities_csv(items: list[Candidate], path: Path) -> None:
    fields = [
        "rank", "keyword", "suggested_title", "suggested_slug", "cluster", "intent",
        "funnel", "coverage_action", "opportunity_score", "demand_score", "gap_score",
        "business_fit_score", "confidence", "trend", "sources", "monthly_searches",
        "monthly_searches_raw", "keyword_planner_competition", "planner_change",
        "gsc_impressions", "gsc_clicks", "gsc_ctr", "gsc_position", "gsc_page",
        "stack_views", "stack_questions", "serp_competition_score", "serp_exact_titles",
        "serp_strong_domains", "serp_user_domain_rank", "existing_similarity",
        "existing_title", "existing_url", "mentioned_in_body", "course_url", "reason",
        "discovery_queries",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, item in enumerate(items, start=1):
            writer.writerow({
                "rank": rank,
                "keyword": item.keyword,
                "suggested_title": item.suggested_title,
                "suggested_slug": item.suggested_slug,
                "cluster": item.cluster_name,
                "intent": item.intent,
                "funnel": item.funnel,
                "coverage_action": item.coverage_action,
                "opportunity_score": item.opportunity_score,
                "demand_score": item.demand_score,
                "gap_score": item.gap_score,
                "business_fit_score": item.business_fit_score,
                "confidence": item.confidence,
                "trend": item.trend_label,
                "sources": source_label(item),
                "monthly_searches": round(item.monthly_searches, 2),
                "monthly_searches_raw": item.monthly_searches_raw,
                "keyword_planner_competition": item.competition_raw,
                "planner_change": item.planner_change,
                "gsc_impressions": round(item.gsc_impressions, 2),
                "gsc_clicks": round(item.gsc_clicks, 2),
                "gsc_ctr": round(item.gsc_ctr, 6),
                "gsc_position": round(item.gsc_position, 2),
                "gsc_page": item.gsc_page,
                "stack_views": round(item.stack_views, 2),
                "stack_questions": item.stack_questions,
                "serp_competition_score": "" if item.serp_competition_score is None else round(item.serp_competition_score, 2),
                "serp_exact_titles": item.serp_exact_titles,
                "serp_strong_domains": item.serp_strong_domains,
                "serp_user_domain_rank": item.serp_user_domain_rank,
                "existing_similarity": round(item.existing_similarity, 4),
                "existing_title": item.existing_title,
                "existing_url": item.existing_url,
                "mentioned_in_body": item.mentioned_in_body,
                "course_url": item.course_url,
                "reason": item.reason,
                "discovery_queries": observation_queries(item),
            })


def write_covered_csv(items: list[Candidate], path: Path) -> None:
    fields = [
        "rank", "keyword", "opportunity_score", "demand_score", "sources",
        "monthly_searches", "gsc_impressions", "existing_similarity", "existing_title",
        "existing_url", "coverage_action", "reason",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, item in enumerate(items, start=1):
            writer.writerow({
                "rank": rank,
                "keyword": item.keyword,
                "opportunity_score": item.opportunity_score,
                "demand_score": item.demand_score,
                "sources": source_label(item),
                "monthly_searches": round(item.monthly_searches, 2),
                "gsc_impressions": round(item.gsc_impressions, 2),
                "existing_similarity": round(item.existing_similarity, 4),
                "existing_title": item.existing_title,
                "existing_url": item.existing_url,
                "coverage_action": item.coverage_action,
                "reason": item.reason,
            })


def candidate_to_dict(item: Candidate) -> dict[str, Any]:
    return {
        "keyword": item.keyword,
        "cluster": item.cluster_name,
        "intent": item.intent,
        "funnel": item.funnel,
        "suggested_title": item.suggested_title,
        "suggested_slug": item.suggested_slug,
        "coverage_action": item.coverage_action,
        "scores": {
            "opportunity": item.opportunity_score,
            "demand": item.demand_score,
            "content_gap": item.gap_score,
            "business_fit": item.business_fit_score,
            "serp_competition": item.serp_competition_score,
        },
        "confidence": item.confidence,
        "trend": item.trend_label,
        "metrics": {
            "monthly_searches": item.monthly_searches,
            "gsc_impressions": item.gsc_impressions,
            "gsc_clicks": item.gsc_clicks,
            "gsc_ctr": item.gsc_ctr,
            "gsc_position": item.gsc_position,
            "stack_views": item.stack_views,
            "stack_questions": item.stack_questions,
        },
        "existing_page": {
            "similarity": item.existing_similarity,
            "title": item.existing_title,
            "url": item.existing_url,
            "mentioned_in_body": item.mentioned_in_body,
        },
        "serp": {
            "checked": item.serp_checked,
            "exact_titles": item.serp_exact_titles,
            "strong_domains": item.serp_strong_domains,
            "user_domain_rank": item.serp_user_domain_rank,
            "top_titles": item.serp_top_titles,
        },
        "sources": sorted(item.sources),
        "reason": item.reason,
        "course_url": item.course_url,
        "observations": [
            {
                "source": observation.source,
                "query": observation.query,
                "family": observation.family,
                "rank": observation.rank,
                "url": observation.url,
                "date": observation.date,
                "value": observation.value,
                "note": observation.note,
            }
            for observation in item.observations
        ],
    }


def write_raw_json(items: list[Candidate], status: dict[str, str], run_date: dt.date, path: Path) -> None:
    payload = {
        "version": SCRIPT_VERSION,
        "run_date": run_date.isoformat(),
        "status": status,
        "candidates": [candidate_to_dict(item) for item in items],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(
    opportunities: list[Candidate],
    covered: list[Candidate],
    status: dict[str, str],
    run_date: dt.date,
    config: dict[str, Any],
    path: Path,
) -> None:
    lines: list[str] = [
        f"# گزارش فرصت‌های محتوایی SEO — {run_date.isoformat()}",
        "",
        f"سایت: **{config['site_name']}**",
        "",
        "> عدد «حجم جست‌وجوی ماهانه» فقط از Keyword Planner خوانده می‌شود. نبود عدد به معنی نبود تقاضا نیست؛ یعنی دادهٔ معتبر ماهانه به برنامه داده نشده است.",
        "",
        "## وضعیت منابع",
        "",
    ]
    for key, value in status.items():
        lines.append(f"- **{key}:** {value}")

    lines.extend([
        "",
        "## اولویت‌های محتوایی",
        "",
        "| رتبه | عبارت | خوشه | نیت | فرصت | تقاضا | شکاف | رقابت SERP | اطمینان |",
        "|---:|---|---|---|---:|---:|---:|---|---|",
    ])
    for rank, item in enumerate(opportunities, start=1):
        lines.append(
            f"| {rank} | {md_escape(item.keyword)} | {md_escape(item.cluster_name)} | "
            f"{md_escape(item.intent)} | {item.opportunity_score:.1f} | {item.demand_score:.1f} | "
            f"{item.gap_score:.1f} | {md_escape(serp_difficulty_display(item))} | {md_escape(item.confidence)} |"
        )

    lines.extend(["", "## بریف محتوایی پیشنهادهای نخست", ""])
    for rank, item in enumerate(opportunities[: int(config["top_content_briefs"])], start=1):
        lines.extend([
            f"### {rank}. {item.suggested_title}",
            "",
            f"- **کلمه هدف:** {item.keyword}",
            f"- **Slug:** `{item.suggested_slug}`",
            f"- **خوشه:** {item.cluster_name}",
            f"- **نیت / مرحله قیف:** {item.intent} / {item.funnel}",
            f"- **امتیاز فرصت:** {item.opportunity_score:.1f}/100",
            f"- **امتیاز تقاضا:** {item.demand_score:.1f}/100",
            f"- **شکاف محتوا:** {item.gap_score:.1f}/100",
            f"- **رقابت SERP:** {serp_difficulty_display(item)}",
            f"- **اطمینان:** {item.confidence}",
            f"- **شواهد:** {item.reason}",
            f"- **لینک دوره:** {item.course_url}",
            "- **ساختار پیشنهادی:**",
        ])
        for heading in outline_for(item):
            lines.append(f"  - {heading}")
        lines.append("")

    lines.extend([
        "## عبارت‌هایی که صفحه متمرکز دارند",
        "",
        "| عبارت | صفحه موجود | شباهت | شواهد |",
        "|---|---|---:|---|",
    ])
    for item in covered:
        if item.existing_url.startswith("http"):
            page = f"[{md_escape(item.existing_title)}]({item.existing_url})"
        else:
            page = md_escape(item.existing_title or item.existing_url)
        lines.append(
            f"| {md_escape(item.keyword)} | {page} | {item.existing_similarity:.0%} | {md_escape(source_label(item))} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_badges(item: Candidate) -> str:
    badges = []
    for source in sorted(item.sources, key=lambda value: SOURCE_LABELS.get(value, value)):
        badges.append(f'<span class="badge">{html_escape(SOURCE_LABELS.get(source, source))}</span>')
    return " ".join(badges)


def score_class(value: float, inverse: bool = False) -> str:
    adjusted = 100.0 - value if inverse else value
    if adjusted >= 72:
        return "good"
    if adjusted >= 48:
        return "medium"
    return "low"


def write_html(
    opportunities: list[Candidate],
    covered: list[Candidate],
    status: dict[str, str],
    run_date: dt.date,
    config: dict[str, Any],
    path: Path,
) -> None:
    status_html = "".join(
        f"<li><strong>{html_escape(key)}:</strong> {html_escape(value)}</li>"
        for key, value in status.items()
    )

    cards: list[str] = []
    for rank, item in enumerate(opportunities[:10], start=1):
        competition = item.serp_competition_score
        competition_html = (
            '<span class="muted">اندازه‌گیری نشده</span>'
            if competition is None
            else f'<span class="metric {score_class(competition, inverse=True)}">{competition:.0f}</span>'
        )
        cards.append(f"""
        <article class="card">
          <div class="rank">{rank}</div>
          <div class="topline">
            <span class="opportunity">فرصت {item.opportunity_score:.1f}</span>
            <span class="confidence">اطمینان: {html_escape(item.confidence)}</span>
          </div>
          <h3>{html_escape(item.suggested_title)}</h3>
          <p class="keyword"><code>{html_escape(item.keyword)}</code></p>
          <div class="badges">{render_badges(item)}</div>
          <div class="score-grid">
            <div><span>تقاضا</span><b class="metric {score_class(item.demand_score)}">{item.demand_score:.0f}</b></div>
            <div><span>شکاف محتوا</span><b class="metric {score_class(item.gap_score)}">{item.gap_score:.0f}</b></div>
            <div><span>تناسب دوره</span><b class="metric {score_class(item.business_fit_score)}">{item.business_fit_score:.0f}</b></div>
            <div><span>رقابت SERP</span>{competition_html}</div>
          </div>
          <div class="details-grid">
            <div><span>خوشه:</span> {html_escape(item.cluster_name)}</div>
            <div><span>نیت:</span> {html_escape(item.intent)}</div>
            <div><span>روند:</span> {html_escape(item.trend_label)}</div>
            <div><span>ماهانه:</span> {monthly_search_display(item)}</div>
          </div>
          <p class="reason">{html_escape(item.reason)}</p>
          <details><summary>بریف مقاله</summary><ol>{''.join(f'<li>{html_escape(value)}</li>' for value in outline_for(item))}</ol></details>
        </article>
        """)

    rows: list[str] = []
    for rank, item in enumerate(opportunities, start=1):
        competition = "—" if item.serp_competition_score is None else f"{item.serp_competition_score:.0f}"
        rows.append(f"""
        <tr>
          <td>{rank}</td>
          <td><strong>{html_escape(item.keyword)}</strong><br><small>{html_escape(item.suggested_title)}</small></td>
          <td>{html_escape(item.cluster_name)}</td>
          <td>{html_escape(item.intent)}</td>
          <td><strong>{item.opportunity_score:.1f}</strong></td>
          <td>{item.demand_score:.1f}</td>
          <td>{item.gap_score:.1f}</td>
          <td>{competition}</td>
          <td>{html_escape(item.confidence)}</td>
          <td>{html_escape(item.trend_label)}</td>
          <td>{monthly_search_display(item)}</td>
          <td>{render_badges(item)}</td>
        </tr>
        """)

    covered_rows: list[str] = []
    for item in covered:
        if item.existing_url.startswith("http"):
            page_link = f'<a href="{html_escape(item.existing_url)}" target="_blank" rel="noopener">{html_escape(item.existing_title)}</a>'
        else:
            page_link = html_escape(item.existing_title or item.existing_url)
        covered_rows.append(f"""
        <tr>
          <td>{html_escape(item.keyword)}</td>
          <td>{item.demand_score:.1f}</td>
          <td>{item.existing_similarity:.0%}</td>
          <td>{page_link}</td>
          <td>{render_badges(item)}</td>
        </tr>
        """)

    html_text = f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>گزارش فرصت‌های SEO — {run_date.isoformat()}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#f4f6fa; color:#182235; font-family:Tahoma,Arial,sans-serif; line-height:1.75; }}
  .wrap {{ max-width:1420px; margin:auto; padding:26px 18px 60px; }}
  .hero {{ background:#fff; border:1px solid #e5e9f1; border-radius:20px; padding:26px; box-shadow:0 12px 34px rgba(24,34,53,.07); }}
  h1,h2,h3 {{ line-height:1.45; }} h1 {{ margin:0 0 8px; }} h2 {{ margin-top:34px; }}
  .notice {{ margin:18px 0; border-right:5px solid #e0a100; background:#fff7d8; border-radius:10px; padding:13px 16px; }}
  .method {{ margin:18px 0; border-right:5px solid #2875d0; background:#edf5ff; border-radius:10px; padding:13px 16px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(350px,1fr)); gap:16px; margin:20px 0 34px; }}
  .card {{ position:relative; background:#fff; border:1px solid #e5e9f1; border-radius:17px; padding:21px; box-shadow:0 8px 25px rgba(24,34,53,.06); }}
  .rank {{ position:absolute; left:17px; top:16px; width:38px; height:38px; border-radius:50%; display:grid; place-items:center; color:#fff; background:#182235; font-weight:bold; }}
  .topline {{ display:flex; flex-wrap:wrap; gap:8px; padding-left:46px; }}
  .opportunity {{ background:#e8f8ee; color:#12653a; border-radius:999px; padding:3px 10px; font-weight:bold; }}
  .confidence {{ background:#eef1f7; border-radius:999px; padding:3px 10px; }}
  .keyword code {{ direction:ltr; unicode-bidi:plaintext; display:inline-block; background:#f1f3f7; padding:4px 8px; border-radius:7px; }}
  .badge {{ display:inline-block; background:#eef1f7; border-radius:999px; padding:2px 9px; margin:2px; font-size:12px; }}
  .score-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:15px 0; }}
  .score-grid > div {{ text-align:center; background:#f7f8fb; border-radius:10px; padding:8px 5px; }}
  .score-grid span {{ display:block; color:#667188; font-size:12px; }}
  .metric {{ font-size:20px; }} .metric.good {{ color:#14804a; }} .metric.medium {{ color:#ad7200; }} .metric.low {{ color:#b33a3a; }}
  .details-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:5px 12px; font-size:14px; }}
  .details-grid span {{ color:#667188; }} .reason {{ font-size:14px; }} .muted {{ color:#7b8497; font-size:13px; }}
  details summary {{ cursor:pointer; font-weight:bold; }}
  .table-wrap {{ overflow:auto; background:#fff; border:1px solid #e5e9f1; border-radius:17px; box-shadow:0 8px 25px rgba(24,34,53,.05); }}
  table {{ width:100%; border-collapse:collapse; min-width:1180px; }}
  th,td {{ text-align:right; vertical-align:top; padding:11px 9px; border-bottom:1px solid #edf0f5; }}
  th {{ position:sticky; top:0; color:#fff; background:#182235; }} tr:hover td {{ background:#fafbfe; }}
  small {{ color:#69758a; }} a {{ color:#175fbd; }} .empty {{ background:#fff; padding:24px; border-radius:16px; }}
  @media(max-width:700px) {{ .score-grid {{ grid-template-columns:1fr 1fr; }} .details-grid {{ grid-template-columns:1fr; }} .hero {{ padding:18px; }} }}
</style>
</head>
<body><div class="wrap">
<section class="hero">
  <h1>گزارش فرصت‌های محتوایی SEO</h1>
  <p><strong>تاریخ:</strong> {run_date.isoformat()} &nbsp; | &nbsp; <strong>سایت:</strong> {html_escape(config['site_name'])}</p>
  <div class="method"><strong>روش امتیازدهی:</strong> تقاضا، شکاف محتوایی سایت، تناسب با دوره و رقابت صفحه نتایج جداگانه سنجیده می‌شوند. تکرار یک seed در modifierهای مختلف، به‌تنهایی امتیاز بالا ایجاد نمی‌کند.</div>
  <div class="notice"><strong>حجم ماهانه:</strong> فقط از Google Ads Keyword Planner خوانده می‌شود. خط تیره یعنی دادهٔ معتبر ماهانه وارد نشده، نه اینکه جست‌وجو صفر است.</div>
  <details open><summary>وضعیت منابع</summary><ul>{status_html}</ul></details>
</section>
<h2>بهترین فرصت‌های امروز</h2>
<div class="grid">{''.join(cards) if cards else '<div class="empty">فرصتی با آستانه فعلی پیدا نشد. اتصال منابع و مقدار minimum_opportunity_score را بررسی کنید.</div>'}</div>
<h2>صف کامل اولویت‌ها</h2>
<div class="table-wrap"><table>
<thead><tr><th>#</th><th>عبارت و عنوان</th><th>خوشه</th><th>نیت</th><th>فرصت</th><th>تقاضا</th><th>شکاف</th><th>رقابت</th><th>اطمینان</th><th>روند</th><th>ماهانه</th><th>منابع</th></tr></thead>
<tbody>{''.join(rows) if rows else '<tr><td colspan="12">موردی یافت نشد.</td></tr>'}</tbody>
</table></div>
<h2>عبارت‌های حذف‌شده به دلیل صفحه موجود</h2>
<div class="table-wrap"><table>
<thead><tr><th>عبارت</th><th>تقاضا</th><th>شباهت</th><th>صفحه موجود</th><th>منابع</th></tr></thead>
<tbody>{''.join(covered_rows) if covered_rows else '<tr><td colspan="5">موردی ثبت نشد.</td></tr>'}</tbody>
</table></div>
</div></body></html>"""
    path.write_text(html_text, encoding="utf-8")


def copy_latest(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def append_run_log(path: Path, status: dict[str, str], opportunities: list[Candidate], run_date: dt.date) -> None:
    lines = [
        f"[{dt.datetime.now().isoformat(timespec='seconds')}] run_date={run_date.isoformat()} opportunities={len(opportunities)}",
    ]
    for key, value in status.items():
        lines.append(f"  {key}: {value}")
    for index, item in enumerate(opportunities[:5], start=1):
        lines.append(f"  TOP{index}: {item.keyword} | opportunity={item.opportunity_score:.1f}")
    lines.append("")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


# =============================================================================
# تلگرام اختیاری
# =============================================================================

def send_telegram(items: list[Candidate], config: dict[str, Any]) -> str:
    token = display_clean(config.get("telegram_bot_token", ""))
    chat_id = display_clean(config.get("telegram_chat_id", ""))
    if not token or not chat_id:
        return "تنظیم نشده"
    if not items:
        return "گزارش خالی بود"

    lines = ["📈 فرصت‌های محتوایی امروز", ""]
    for rank, item in enumerate(items[: int(config["telegram_top_n"])], start=1):
        volume = f" | ماهانه≈{item.monthly_searches:,.0f}" if item.monthly_searches > 0 else ""
        competition = "" if item.serp_competition_score is None else f" | رقابت {item.serp_competition_score:.0f}"
        lines.append(f"{rank}) {item.keyword}")
        lines.append(f"فرصت {item.opportunity_score:.1f} | تقاضا {item.demand_score:.1f}{competition}{volume}")
        lines.append("")
    text = "\n".join(lines)[:3900]
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=int(config["request_timeout_seconds"])) as response:
            response.read()
        return "ارسال شد"
    except Exception as exc:
        return f"خطا: {type(exc).__name__}"


# =============================================================================
# ایمیل گزارش (مناسب GitHub Actions و اجرای محلی)
# =============================================================================

def send_email_report(
    items: list[Candidate],
    paths: dict[str, Path],
    config: dict[str, Any],
    run_date: dt.date,
) -> str:
    """ارسال خلاصه و فایل‌های گزارش با Resend Email API.

    اطلاعات حساس فقط از متغیرهای محیطی خوانده می‌شوند:
      RESEND_API_KEY
    متغیرهای اختیاری:
      RESEND_FROM, EMAIL_TO
    """
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    email_to = display_clean(os.environ.get("EMAIL_TO", config.get("email_to", "")))
    resend_from = display_clean(
        os.environ.get("RESEND_FROM", config.get("resend_from", "Optimization Expert <onboarding@resend.dev>"))
    )
    if not api_key or not email_to:
        return "تنظیم نشده؛ RESEND_API_KEY / EMAIL_TO را بررسی کنید"

    recipients = [value.strip() for value in re.split(r"[,;]", email_to) if value.strip()]
    if not recipients:
        return "گیرنده معتبر نیست"

    top_n = max(1, int(config.get("email_top_n", 12)))
    lines = [
        f"گزارش روزانه فرصت‌های SEO — {run_date.isoformat()}",
        "",
        f"تعداد فرصت‌های جدید: {len(items)}",
        "",
    ]
    if items:
        lines.append("فرصت‌های برتر:")
        for rank, item in enumerate(items[:top_n], start=1):
            monthly = f" | جست‌وجوی ماهانه≈{item.monthly_searches:,.0f}" if item.monthly_searches > 0 else ""
            competition = (
                f" | رقابت={item.serp_competition_score:.0f}"
                if item.serp_competition_score is not None else ""
            )
            lines.append(
                f"{rank}. {item.keyword} | فرصت={item.opportunity_score:.1f} "
                f"| تقاضا={item.demand_score:.1f}{competition}{monthly}"
            )
    else:
        lines.append("امروز فرصت جدیدی با حداقل امتیاز تعیین‌شده پیدا نشد.")

    lines.extend([
        "",
        "فایل HTML، CSV و بریف Markdown به این ایمیل پیوست شده‌اند.",
        "این پیام به‌صورت خودکار توسط GitHub Actions و Resend ارسال شده است.",
    ])

    attachments_payload = []
    attachments = [
        paths.get("latest_html"),
        paths.get("latest_opportunities_csv"),
        paths.get("latest_markdown"),
    ]
    for attachment in attachments:
        if not attachment or not attachment.exists() or not attachment.is_file():
            continue
        attachments_payload.append({
            "filename": attachment.name,
            "content": base64.b64encode(attachment.read_bytes()).decode("ascii"),
        })

    payload: dict[str, Any] = {
        "from": resend_from,
        "to": recipients,
        "subject": f"SEO Opportunity Report | {run_date.isoformat()} | {len(items)} opportunities",
        "text": "\n".join(lines),
    }
    if attachments_payload:
        payload["attachments"] = attachments_payload

    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OptimizationExpert-SEO-Bot/5.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8", errors="replace"))
        message_id = body.get("id", "unknown") if isinstance(body, dict) else "unknown"
        return f"ارسال شد به {', '.join(recipients)}؛ Resend ID={message_id}"
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        return f"خطای Resend HTTP {exc.code}: {detail}"
    except Exception as exc:
        return f"خطا: {type(exc).__name__}: {exc}"


# =============================================================================
# اجرای روزانه با Windows Task Scheduler
# =============================================================================

def parse_clock(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", value)
    if not match:
        raise ValueError("زمان باید مانند 09:00 باشد")
    hour, minute = int(match.group(1)), int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("زمان نامعتبر است")
    return hour, minute


def install_windows_task(base_dir: Path, time_text: str) -> tuple[bool, str]:
    if os.name != "nt":
        return False, "نصب خودکار Task Scheduler فقط روی Windows انجام می‌شود."
    hour, minute = parse_clock(time_text)
    normalized_time = f"{hour:02d}:{minute:02d}"
    script_path = Path(__file__).resolve()
    python_path = Path(sys.executable).resolve()
    batch_path = base_dir / "run_seo_bot_daily.bat"
    config, _config_path = load_config(base_dir)
    output_dir = base_dir / str(config["output_folder"])
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_text = (
        "@echo off\r\n"
        f'cd /d "{base_dir}"\r\n'
        f'"{python_path}" "{script_path}" --output-base "{base_dir}" --no-open '
        f'>> "{output_dir / "scheduled_run.log"}" 2>&1\r\n'
    )
    batch_path.write_text(batch_text, encoding="utf-8")
    command = [
        "schtasks", "/Create", "/TN", WINDOWS_TASK_NAME,
        "/TR", f'cmd.exe /c "{batch_path}"',
        "/SC", "DAILY", "/ST", normalized_time, "/F",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        return False, f"اجرای schtasks ممکن نشد: {exc}"
    output = display_clean((result.stdout or "") + " " + (result.stderr or ""))
    if result.returncode != 0:
        return False, output or f"schtasks return code={result.returncode}"
    return True, f"Task «{WINDOWS_TASK_NAME}» برای ساعت {normalized_time} ساخته شد. {output}"


def remove_windows_task() -> tuple[bool, str]:
    if os.name != "nt":
        return False, "حذف خودکار Task Scheduler فقط روی Windows انجام می‌شود."
    command = ["schtasks", "/Delete", "/TN", WINDOWS_TASK_NAME, "/F"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        return False, f"اجرای schtasks ممکن نشد: {exc}"
    output = display_clean((result.stdout or "") + " " + (result.stderr or ""))
    if result.returncode != 0:
        return False, output or f"schtasks return code={result.returncode}"
    return True, output or f"Task «{WINDOWS_TASK_NAME}» حذف شد."


# =============================================================================
# اجرای کامل
# =============================================================================

def run_once(
    base_dir: Path,
    offline: bool = False,
    open_report: bool = True,
    first_hop_budget: int | None = None,
    second_hop_budget: int | None = None,
    quick: bool = False,
) -> dict[str, Path]:
    base_dir = base_dir.expanduser().resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    config, config_path = load_config(base_dir)
    config["_base_dir"] = str(base_dir)
    if first_hop_budget is not None:
        config["first_hop_queries"] = max(1, first_hop_budget)
    if second_hop_budget is not None:
        config["second_hop_queries"] = max(0, second_hop_budget)
    if quick:
        config["first_hop_queries"] = min(int(config["first_hop_queries"]), 12)
        config["second_hop_queries"] = min(int(config["second_hop_queries"]), 4)
        config["serp_checks_per_run"] = min(int(config["serp_checks_per_run"]), 4)
        config["stackexchange_pagesize"] = min(int(config["stackexchange_pagesize"]), 12)

    run_date = dt.date.today()
    output_dir = base_dir / str(config["output_folder"])
    cache_dir = output_dir / "cache"
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    status: dict[str, str] = {
        "نسخه برنامه": SCRIPT_VERSION,
        "فایل تنظیمات": str(config_path),
        "حالت اجرا": "آفلاین" if offline else ("سریع" if quick else "کامل"),
    }
    store: dict[str, Candidate] = {}

    pages = collect_existing_pages(base_dir, cache_dir, config, offline, status)

    planner_path = find_file(base_dir, str(config.get("keyword_planner_file", "")), KEYWORD_PLANNER_CSV_NAMES)
    if planner_path:
        load_keyword_planner_csv(planner_path, store, status, run_date)
    else:
        status["Keyword Planner"] = "فایل پیدا نشد؛ حجم ماهانه نمایش داده نمی‌شود"

    gsc_csv_path = find_file(base_dir, str(config.get("gsc_csv_file", "")), GSC_CSV_NAMES)
    if gsc_csv_path:
        load_gsc_csv(gsc_csv_path, store, status, run_date)
    else:
        status["Search Console CSV"] = "فایل پیدا نشد"
    collect_gsc_api(store, config, status, run_date)

    if offline:
        for source in SOURCE_FETCHERS:
            status[source] = "حالت آفلاین"
        status["Stack Exchange"] = "حالت آفلاین"
        status["Serper / Google SERP"] = "حالت آفلاین"
    else:
        first_probes = choose_first_hop_probes(
            run_date,
            int(config["first_hop_queries"]),
            bool(config.get("monitor_approved_keywords", True)),
        )
        fixed_count = len(approved_keyword_probes()) if config.get("monitor_approved_keywords", True) else 0
        status["کلمات ثابت پایش‌شده"] = str(fixed_count)
        status["Queryهای اکتشافی مرحله اول"] = str(max(0, len(first_probes) - fixed_count))
        status["کل Queryهای مرحله اول"] = str(len(first_probes))
        collect_all_autocomplete(store, first_probes, cache_dir, config, status, run_date)

        second_probes = build_second_hop_probes(store, int(config["second_hop_queries"]), run_date)
        status["Queryهای مرحله دوم"] = str(len(second_probes))
        second_status: dict[str, str] = {}
        collect_all_autocomplete(store, second_probes, cache_dir, config, second_status, run_date)
        for key, value in second_status.items():
            status[f"{key} — مرحله دوم"] = value

        collect_stackexchange(store, cache_dir, config, status, run_date)
        enrich_with_serper(store, pages, cache_dir, config, status, run_date)

    status["کاندیدای خام"] = str(len(store))
    history_path = output_dir / "opportunity_history.json"
    history = load_history(history_path)
    opportunities, covered, all_items = finalise_candidates(store, pages, history, run_date, config)
    status["فرصت نهایی"] = str(len(opportunities))
    status["حذف‌شده به دلیل صفحه موجود"] = str(len(covered))
    status["Telegram"] = send_telegram(opportunities, config)

    date_text = run_date.isoformat()
    paths = {
        "html": output_dir / f"seo_opportunity_report_{date_text}.html",
        "opportunities_csv": output_dir / f"seo_opportunities_{date_text}.csv",
        "covered_csv": output_dir / f"already_covered_{date_text}.csv",
        "markdown": output_dir / f"content_briefs_{date_text}.md",
        "raw_json": output_dir / f"raw_evidence_{date_text}.json",
        "history": history_path,
        "config": config_path,
    }
    write_opportunities_csv(opportunities, paths["opportunities_csv"])
    write_covered_csv(covered, paths["covered_csv"])
    write_markdown(opportunities, covered, status, run_date, config, paths["markdown"])
    write_html(opportunities, covered, status, run_date, config, paths["html"])
    write_raw_json(all_items, status, run_date, paths["raw_json"])

    latest_paths = {
        "html": output_dir / "seo_opportunity_report_latest.html",
        "opportunities_csv": output_dir / "seo_opportunities_latest.csv",
        "covered_csv": output_dir / "already_covered_latest.csv",
        "markdown": output_dir / "content_briefs_latest.md",
        "raw_json": output_dir / "raw_evidence_latest.json",
    }
    for key, latest_path in latest_paths.items():
        copy_latest(paths[key], latest_path)
    paths.update({f"latest_{key}": value for key, value in latest_paths.items()})

    email_status = send_email_report(opportunities, paths, config, run_date)
    status["Email"] = email_status
    print(f"EMAIL_STATUS: {email_status}", flush=True)

    require_email = os.environ.get("REQUIRE_EMAIL_SUCCESS", "").strip().lower() in {"1", "true", "yes", "on"}
    if require_email and not email_status.startswith("ارسال شد"):
        raise RuntimeError(f"Email delivery failed: {email_status}")

    update_history(history, all_items, opportunities, run_date, config, history_path)
    append_run_log(output_dir / "runs.log", status, opportunities, run_date)

    print("\n" + "=" * 78)
    print("SEO Opportunity Bot v4 — گزارش ساخته شد")
    print(f"فرصت‌های جدید: {len(opportunities)}")
    print(f"عبارت‌های دارای صفحه متمرکز: {len(covered)}")
    print(f"HTML: {latest_paths['html']}")
    print(f"CSV: {latest_paths['opportunities_csv']}")
    print(f"Briefs: {latest_paths['markdown']}")
    print("=" * 78 + "\n")

    should_open = bool(config.get("open_html_report", True)) and open_report
    if should_open and latest_paths["html"].exists():
        try:
            webbrowser.open(latest_paths["html"].as_uri())
        except Exception:
            pass
    return paths


# =============================================================================
# CLI
# =============================================================================

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="کشف روزانه تقاضای جست‌وجو، شکاف محتوا و فرصت‌های SEO برای دوره‌های Optimization Expert"
    )
    parser.add_argument("--offline", action="store_true", help="فقط فایل‌های محلی، GSC CSV و Keyword Planner CSV")
    parser.add_argument("--quick", action="store_true", help="اجرای سبک برای آزمون اولیه")
    parser.add_argument("--no-open", action="store_true", help="گزارش HTML خودکار باز نشود")
    parser.add_argument("--first-hop", type=int, default=None, help="تعداد queryهای مرحله اول")
    parser.add_argument("--second-hop", type=int, default=None, help="تعداد queryهای مرحله دوم")
    parser.add_argument("--output-base", default="", help="پوشه پایه تنظیمات و خروجی؛ پیش‌فرض کنار اسکریپت")
    parser.add_argument("--install-task", metavar="HH:MM", default="", help="ساخت Task روزانه در Windows")
    parser.add_argument("--remove-task", action="store_true", help="حذف Task روزانه Windows")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args, _unknown = parser.parse_known_args()
    base_dir = Path(args.output_base).expanduser().resolve() if args.output_base else script_directory()

    try:
        if args.install_task:
            base_dir.mkdir(parents=True, exist_ok=True)
            load_config(base_dir)
            success, message = install_windows_task(base_dir, args.install_task)
            print(message)
            return 0 if success else 1
        if args.remove_task:
            success, message = remove_windows_task()
            print(message)
            return 0 if success else 1

        run_once(
            base_dir=base_dir,
            offline=bool(args.offline),
            open_report=not bool(args.no_open),
            first_hop_budget=args.first_hop,
            second_hop_budget=args.second_hop,
            quick=bool(args.quick),
        )
        return 0
    except KeyboardInterrupt:
        print("اجرای برنامه توسط کاربر متوقف شد.")
        return 130
    except Exception as exc:
        print(f"خطای پیش‌بینی‌نشده: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
