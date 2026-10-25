"""Central configuration: paths and simulation parameters."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "ecommerce.db"
SQL_DIR = ROOT / "sql"
FIG_DIR = ROOT / "reports" / "figures"
TABLE_DIR = ROOT / "reports" / "tables"
POWERBI_DATA = ROOT / "powerbi" / "data"

# Synthetic data parameters
SEED = 42
START_DATE = "2023-01-01"
END_DATE = "2024-12-31"
N_CUSTOMERS = 8000
N_GUEST_ORDERS = 400

# CLV model: cap on expected customer lifespan (years)
MAX_LIFESPAN_YEARS = 5


def ensure_dirs():
    for path in (DATA_RAW, FIG_DIR, TABLE_DIR, POWERBI_DATA):
        path.mkdir(parents=True, exist_ok=True)
