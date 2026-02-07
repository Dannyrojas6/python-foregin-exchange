from pathlib import Path

DATA_DIR = Path.cwd() / "data"
DATA_DIR.mkdir(exist_ok=True)
CSV_DIR = Path.cwd() / "csv"
CSV_DIR.mkdir(exist_ok=True)

STATUS_VALID = "VALID"
STATUS_NO_FILE = "NO_FILE"
STATUS_BROKEN = "BROKEN"
STATUS_EXPIRED = "EXPIRED"

TIME_OUT = (3, 10)
CACHE_EXPIRE_DAYS = 2
BASES = ["usd", "cny", "jpy", "gbp", "hkd", "twd", "krw", "aud", "cad", "sgd"]
