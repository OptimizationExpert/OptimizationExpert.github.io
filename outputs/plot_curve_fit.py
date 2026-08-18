import numpy as np
import matplotlib.pyplot as plt

# --- raw / historical data (used to fit the curve) ---
data = {
    2024: {"low": 43.36, "mid": 43.36, "high": 43.36},
    2025: {"low": 44.17, "mid": 45.38, "high": 46.25},
    2026: {"low": 45.32, "mid": 47.26, "high": 49.10},
    2027: {"low": 46.25, "mid": 49.09, "high": 51.81},
    2028: {"low": 47.05, "mid": 50.64, "high": 54.06},
    2029: {"low": 47.85, "mid": 52.18, "high": 56.26},
    2030: {"low": 48.64, "mid": 53.72, "high": 58.36},
    2031: {"low": 49.42, "mid": 55.21, "high": 60.23},
    2032: {"low": 50.14, "mid": 56.57, "high": 61.89},
    2033: {"low": 50.85, "mid": 57.81, "high": 63.30},
    2034: {"low": 51.52, "mid": 58.92, "high": 64.49},
    2035: {"low": 52.19, "mid": 59.90, "high": 65.58},
}

# --- previously computed forecast (2036-2041), added here so it can be
#     plotted next to the freshly-fitted curve for a sanity check ---
forecast = {
    2036: {"low": 52.74, "mid": 60.94, "high": 66.45},
    2037: {"low": 53.30, "mid": 61.82, "high": 67.12},
    2038: {"low": 53.82, "mid": 62.62, "high": 67.61},
    2039: {"low": 54.31, "mid": 63.32, "high": 67.90},
    2040: {"low": 54.77, "mid": 63.94, "high": 67.99},
    2041: {"low": 55.18, "mid": 64.47, "high": 67.89},
}

years_actual = np.array(sorted(data.keys()))
x_actual = years_actual - years_actual[0]  # 0..11, x=0 at 2024

years_forecast = np.array(sorted(forecast.keys()))
x_forecast = years_forecast - years_actual[0]

series_names = ["low", "mid", "high"]
colors = {"low": "tab:blue", "mid": "tab:orange", "high": "tab:green"}

# years to extrapolate through (2024..2041) — the curve is fit ONLY on
# `data` (2024-2035); `forecast` values above are plotted separately as
# points so you can visually check them against the fitted curve.
years_full = np.arange(2024, 2042)
x_full = years_full - years_actual[0]

fig, ax = plt.subplots(figsize=(9, 6))

for name in series_names:
    y_actual = np.array([data[yr][name] for yr in years_actual])

    # fit a quadratic: y = a + b*x + c*x^2  (np.polyfit returns highest degree first)
    coeffs = np.polyfit(x_actual, y_actual, deg=2)
    poly = np.poly1d(coeffs)

    y_fit_full = poly(x_full)

    # print the equation and fit quality so you can check it yourself
    c2, c1, c0 = coeffs
    y_fit_on_actual = poly(x_actual)
    residuals = y_actual - y_fit_on_actual
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_actual - y_actual.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    print(f"{name}: y = {c0:.4f} + {c1:.4f}*x + {c2:.5f}*x^2   (R^2 = {r2:.5f})")
    print(f"  {name} forecast 2036-2041:",
          [round(v, 2) for v in y_fit_full[years_full >= 2036]])

    y_forecast_given = np.array([forecast[yr][name] for yr in years_forecast])

    ax.plot(years_full, y_fit_full, color=colors[name], label=f"{name} fit")
    ax.scatter(years_actual, y_actual, color=colors[name], marker="o", zorder=5,
               label=f"{name} actual" if name == series_names[0] else None)
    ax.scatter(years_forecast, y_forecast_given, color=colors[name], marker="x",
               s=60, zorder=5, label=f"{name} given forecast" if name == series_names[0] else None)

ax.axvline(2035, color="gray", linestyle="--", linewidth=1)
ax.set_xlabel("Year")
ax.set_ylabel("Value")
ax.set_title("Actual data (dots) vs quadratic curve fit (lines), extrapolated to 2041")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("curve_fit_forecast.png", dpi=150)
plt.show()
