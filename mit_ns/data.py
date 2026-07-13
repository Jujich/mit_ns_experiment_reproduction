"""Data loading helpers."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mit_ns import DATA_DIR, DV_COEFFICIENTS, LEGACY_CSV_DIR, ROOT


def _resolve(name: str) -> Path:
    for base in (LEGACY_CSV_DIR, DATA_DIR, ROOT):
        path = base / name
        if path.exists():
            return path
    raise FileNotFoundError(f"Cannot find data file: {name}")


def load_interaction_matrix() -> np.ndarray:
    path = _resolve("input_matrix_figure_6_1.csv")
    df = pd.read_csv(path, index_col=0)
    return df.to_numpy(dtype=float)


def load_dv_coefficients() -> dict[str, int]:
    path = _resolve("dv_coefficients.csv")
    row = pd.read_csv(path).iloc[0]
    return {k: int(row[k]) for k in row.index}


def load_table_9_1() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "table_9_1_dv_comparison.csv")


def load_table_9_2() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "table_9_2_cost_estimates.csv")


def load_capital_costs() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "capital_costs_ch9.csv")


def load_thesis_savings_ranges() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "thesis_savings_ranges.csv")


def load_system_labels() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "system_labels.csv")


def load_design_constraints() -> dict:
    with open(DATA_DIR / "design_constraints.json", encoding="utf-8") as f:
        return json.load(f)


def compute_historical_dv(mom: float, mav: float, pprv: float, cvv: float, mfv: float) -> float:
    c = DV_COEFFICIENTS
    return (
        c["A1_MOM"] * mom
        + c["A2_MAV"] * mav
        + c["A3_PPRV"] * pprv
        + c["A4_CVV"] * cvv
        + c["A5_MFV"] * mfv
    )
