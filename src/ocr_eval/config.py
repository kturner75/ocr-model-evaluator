from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

CONFIG_DIR = PROJECT_ROOT / "config"
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
DATA_DIR = PROJECT_ROOT / "data"

CONFIG_DOCUMENTS_DIR = CONFIG_DIR / "documents"
CONFIG_SCHEMAS_DIR = CONFIG_DIR / "schemas"
CONFIG_PROMPTS_DIR = CONFIG_DIR / "prompts"
CONFIG_MODELS_DIR = CONFIG_DIR / "models"
CONFIG_EXPECTED_DIR = CONFIG_DIR / "expected"

DB_PATH = DATA_DIR / "results.db"

for d in [
    CONFIG_DOCUMENTS_DIR,
    CONFIG_SCHEMAS_DIR,
    CONFIG_PROMPTS_DIR,
    CONFIG_MODELS_DIR,
    CONFIG_EXPECTED_DIR,
    DOCUMENTS_DIR,
    DATA_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)
