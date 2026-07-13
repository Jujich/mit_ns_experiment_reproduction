"""DV-proxy objective: MOM from partition + surrogates for MAV/CVV/MFV/PPRV.

Without full pipe/layout geometry we cannot recompute true PPRV/MAV/CVV/MFV.
Surrogates use thesis formulas + partition-derived statistics so that optimizers
can minimize a Design-Value-like scalar and we can compare to cut-only mode.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np

from mit_ns import A1_MOM, A2_MAV, A3_PPRV, A4_CVV, A5_MFV, SH2_CVV, SH2_MAV, SH2_MFV, SH2_PPRV
from mit_ns.objective import inter_module_cut


@dataclass
class DVProxyComponents:
    mom: float
    mav: float
    pprv: float
    cvv: float
    mfv: float
    cut: int
    dv: float


def mom_from_partition(matrix: np.ndarray, assignment: np.ndarray) -> float:
    """MOM proxy = inter-module cut (same units as thesis MBIV sum for interfaces)."""
    return float(inter_module_cut(matrix, assignment))


def mav_surrogate(assignment: np.ndarray, k: int, baseline_mav: float = SH2_MAV) -> float:
    """Prefer balanced module sizes (lower variance → lower MAV).

    Calibrated so equal-size K-module partitions sit near Modular SH II MAV.
    """
    sizes = np.array(list(Counter(assignment).values()), dtype=float)
    if len(sizes) == 0:
        return baseline_mav
    mean = sizes.mean()
    cv = float(sizes.std() / max(mean, 1e-9))
    # imbalance + using wrong k relative to preferred mid-range
    k_penalty = abs(k - 5) * 40.0
    return baseline_mav * (0.85 + 0.5 * cv) + k_penalty


def cvv_surrogate(assignment: np.ndarray, k: int, baseline_cvv: float = SH2_CVV) -> float:
    """More modules / more imbalance → more boundary concrete / forms."""
    sizes = np.array(list(Counter(assignment).values()), dtype=float)
    imbalance = float(sizes.std() / max(sizes.mean(), 1e-9))
    return baseline_cvv * (0.92 + 0.03 * k + 0.15 * imbalance)


def mfv_surrogate(assignment: np.ndarray, k: int, baseline_mfv: float = SH2_MFV) -> float:
    """MFV grows with number of distinct module geometries (size classes)."""
    sizes = tuple(sorted(Counter(assignment).values()))
    n_styles = len(set(sizes))
    return baseline_mfv * (0.7 + 0.08 * k + 0.15 * n_styles)


def pprv_surrogate(matrix: np.ndarray, assignment: np.ndarray, baseline_pprv: float = SH2_PPRV) -> float:
    """Pipe penalty grows with inter-module interface weight (cut)."""
    cut = mom_from_partition(matrix, assignment)
    # scale relative to Modular SH II cut≈ historical MOM 1180
    return baseline_pprv * (0.5 + 0.5 * (cut / max(SH2_MOM_REF, 1.0)))


SH2_MOM_REF = 1180.0


def evaluate_dv_proxy(
    matrix: np.ndarray,
    assignment: np.ndarray,
    k: int | None = None,
    freeze_pprv: bool = False,
) -> DVProxyComponents:
    if k is None:
        k = len(set(assignment))
    cut = inter_module_cut(matrix, assignment)
    mom = float(cut)
    mav = mav_surrogate(assignment, k)
    cvv = cvv_surrogate(assignment, k)
    mfv = mfv_surrogate(assignment, k)
    pprv = SH2_PPRV if freeze_pprv else pprv_surrogate(matrix, assignment)
    dv = A1_MOM * mom + A2_MAV * mav + A3_PPRV * pprv + A4_CVV * cvv + A5_MFV * mfv
    return DVProxyComponents(mom=mom, mav=mav, pprv=pprv, cvv=cvv, mfv=mfv, cut=cut, dv=dv)


def dv_proxy_objective(matrix: np.ndarray, k: int, freeze_pprv: bool = False):
    def _obj(assignment: np.ndarray) -> float:
        return evaluate_dv_proxy(matrix, assignment, k=k, freeze_pprv=freeze_pprv).dv

    return _obj
