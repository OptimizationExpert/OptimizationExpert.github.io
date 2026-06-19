---
layout: post
title: "Solver خوب بدون رنگ برای Pyomo؟ سه راهکار عملی"
date: 2026-06-19
display_date: "۲۹ خرداد ۱۴۰۵"
description: "سه راه برای نصب و استفاده از Solver های رایگان برای Pyomo: نصب محلی، Google Colab، و سرور NEOS."
---

وقتی می‌خوای با Pyomo مدل‌سازی کنی، اول باید یک **Solver** داشته باشی. مسئله اینه که خیلی از solverهای خوب (Gurobi، CPLEX) رایگان نیستن. ولی خیلی راهکار رایگان و قابل‌اعتماد هم هست. اینجا سه تا بهترین گزینه رو معرفی می‌کنم.

---

## ۱) نصب روی کامپیوتر شما (بهترین گزینه برای کار طولانی‌مدت)

اگر می‌خوای solver رو مستقیم روی سیستم خودت داشته باشی:

**لازم است:** Anaconda یا Miniconda نصب داشته باشی. دانلود کن از: https://www.anaconda.com/

**سپس کافیه این کامند رو اجرا کنی:**

```bash
conda install -c conda-forge pyomo.solvers
```

این دستور خودکار این سه تا solver معروف و رایگان رو نصب می‌کنه:
- **GLPK** — خطی و صحیح (Linear & Integer Programming)
- **CBC** — صحیح (Integer Programming) — سریع‌تر از GLPK
- **IPOPT** — غیرخطی (Nonlinear Programming)

⚠️ **نکته مهم:** ورژن Python و Anaconda مهمه. اگر از یک نسخه‌ی خیلی جدید استفاده کنی و بعدش مشکل پیش بیاد، دوباره نصب هم سختTR خواهد بود. بهتره از ورژن Python **۳.۷ یا ۳.۹** شروع کنی.

**بعد از نصب، این کد رو تست کن:**

```python
from pyomo.environ import *

m = ConcreteModel()
m.x = Var(within=NonNegativeReals)
m.obj = Objective(expr=m.x**2)

opt = SolverFactory('ipopt')
opt.solve(m)
print(value(m.x))
```

اگر بدون خطا اجرا شد، بشاد! Solver شما آماده‌ست.

---

## ۲) Google Colab (بدون نصب، درست در مرورگر)

اگر نمی‌خوای چیزی نصب کنی یا سیستمت ضعیفه، Google Colab بهترین گزینه است.

**کل کاری که باید کنی:**

1. این لینک رو باز کن:
[   https://colab.research.google.com/github/OptimizationExpert/Pyomo/blob/main/Pyomo_on_Google_Colab.ipynb
](link)
2. حساب Google خودت رو لاگین کن (رایگان).

3. سلول‌های کد (cell) رو یکی بعد از دیگری اجرا کن (دکمه‌ی ▶ یا Shift+Enter).

Colab خودش Pyomo رو نصب می‌کنه و solver هم آماده می‌کنه. دیگر نیاز به نصب محلی نیست.

**مزیت:** سریع، رایگان، هیچ سختافزار نمی‌خواد.
**نقص:** بعد از بسته‌شدن کپی، باید دوباره solver نصب کنی (ولی الگوریتم ذخیره می‌شه).

---

## ۳) سرور NEOS (بدون نصب، solving انلاین)

برای مسائل کوچک‌تر و یکی‌دفعه، می‌تونی از **NEOS Server** استفاده کنی — یک سرور رایگان که solver رو آنلاین اجرا می‌کنه.

**شرط:** اتصال به اینترنت لازمه؛ مدل ترجیحاً کوچک باشه.

**نحوه‌ی استفاده:**

```python
from pyomo.environ import *

m = ConcreteModel()
m.x = Var(within=NonNegativeReals)
m.obj = Objective(expr=m.x**2 - 4*m.x)

# استفاده از NEOS
mgr = SolverManagerFactory('neos')
res = mgr.solve(m, opt='ipopt')

print(value(m.obj))
```

بیشتر جزئیات و نمونه‌های کامل در لینک زیر هست:
https://t.me/c/1349591965/4050

---

## مقایسه سریع

| راهکار | نصب | سرعت | مناسب برای |
|---|---|---|---|
| **کامپیوتر شخصی** | یک‌بار | ⚡⚡⚡ سریع | پروژه‌های طولانی و بزرگ |
| **Google Colab** | ❌ ندارد | ⚡⚡ متوسط | یادگیری و تست کوتاه‌مدت |
| **NEOS Server** | ❌ ندارد | ⚡ کند | مسائل کوچک و شنایی‌بخشی |

---

## نتیجه

اگر تازه شروع کردی و می‌خوای بدون سردرد امتحان کنی: **Google Colab** بهترین است.

اگر قصد داری پروژه‌ی جدی بسازی: **نصب محلی** لازمه.

برای سریع و خیلی ساده: **NEOS Server**.

**برای کمک و سؤال:** در تلگرام @pypyid پیام بده یا به کانال بپیوند.
https://t.me/pyomochannel
---

