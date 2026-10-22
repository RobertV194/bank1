"""EDA, очищення даних та Feature Engineering (агрегація до user_id)."""
import pandas as pd

from .config import NROWS

REQUIRED_COLUMNS = {"event_time", "event_type", "user_id", "user_session"}


def load_data(file_path, nrows: int = NROWS) -> pd.DataFrame:
    """Завантажує вибірку з обмеженням nrows і перевіряє наявність потрібних колонок."""
    df = pd.read_csv(file_path, nrows=nrows)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"У датасеті немає колонок: {sorted(missing)}")
    return df


def run_eda(df: pd.DataFrame) -> dict:
    """Короткий EDA-звіт: розмір, типи, пропуски, дублікати, розподіл подій."""
    report = {
        "shape": df.shape,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing": df.isna().sum().to_dict(),
        "duplicates": int(df.duplicated().sum()),
        "event_counts": df["event_type"].value_counts().to_dict(),
    }
    print("EDA:", report)
    return report


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Дублікати -> пропуски -> нормалізація дат. Повертає нову таблицю."""
    df = df.drop_duplicates().copy()

    df = df.dropna(subset=["user_id"])

    num_cols = df.select_dtypes(include="number").columns
    text_cols = [c for c in df.columns
                 if c not in num_cols and not pd.api.types.is_datetime64_any_dtype(df[c])]
    df[text_cols] = df[text_cols].fillna("Unknown")
    df[num_cols] = df[num_cols].fillna(0)

    # Нормалізація дат
    df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce", utc=True)
    df = df.dropna(subset=["event_time"])

    df["user_id"] = df["user_id"].astype("int64")
    return df.reset_index(drop=True)


def engineer_features(df: pd.DataFrame, engagement_quantile: float = 0.75) -> pd.DataFrame:
    """Агрегація до user_id: перегляди, кошики, покупки, тривалість сесій, витрати."""
    sessions = (
        df.groupby(["user_id", "user_session"])["event_time"]
        .agg(["min", "max"])
        .assign(duration=lambda s: (s["max"] - s["min"]).dt.total_seconds())
    )
    per_user = sessions.groupby("user_id").agg(
        session_duration=("duration", "mean"),
        n_sessions=("duration", "size"),
    )

    counts = (
        pd.crosstab(df["user_id"], df["event_type"])
        .reindex(columns=["view", "cart", "purchase"], fill_value=0)
        .rename(columns={"view": "views", "cart": "carts", "purchase": "purchases"})
    )

    price = df["price"] if "price" in df.columns else pd.Series(0.0, index=df.index)
    spend = price[df["event_type"] == "purchase"].groupby(df["user_id"]).sum().rename("total_spend")

    features = per_user.join(counts).join(spend).fillna(0).reset_index()
    features["avg_check"] = (features["total_spend"] / features["purchases"].where(features["purchases"] > 0)).fillna(0)

    threshold = features["n_sessions"].quantile(engagement_quantile)
    features["high_engagement"] = (features["n_sessions"] >= threshold).astype(int)
    return features
