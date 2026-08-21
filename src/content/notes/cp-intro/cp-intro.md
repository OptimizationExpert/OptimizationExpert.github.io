---
title: "حل همه جواب‌ها با OR-Tools"
description: "آموزش پیدا کردن همه جواب‌های یک مدل با Constraint Programming در OR-Tools؛ همراه با یک مثال ساده و قابل اجرا در Python برای درک enumerate کردن جواب‌ها."
pubDate: 2026-08-07
author: "dr-soroudi"
minimalImage: "./cp-intro-mini.webp"
minimalImageAlt: "تصویر مینیمال آیکون بهینه‌سازی"
image: "./cp-intro.webp"
imageAlt: "حل همه جواب‌ها با OR-Tools و Constraint Programming | پایتون"
tags: ["CP", "پازل ریاضی", "Constraint Programming"]
relatedCourses: ["vrp-python"]
relatedNotes: ["mathematical-modeling-art", "google-colab", "pyomo-solvers"]
---

## مرور مفهوم CP با OR-Tools

امروز می‌خواهیم با یک مسئله‌ی ساده شروع کنیم و مفهوم **Constraint Programming (CP)** را مرور کنیم.

### صورت مسئله

مسئله‌ی زیر را در نظر بگیرید:

$$
\begin{aligned}
\max \quad & x+y \\
\text{s.t.} \quad & x+5y \leq 2 \\
& x,y \in \{0,1,2\}
\end{aligned}
$$

همان‌طور که می‌بینید، متغیرهای تصمیم ما یعنی $x$ و $y$، متغیرهای **Integer** هستند و نمی‌توانند هر مقدار دلخواهی بگیرند.

دامنه‌ی هر متغیر برابر است با:

$$
D(x)=D(y)=\{0,1,2\}
$$

اما این موضوع چه چیزی به ما می‌گوید؟

در این مسئله باید به‌صورت هم‌زمان دو بخش را در نظر بگیریم:

1. **تابع هدف** که قرار است بیشینه شود؛
2. **قیود مسئله** که مشخص می‌کنند چه ترکیب‌هایی از متغیرها مجاز هستند.

تابع هدف ما برابر است با:

$$
\max(x+y)
$$

و قید مسئله برابر است با:

$$
x+5y\leq2
$$

بنابراین، وقتی مقداری برای $x$ انتخاب می‌کنیم، دیگر نمی‌توانیم هر مقدار دلخواهی را برای $y$ در نظر بگیریم.

در واقع، مقادیر متغیرها به‌واسطه‌ی قیود به یکدیگر وابسته می‌شوند. این دقیقاً یکی از ایده‌های اصلی در **Constraint Programming** است.

---

### پیاده‌سازی مسئله در OR-Tools

برای حل مسئله از سالوری **CP-SAT** در کتابخانه‌ی OR-Tools استفاده می‌کنیم.

```python
from ortools.sat.python import cp_model
model = cp_model.CpModel()
x = model.new_int_var(0, 2, "x")
y = model.new_int_var(0, 2, "y")
model.add(x + 5 * y <= 2)
model.maximize(x + y)
solver = cp_model.CpSolver()
status = solver.solve(model)
print(solver.status_name(status))
print("OF =", solver.objective_value)
print(f"x = {solver.value(x)}, y = {solver.value(y)}")
```

در این قسمت ابتدا متغیرهای $x$ و $y$ را تعریف کرده‌ایم:

```python
x = model.new_int_var(0, 2, "x")
y = model.new_int_var(0, 2, "y")
```

بنابراین:

$$
x,y\in\{0,1,2\}
$$

سپس قید زیر را به مدل اضافه کرده‌ایم:

```python
model.add(x + 5 * y <= 2)
```

که معادل رابطه‌ی ریاضی زیر است:

$$
x+5y\leq2
$$

در نهایت تابع هدف را مشخص می‌کنیم:

```python
model.maximize(x + y)
```
یعنی:
$$
\max(x+y)
$$

---

## پیدا کردن تمام جواب‌های Feasible

تا اینجا از Solver خواستیم که مسئله‌ی بهینه‌سازی را حل کند و بهترین جواب را پیدا کند.
اما یک سؤال مهم مطرح می‌شود:

> اگر به‌جای بهترین جواب، بخواهیم **تمام جواب‌های feasible** مسئله را پیدا کنیم، چه کاری باید انجام دهیم؟

برای این کار می‌توانیم از کلاس زیر
استفاده کنیم.

```python
CpSolverSolutionCallback
```
یک Callback می‌سازیم که هر بار Solver یک جواب feasible پیدا کرد، مقادیر متغیرها را چاپ کند.

```python
class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print all intermediate solutions."""
    def __init__(self, variables: list[cp_model.IntVar]):
        super().__init__()

        self.__variables = variables
        self.__solution_count = 0

    def on_solution_callback(self) -> None:
        self.__solution_count += 1
        print(f"Solution {self.__solution_count}")
        for variable in self.__variables:
            print(
                f"{variable} = {self.value(variable)}",
                end=" ")
        print()

    @property
    def solution_count(self) -> int:
        return self.__solution_count
```

هر بار که Solver یک جواب جدید پیدا کند، متد
زیر فراخوانی می‌شود.

```python
on_solution_callback()
```
متغیر مقابل 
نیز تعداد جواب‌های پیدا شده را نگه می‌دارد.
```python
self.__solution_count
```
---

### Enumerate کردن تمام جواب‌ها

اکنون می‌توانیم مدل را بدون تابع هدف تعریف کنیم و از Solver بخواهیم تمام جواب‌های feasible را پیدا کند.

```python
def all_solutions_sample_sat():
    model = cp_model.CpModel()
    x = model.new_int_var(0, 2, "x")
    y = model.new_int_var(0, 2, "y")
    model.add(x + 5 * y <= 2)
    solver = cp_model.CpSolver()
    solution_printer = VarArraySolutionPrinter([x, y])
    solver.parameters.enumerate_all_solutions = True
    status = solver.solve(
        model,
        solution_printer)

    print(f"Status = {solver.status_name(status)}")
    print(
        f"Number of solutions found: "
        f"{solution_printer.solution_count}"
    )
all_solutions_sample_sat()
```

نکته‌ی مهم در این قسمت خط زیر است:

```python
solver.parameters.enumerate_all_solutions = True
```

با فعال کردن این گزینه، Solver جست‌وجو را بعد از پیدا کردن اولین جواب متوقف نمی‌کند و تمام جواب‌های feasible را بررسی می‌کند.


## بررسی جواب‌های Feasible 
برای اینکه بهتر متوجه مسئله شویم، دوباره قید را در نظر بگیریم:

$$
x+5y\leq2,\qquad x,y\in{0,1,2}
$$

اگر $y=0$ باشد، قید تبدیل می‌شود به

$$
x\leq2
$$

بنابراین سه جواب feasible داریم:

$$
(x,y)\in{(0,0),(1,0),(2,0)}
$$

اما اگر $y=1$ باشد، خواهیم داشت

$$
x+5\leq2
$$

که امکان‌پذیر نیست. برای $y=2$ نیز داریم

$$
x+10\leq2
$$

که باز هم امکان‌پذیر نیست.

در نتیجه مجموعه‌ی جواب‌های feasible برابر است با

$$
\mathcal{F}={(0,0),(1,0),(2,0)}
$$

اگر دوباره تابع هدف را در نظر بگیریم:

$$
\max(x+y)
$$
مقادیر تابع هدف برای جواب‌های feasible به‌صورت زیر هستند:
$$
f(0,0)=0,\qquad
f(1,0)=1,\qquad
f(2,0)=2
$$
بنابراین جواب بهینه برابر است با

$$
x^*=2,\qquad y^*=0,\qquad z^*=2
$$


---

## اگر فقط $n$ جواب بخواهیم چه؟

حالا فرض کنید تمام جواب‌های feasible را نمی‌خواهیم و فقط می‌خواهیم Solver بعد از پیدا کردن $n$ جواب متوقف شود.

برای این کار می‌توانیم Callback قبلی را کمی تغییر دهیم و یک **limit** برای تعداد جواب‌ها تعریف کنیم.

```python
class VarArraySolutionPrinterNSolutions(
    cp_model.CpSolverSolutionCallback
):
    def __init__(
        self,
        variables: list[cp_model.IntVar],
        n: int
    ):
        super().__init__()
        self.__variables = variables
        self.__solution_count = 0
        self.__limit = n

    def on_solution_callback(self) -> None:
        self.__solution_count += 1
        print(f"Solution {self.__solution_count}")
        for variable in self.__variables:
            print( f"{variable} = {self.value(variable)}", end=" " )

        print()
        if self.__solution_count == self.__limit:
            self.stop_search()

    @property
    def solution_count(self) -> int:
        return self.__solution_count
```

تفاوت اصلی در این قسمت است:

```python
if self.__solution_count == self.__limit:
    self.stop_search()
```

یعنی هر زمان تعداد جواب‌های پیدا شده به مقدار تعیین‌شده برسد، جست‌وجوی Solver متوقف می‌شود.

---

### مثال: پیدا کردن فقط دو جواب

برای مثال، اگر بخواهیم فقط دو جواب feasible پیدا کنیم:

```python
def all_solutions_sample_sat_nsolution():
    model = cp_model.CpModel()
    x = model.new_int_var(0, 2, "x")
    y = model.new_int_var(0, 2, "y")
    model.add(x + 5 * y <= 2)
    solver = cp_model.CpSolver()
    solution_printer = VarArraySolutionPrinterNSolutions(
        [x, y],2)
    solver.parameters.enumerate_all_solutions = True
    status = solver.solve(model, solution_printer)
    print(f"Status = {solver.status_name(status)}")
    print(
        f"Number of solutions found: "
        f"{solution_printer.solution_count}"
    )
all_solutions_sample_sat_nsolution()
```

در این مثال مقدار

```python
n=2
```

به Callback ارسال شده است:

```python
VarArraySolutionPrinterNSolutions([x, y], 2)
```

بنابراین Solver بعد از پیدا کردن دو جواب، جست‌وجو را متوقف می‌کند.

---

## جمع‌بندی

در این مثال ساده چند مفهوم مهم در **Constraint Programming** را دیدیم.

ابتدا دامنه‌ی متغیرها را مشخص کردیم:

$$
D(x)=D(y)=\{0,1,2\}
$$

سپس یک قید بین متغیرها تعریف کردیم:

$$
x+5y\leq2
$$

این قید باعث شد همه‌ی ترکیب‌های ممکن از $x$ و $y$ قابل قبول نباشند و فضای جواب از

$$
3\times3=9
$$

حالت ممکن، به فقط سه جواب feasible کاهش پیدا کند:

$$
\mathcal{F}
=
\{(0,0),(1,0),(2,0)\}
$$

سپس دیدیم که در OR-Tools می‌توانیم سه نوع جست‌وجو داشته باشیم:

- پیدا کردن جواب بهینه؛
- پیدا کردن تمام جواب‌های feasible؛
- پیدا کردن فقط $n$ جواب feasible.

این مثال ساده مقدمه‌ای برای درک یکی از ایده‌های اصلی CP است:

> **متغیرها دارای دامنه هستند و قیود، مقادیر سازگار در این دامنه‌ها را مشخص می‌کنند.**

در مسائل بزرگ‌تر، قدرت Constraint Programming زمانی بیشتر مشخص می‌شود که قیود مختلف باعث حذف بخش بزرگی از فضای جست‌وجو شوند.

اگر می‌خواهید مدل‌سازی و حل کامل مسایل پیچیده تر رو در Python با OR-Tools قدم‌به‌قدم یاد بگیرید، این موضوع در <a href="/courses/vrp-python/" class="content-link">دوره بهینه‌سازی حمل و نقل </a> به‌صورت پروژه‌محور پوشش داده شده است.
