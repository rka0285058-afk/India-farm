#!/usr/bin/env python3
"""
India: agriculture employs >40% of workers but yields ~16% of GDP.
A transparent, data-anchored model that (1) establishes the stylised facts from
official statistics, (2) quantifies the labour-productivity gap, (3) links it to
land fragmentation and low farm incomes, and (4) stress-tests climate shocks.

Inputs are official-source figures (MoSPI PLFS / National Accounts / NSS 77th
round SAS; Dept. of Agriculture - Agriculture Census 2015-16). Every number is
tagged in DATA with its source. Assumptions are labelled ASSUMPTION.

Outputs (written next to this script):
  agri_model_results.json, agri_model_tables.csv, agri_model_charts.png
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --------------------------------------------------------------------------
# 1. DATA (official sources)
# --------------------------------------------------------------------------
DATA = {
    # MoSPI - PLFS Annual Report 2025 (Jan-Dec 2025)
    "agri_emp_share_2025": 43.0,   # % of workers, usual status
    "agri_emp_share_2024": 44.8,
    "workers_crore_2025": 61.6,    # 41.6 male + 20.0 female
    # MoSPI - National Accounts (GVA, agriculture & allied, share of total GVA)
    # Range across series/estimates: old 2011-12 series ~15-17%, new 2022-23
    # series FY26 ~18%. Stated headline in the question: ~16%.
    "agri_gva_share_headline": 16.0,
    "agri_gva_share_range": (15.0, 18.0),
    # Agriculture Census 2015-16 (Dept. of Agriculture & Farmers Welfare)
    "holdings_thousand": {"Marginal (<1 ha)": 100251, "Small (1-2 ha)": 25809,
                          "Semi-medium (2-4 ha)": 13993, "Medium (4-10 ha)": 5561,
                          "Large (>10 ha)": 838},
    "avg_holding_ha": 1.08,
    # % of operated area by class: marginal 24 (NABARD WP 2025-3 citing census),
    # small+marginal 47.34, semi-medium 23.65, semi-medium+medium 43.61,
    # large 9.07 -> medium derived as 43.61 - 23.65.
    "area_share_pct": {"Marginal (<1 ha)": 24.0, "Small (1-2 ha)": 47.34 - 24.0,
                       "Semi-medium (2-4 ha)": 23.65, "Medium (4-10 ha)": 43.61 - 23.65,
                       "Large (>10 ha)": 9.07},
    # NSS 77th round SAS (July 2018-June 2019), agricultural households
    "sas_income_month": 8337.0,    # NOTE: verify against the NSO report; some
                                   # secondary sources quote a different figure.
    "sas_wage_income_month": 4063.0,
    "sas_lease_income_month": 134.0,
    "sas_avg_loan": 74121.0,
    "sas_indebted_pct": 50.2,
    "sas_crop_cost_month": 3739.0,
    # NABARD working paper 2025-3: threshold farm size for adequate income
    "nabard_threshold_ha": 1.65,
}

OUT = {}

# --------------------------------------------------------------------------
# 2. MODULE A - Sectoral labour productivity gap
# --------------------------------------------------------------------------
def productivity(e, g):
    """e, g = agri share of employment, GVA (fractions). Output & labour = 1."""
    p_a = g / e
    p_n = (1 - g) / (1 - e)
    return p_a, p_n, p_n / p_a

e0 = DATA["agri_emp_share_2025"] / 100
g0 = DATA["agri_gva_share_headline"] / 100
p_a, p_n, ratio = productivity(e0, g0)
OUT["A_baseline"] = {
    "agri_emp_share_pct": e0 * 100, "agri_gva_share_pct": g0 * 100,
    "agri_productivity_rel_to_economy": round(p_a, 3),
    "nonagri_productivity_rel_to_economy": round(p_n, 3),
    "nonagri_to_agri_productivity_ratio": round(ratio, 2),
    "agri_workers_crore": round(DATA["workers_crore_2025"] * e0, 1),
}

emp_grid = [40, 41, 42, 43.0, 44.8, 45]
gva_grid = [15, 16, 17, 18]
sens = pd.DataFrame(
    [[productivity(e / 100, g / 100)[2] for e in emp_grid] for g in gva_grid],
    index=[f"GVA {g}%" for g in gva_grid], columns=[f"Emp {e}%" for e in emp_grid])
OUT["A_sensitivity_ratio_range"] = (round(sens.values.min(), 2), round(sens.values.max(), 2))

# Reallocation scenario: move d pp of workers out of agriculture.
# phi = productivity of movers relative to the non-agri average.
# Agri output held constant (surplus labour) -> gain = d * phi * p_n
# Agri output falls pro-rata (no surplus) -> gain = d * (phi * p_n - p_a)
rows = []
for d in (3, 5, 10):
    for phi in (0.5, 1.0):
        gain_surplus = d / 100 * phi * p_n * 100
        gain_nosurplus = d / 100 * (phi * p_n - p_a) * 100
        rows.append({"shift_pp": d, "phi": phi,
                     "gdp_gain_pct_surplus_labour": round(gain_surplus, 1),
                     "gdp_gain_pct_no_surplus": round(gain_nosurplus, 1)})
realloc = pd.DataFrame(rows)

# --------------------------------------------------------------------------
# 3. MODULE B - Land fragmentation (size-class Lorenz / Gini)
# --------------------------------------------------------------------------
cls = list(DATA["holdings_thousand"])
n = np.array([DATA["holdings_thousand"][c] for c in cls], float) * 1e3
a_sh = np.array([DATA["area_share_pct"][c] for c in cls], float)
a_sh = a_sh / a_sh.sum()
n_sh = n / n.sum()
total_area_mha = n.sum() * DATA["avg_holding_ha"] / 1e6
mean_size = a_sh * total_area_mha * 1e6 / n          # ha per holding, by class
land = pd.DataFrame({"class": cls, "holdings_thousand": n / 1e3,
                     "share_holdings_pct": n_sh * 100, "share_area_pct": a_sh * 100,
                     "avg_size_ha": mean_size})
cx = np.r_[0, np.cumsum(n_sh)]
cy = np.r_[0, np.cumsum(a_sh)]
gini = 1 - np.sum((cx[1:] - cx[:-1]) * (cy[1:] + cy[:-1]))
OUT["B_land"] = {
    "total_operated_area_mha": round(total_area_mha, 1),
    "gini_between_class_lower_bound": round(gini, 3),
    "small_marginal_holdings_pct": round(n_sh[:2].sum() * 100, 1),
    "small_marginal_area_pct": round(a_sh[:2].sum() * 100, 1),
    "large_to_marginal_avg_size_ratio": round(mean_size[-1] / mean_size[0], 1),
    "avg_size_by_class_ha": {c: round(m, 2) for c, m in zip(cls, mean_size)},
}

# --------------------------------------------------------------------------
# 4. MODULE C - Farm-household income and climate stress test
# --------------------------------------------------------------------------
# Income = r * land (land-linked: cultivation, livestock, other) + wages + lease.
# r is calibrated so the *average* holding reproduces the SAS household income.
# ASSUMPTION: constant returns per hectare across size classes (inverse
# size-productivity effects ignored); SAS households and Census holdings are
# different universes, so class incomes are indicative, not survey estimates.
Y = DATA["sas_income_month"]
W = DATA["sas_wage_income_month"]
L = DATA["sas_lease_income_month"]
land_linked_avg = Y - W - L
r = land_linked_avg * 12 / DATA["avg_holding_ha"]          # Rs/ha/year
OUT["C_calibration"] = {
    "wage_share_of_income_pct": round(W / Y * 100, 1),
    "land_linked_income_per_ha_year_rs": round(r),
    "debt_to_annual_income": round(DATA["sas_avg_loan"] / (Y * 12), 2),
}

def class_income(shock=0.0, wage_pass=0.0):
    """wage_pass: share of the shock that also hits wage income (farm-labour
    demand falls in a bad season). 0 = wages unaffected (floor on losses)."""
    return (r * (1 - shock) * mean_size / 12) + W * (1 - wage_pass * shock) + L

inc = land.copy()
inc["income_month_base"] = class_income(0)
inc["income_month_minus10"] = class_income(0.10)
inc["income_month_minus20"] = class_income(0.20)                 # wages unaffected
inc["income_month_minus20_wages_hit"] = class_income(0.20, 1.0)  # wages fall too
inc["wage_dependence_pct"] = W / inc["income_month_base"] * 100
OUT["C_class_income_month"] = {c: round(v) for c, v in zip(cls, inc["income_month_base"])}
OUT["C_climate_stress"] = {
    "avg_holding_income_drop_pct_minus10": round(
        (1 - (r * 0.9 * DATA["avg_holding_ha"] / 12 + W + L) / Y) * 100, 1),
    "avg_holding_income_drop_pct_minus20": round(
        (1 - (r * 0.8 * DATA["avg_holding_ha"] / 12 + W + L) / Y) * 100, 1),
    "marginal_income_drop_pct_minus20_wages_unaffected": round(
        (1 - inc["income_month_minus20"][0] / inc["income_month_base"][0]) * 100, 1),
    "marginal_income_drop_pct_minus20_wages_also_hit": round(
        (1 - inc["income_month_minus20_wages_hit"][0] / inc["income_month_base"][0]) * 100, 1),
    "note": "Shock sizes are ASSUMPTIONS (scenario analysis), not observed data.",
}

# Land needed for an agri household to match "productivity parity"
# ASSUMPTION: earnings scale with sectoral labour productivity.
target = Y * ratio
need_ha = (target - W - L) * 12 / r
share_ge_4ha = n_sh[3:].sum() * 100
OUT["C_parity"] = {
    "target_income_month_rs": round(target),
    "land_needed_ha": round(need_ha, 1),
    "multiple_of_avg_holding": round(need_ha / DATA["avg_holding_ha"], 1),
    "pct_holdings_at_or_above_4ha": round(share_ge_4ha, 1),
    "nabard_threshold_ha": DATA["nabard_threshold_ha"],
    "pct_holdings_below_threshold_approx": round(
        n_sh[:2].sum() * 100 - (0.35 * n_sh[1] * 100), 1),  # small class split at 1.65 ha, ~65% below (linear approx)
}

# --------------------------------------------------------------------------
# 5. Verdict on the stated facts
# --------------------------------------------------------------------------
OUT["verdict"] = {
    "workforce_gt_40pct": DATA["agri_emp_share_2025"] > 40,
    "gva_share_about_16pct_in_official_range": DATA["agri_gva_share_range"][0] <= 16 <= DATA["agri_gva_share_range"][1],
    "productivity_gap_holds_across_all_combinations": bool((sens.values > 2).all()),
}

with open("agri_model_results.json", "w") as f:
    json.dump(OUT, f, indent=2, default=float)
with open("agri_model_tables.csv", "w") as f:
    for name, df in [("sensitivity_nonagri_to_agri_ratio", sens.round(2)),
                     ("land_classes", land.round(2)),
                     ("income_by_class", inc.round(0)),
                     ("reallocation", realloc)]:
        f.write(f"# {name}\n")
        df.to_csv(f)
        f.write("\n")

# --------------------------------------------------------------------------
# 6. Charts (light surface, reference categorical palette: blue, orange)
# --------------------------------------------------------------------------
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e5e4e0", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF,
                     "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
                     "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False})
fig, ax = plt.subplots(2, 3, figsize=(15, 8.6))
fig.suptitle("India agriculture: 43% of workers, ~16% of GVA - what sits behind the gap",
             fontsize=13, x=0.01, ha="left", fontweight="bold")

def barlabels(a, bars, fmt="{:.0f}"):
    for b in bars:
        a.text(b.get_x() + b.get_width() / 2, b.get_height(), fmt.format(b.get_height()),
               ha="center", va="bottom", fontsize=8, color=INK)

def style(a, title, ylabel):
    a.set_title(title, loc="left", fontsize=10, color=INK)
    a.set_ylabel(ylabel)
    a.grid(axis="y", color=GRID, lw=0.8)
    a.set_axisbelow(True)

# (a) workforce vs GVA
a = ax[0, 0]
x = np.arange(2)
w = 0.36
v1 = [e0 * 100, 100 - e0 * 100]
v2 = [g0 * 100, 100 - g0 * 100]
b1 = a.bar(x - w / 2 - 1 / 100, v1, w, color=BLUE, label="Share of workforce (PLFS 2025)")
b2 = a.bar(x + w / 2 + 1 / 100, v2, w, color=ORANGE, label="Share of GVA (MoSPI, ~16%)")
barlabels(a, b1); barlabels(a, b2)
a.set_xticks(x, ["Agriculture", "Non-agriculture"])
a.legend(frameon=False, fontsize=8, loc="upper left")
a.set_ylim(0, 100)
style(a, f"(a) Non-farm worker is ~{ratio:.1f}x as productive", "% of total")

# (b) sensitivity heatmap
a = ax[0, 1]
im = a.imshow(sens.values, cmap="Blues", aspect="auto", vmin=2, vmax=5)
a.set_xticks(range(len(emp_grid)), [f"{e}%" for e in emp_grid])
a.set_yticks(range(len(gva_grid)), [f"{g}%" for g in gva_grid])
for i in range(sens.shape[0]):
    for j in range(sens.shape[1]):
        a.text(j, i, f"{sens.values[i, j]:.1f}x", ha="center", va="center", fontsize=8,
               color="white" if sens.values[i, j] > 3.9 else INK)
a.set_xlabel("Agriculture share of workforce")
a.set_ylabel("Agriculture share of GVA")
a.set_title("(b) Gap survives every official range", loc="left", fontsize=10)
for s in a.spines.values():
    s.set_visible(False)

# (c) Lorenz
a = ax[0, 2]
a.plot([0, 1], [0, 1], color=INK2, lw=1, ls="--", label="Perfect equality")
a.plot(cx, cy, color=BLUE, lw=2, marker="o", ms=5, label=f"Land (Gini >= {gini:.2f})")
a.fill_between(cx, cx, cy, color=BLUE, alpha=0.08)
a.set_xlabel("Cumulative share of holdings (smallest first)")
style(a, "(c) Land concentration, Agri Census 2015-16", "Cumulative share of area")
a.legend(frameon=False, fontsize=8, loc="upper left")

# (d) holdings vs area
a = ax[1, 0]
x = np.arange(len(cls))
b1 = a.bar(x - w / 2 - 0.01, n_sh * 100, w, color=BLUE, label="% of holdings")
b2 = a.bar(x + w / 2 + 0.01, a_sh * 100, w, color=ORANGE, label="% of operated area")
barlabels(a, b1, "{:.0f}"); barlabels(a, b2, "{:.0f}")
a.set_xticks(x, [c.split(" (")[0] + "\n(" + c.split("(")[1] for c in cls], fontsize=8)
a.legend(frameon=False, fontsize=8)
style(a, "(d) 86% of holdings are <2 ha, 47% of land", "%")

# (e) income by class under climate shock
a = ax[1, 1]
b1 = a.bar(x - w / 2 - 0.01, inc["income_month_base"], w, color=BLUE, label="Baseline")
b2 = a.bar(x + w / 2 + 0.01, inc["income_month_minus20_wages_hit"], w, color=ORANGE,
           label="-20% shock, farm wages also fall (assumed)")
barlabels(a, b1, "{:,.0f}"); barlabels(a, b2, "{:,.0f}")
a.set_xticks(x, [c.split(" (")[0] for c in cls], fontsize=8)
a.legend(frameon=False, fontsize=8, loc="upper left")
style(a, "(e) Modelled monthly household income (Rs)", "Rs / month")

# (f) reallocation
a = ax[1, 2]
d = [3, 5, 10]
xx = np.arange(3)
g_half = [realloc[(realloc.shift_pp == k) & (realloc.phi == 0.5)].gdp_gain_pct_surplus_labour.iloc[0] for k in d]
g_full = [realloc[(realloc.shift_pp == k) & (realloc.phi == 1.0)].gdp_gain_pct_surplus_labour.iloc[0] for k in d]
b1 = a.bar(xx - w / 2 - 0.01, g_half, w, color=BLUE, label="Movers earn 50% of non-farm avg")
b2 = a.bar(xx + w / 2 + 0.01, g_full, w, color=ORANGE, label="Movers earn 100% of non-farm avg")
barlabels(a, b1, "{:.1f}"); barlabels(a, b2, "{:.1f}")
a.set_xticks(xx, [f"{k} pp of workers\nleave farming" for k in d])
a.legend(frameon=False, fontsize=8, loc="upper left")
style(a, "(f) GDP gain from labour reallocation (%)", "% of GDP (surplus-labour case)")

fig.text(0.01, 0.005,
         "Sources: MoSPI PLFS Annual Report 2025; MoSPI National Accounts; NSS 77th round SAS (2018-19); "
         "Agriculture Census 2015-16; NABARD WP 2025-3. Panels (e),(f) are scenario outputs.",
         fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.02, 1, 0.96))
fig.savefig("agri_model_charts.png", dpi=150)

print(json.dumps(OUT, indent=2, default=float))
print(sens.round(2).to_string())
print(realloc.to_string(index=False))
print(inc.round(0).to_string(index=False))
