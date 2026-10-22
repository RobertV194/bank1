"""Жадібні рекомендації: топ-N продуктів кластера за співвідношенням покупок до переглядів."""
import pandas as pd


def build_product_stats(events: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    """Статистика продуктів по кластерах: views, purchases, price, conversion."""
    merged = events.merge(users[["user_id", "cluster"]], on="user_id", how="inner")
    grouped = merged.groupby(["cluster", "product_id"])
    stats = grouped.agg(
        views=("event_type", lambda s: (s == "view").sum()),
        purchases=("event_type", lambda s: (s == "purchase").sum()),
        price=("price", "median"),
    ).reset_index()
    stats["conversion"] = stats["purchases"] / (stats["views"] + 1)
    return stats


def recommend_top_n(product_stats: pd.DataFrame, cluster: int, top_n: int = 5,
                    avg_check: float | None = None, tolerance: float = 0.3,
                    min_views: int = 3) -> list:
    """Жадібний відбір топ-N за conversion; за наявності avg_check застосовує ціновий фільтр ±tolerance."""
    pool = product_stats[(product_stats["cluster"] == cluster) & (product_stats["views"] >= min_views)]

    if avg_check and avg_check > 0:
        in_range = pool[pool["price"].between(avg_check * (1 - tolerance), avg_check * (1 + tolerance))]
        if len(in_range) >= top_n:
            pool = in_range

    return pool.sort_values("conversion", ascending=False).head(top_n)["product_id"].tolist()


def recommend_for_user(users: pd.DataFrame, product_stats: pd.DataFrame, user_id: int,
                       top_n: int = 5, price_aware: bool = True) -> list:
    """Рекомендації для конкретного користувача."""
    row = users[users["user_id"] == user_id]
    if row.empty:
        return []
    avg_check = float(row["avg_check"].iloc[0]) if price_aware else None
    return recommend_top_n(product_stats, int(row["cluster"].iloc[0]), top_n, avg_check)
