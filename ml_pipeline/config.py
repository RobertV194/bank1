"""Спільні константи ML-пайплайну (шляхи, назви колонок, параметри)."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data" / "events.csv"
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

RANDOM_STATE = 42
NROWS = 50_000                      # ліміт рядків при завантаженні вибірки

# Ознаки для кластеризації та класифікації
CLUSTER_FEATURES = ["views", "carts", "purchases", "session_duration"]
# high_engagement будується з n_sessions, тому n_sessions НЕ входить в ознаки (уникаємо витоку)
CLASSIFIER_FEATURES = ["views", "carts", "purchases", "session_duration", "avg_check"]
# Регресія прогнозує total_spend, тому purchases та avg_check не беремо (вони його майже дублюють)
REGRESSION_FEATURES = ["views", "carts", "session_duration", "n_sessions"]
