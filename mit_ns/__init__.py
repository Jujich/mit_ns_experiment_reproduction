"""MIT Nuclear Modularity reproduction package (Lapp 1989)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"

# Prefer root CSVs (legacy notebook) then data/
LEGACY_CSV_DIR = ROOT

A1_MOM = 535
A2_MAV = 472
A3_PPRV = 1268
A4_CVV = 36
A5_MFV = 196

DV_COEFFICIENTS = {
    "A1_MOM": A1_MOM,
    "A2_MAV": A2_MAV,
    "A3_PPRV": A3_PPRV,
    "A4_CVV": A4_CVV,
    "A5_MFV": A5_MFV,
}

# Historical Modular SH II component values (thesis validation)
SH2_MOM = 1180
SH2_MAV = 2895
SH2_PPRV = 2773
SH2_CVV = 1_266_483
SH2_MFV = 3444

# Historical Original Plant components (Table 9-1)
SH_MOM = 2112
SH_MAV = 4236
SH_PPRV = 5901
SH_CVV = 1_801_000
SH_MFV = 5102

DV_ORIGINAL_THESIS_MUSD = 76.45
DV_MODULAR_SH2_THESIS_MUSD = 51.78

MEINT_UNDIRECTED = 1228
N_SYSTEMS = 25
