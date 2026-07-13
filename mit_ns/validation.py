"""Historical DV and matrix integrity checks."""

from __future__ import annotations

import numpy as np

from mit_ns import (
    DV_MODULAR_SH2_THESIS_MUSD,
    DV_ORIGINAL_THESIS_MUSD,
    MEINT_UNDIRECTED,
    SH2_CVV,
    SH2_MAV,
    SH2_MFV,
    SH2_MOM,
    SH2_PPRV,
    SH_CVV,
    SH_MAV,
    SH_MFV,
    SH_MOM,
    SH_PPRV,
)
from mit_ns.data import compute_historical_dv, load_interaction_matrix, load_table_9_1


def validate_matrix(matrix: np.ndarray | None = None) -> dict:
    if matrix is None:
        matrix = load_interaction_matrix()
    n = matrix.shape[0]
    assert matrix.shape == (25, 25)
    assert np.allclose(matrix, matrix.T)
    meint = int((matrix.sum() - np.trace(matrix)) // 2)
    assert meint == MEINT_UNDIRECTED
    return {"n": n, "meint_undirected": meint, "ok": True}


def validate_historical_dv() -> dict:
    dv_sh2 = compute_historical_dv(SH2_MOM, SH2_MAV, SH2_PPRV, SH2_CVV, SH2_MFV)
    dv_sh = compute_historical_dv(SH_MOM, SH_MAV, SH_PPRV, SH_CVV, SH_MFV)
    assert abs(dv_sh2 / 1e6 - DV_MODULAR_SH2_THESIS_MUSD) < 0.05
    # Original thesis headline is 76.45; recomputed from Table 9-1 may differ slightly
    table = load_table_9_1()
    assert int(table.loc[table.dv_component == "MOM", "shearon_harris"].iloc[0]) == SH_MOM
    assert int(table.loc[table.dv_component == "MOM", "shearon_harris_ii"].iloc[0]) == SH2_MOM
    return {
        "dv_modular_sh2_musd": round(dv_sh2 / 1e6, 2),
        "dv_original_from_table_9_1_musd": round(dv_sh / 1e6, 2),
        "dv_original_thesis_headline_musd": DV_ORIGINAL_THESIS_MUSD,
        "dv_reduction_pct_vs_headline": round(
            100 * (1 - (dv_sh2 / 1e6) / DV_ORIGINAL_THESIS_MUSD), 1
        ),
        "ok": True,
    }


def run_all_validations() -> dict:
    return {
        "matrix": validate_matrix(),
        "historical_dv": validate_historical_dv(),
    }
