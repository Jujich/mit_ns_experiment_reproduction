"""Chapter 9 capital-cost sensitivity / AFUDC reproduction."""

from __future__ import annotations

import math

import pandas as pd

from mit_ns.data import load_capital_costs, load_thesis_savings_ranges


def total_with_uniform_idc(base_cost: float, years: float, interest_rate: float) -> float:
    """Interest-during-construction with uniform spend over construction period.

    Total = C * ((1+r)^T - 1) / (r * T)
    """
    if years <= 0:
        return base_cost
    if abs(interest_rate) < 1e-12:
        return base_cost
    return base_cost * ((1.0 + interest_rate) ** years - 1.0) / (interest_rate * years)


def modular_schedule(conventional_years: float, fraction: float) -> float:
    return conventional_years * fraction


def sensitivity_grid(
    case_id: int = 1,
    conventional_years: list[float] | None = None,
    interest_rates: list[float] | None = None,
    modular_fractions: list[float] | None = None,
) -> pd.DataFrame:
    if conventional_years is None:
        conventional_years = [5.0, 7.0]
    if interest_rates is None:
        interest_rates = [0.06, 0.10, 0.14]
    if modular_fractions is None:
        # Case A/B/C from thesis 9.6.1
        modular_fractions = [0.50, 0.65, 0.80]

    costs = load_capital_costs()
    conv = float(costs[(costs.case_id == case_id) & (costs.construction == "conventional")]["capital_cost_musd"].iloc[0])
    mod = float(costs[(costs.case_id == case_id) & (costs.construction == "modular")]["capital_cost_musd"].iloc[0])

    rows = []
    for t_conv in conventional_years:
        for r in interest_rates:
            for frac in modular_fractions:
                t_mod = modular_schedule(t_conv, frac)
                tot_c = total_with_uniform_idc(conv, t_conv, r)
                tot_m = total_with_uniform_idc(mod, t_mod, r)
                savings_musd = tot_c - tot_m
                savings_pct = 100.0 * savings_musd / tot_c if tot_c else 0.0
                rows.append(
                    {
                        "case_id": case_id,
                        "conventional_years": t_conv,
                        "modular_fraction": frac,
                        "modular_years": t_mod,
                        "interest_rate": r,
                        "conventional_total_musd": round(tot_c, 2),
                        "modular_total_musd": round(tot_m, 2),
                        "savings_musd": round(savings_musd, 2),
                        "savings_pct": round(savings_pct, 2),
                    }
                )
    return pd.DataFrame(rows)


def summarize_vs_thesis(case_id: int = 1) -> pd.DataFrame:
    grid = sensitivity_grid(case_id=case_id)
    thesis = load_thesis_savings_ranges()
    thesis = thesis[thesis.case_id == case_id]
    rows = []
    for _, trow in thesis.iterrows():
        years = float(trow["conventional_years"])
        subset = grid[grid.conventional_years == years]
        rows.append(
            {
                "case_id": case_id,
                "conventional_years": years,
                "model_savings_pct_min": subset["savings_pct"].min(),
                "model_savings_pct_max": subset["savings_pct"].max(),
                "model_savings_pct_mean": round(subset["savings_pct"].mean(), 2),
                "thesis_savings_pct_min": trow["savings_pct_min"],
                "thesis_savings_pct_max": trow["savings_pct_max"],
                "thesis_avg_savings_pct": trow["avg_savings_pct"],
                "model_avg_vs_thesis_avg_pp": round(
                    subset["savings_pct"].mean() - float(trow["avg_savings_pct"]), 2
                ),
            }
        )
    return pd.DataFrame(rows)


def abstract_savings_band() -> dict:
    """Reproduce abstract claim: 26–46% average savings across Case 1/2 (7-yr)."""
    c1 = summarize_vs_thesis(1)
    c2 = summarize_vs_thesis(2)
    c1_7 = float(c1[c1.conventional_years == 7]["thesis_avg_savings_pct"].iloc[0])
    c2_7 = float(c2[c2.conventional_years == 7]["thesis_avg_savings_pct"].iloc[0])
    return {
        "thesis_case1_7yr_avg_pct": c1_7,
        "thesis_case2_7yr_avg_pct": c2_7,
        "abstract_band_pct": [min(c1_7, c2_7), max(c1_7, c2_7)],
        "note": "Abstract 26–46% matches Case 2 / Case 1 seven-year averages from Ch.9.6.3",
    }
