"""Читання ML-артефактів (joblib) для вебпанелі: підсумок моделей, PCA, рекомендації."""
from pathlib import Path
from typing import Optional

import joblib

from ml_pipeline.recommender import recommend_top_n


class ArtifactsNotFound(RuntimeError):
    """Артефакти ще не створені (не запускався ml_pipeline.train)."""


class MLService:
    """Лінивий завантажувач артефактів із кешем: веб лише читає готові результати."""

    def __init__(self, artifacts_dir) -> None:
        self._dir = Path(artifacts_dir)
        self._cache: dict = {}

    def _load(self, name: str):
        if name not in self._cache:
            path = self._dir / f"{name}.joblib"
            if not path.exists():
                raise ArtifactsNotFound(
                    "ML-артефакти не знайдено. Запустіть: python -m ml_pipeline.train")
            self._cache[name] = joblib.load(path)
        return self._cache[name]

    def summary(self) -> dict:
        """Метрики класифікатора та регресії, k з методу ліктя, розміри кластерів."""
        users, metrics = self._load("users"), self._load("metrics")
        sizes = users["cluster"].value_counts().sort_index()
        return {
            "best_k": int(metrics["best_k"]),
            "n_users": int(len(users)),
            "cluster_sizes": {str(int(k)): int(v) for k, v in sizes.items()},
            "classifier": metrics["classifier"],
            "regression": metrics["regression"],
            "sample_user_ids": [int(x) for x in users["user_id"].head(5)],
        }

    def recommendations(self, user_id: int, top_n: int = 5, tolerance: float = 0.3) -> Optional[dict]:
        """Жадібні рекомендації для клієнта: із ціновим фільтром і без нього."""
        users, stats = self._load("users"), self._load("product_stats")
        row = users[users["user_id"] == user_id]
        if row.empty:
            return None
        cluster = int(row["cluster"].iloc[0])
        avg_check = float(row["avg_check"].iloc[0])

        priced = recommend_top_n(stats, cluster, top_n, avg_check=avg_check, tolerance=tolerance)
        plain = recommend_top_n(stats, cluster, top_n)
        price_range = ([round(avg_check * (1 - tolerance), 2), round(avg_check * (1 + tolerance), 2)]
                       if avg_check > 0 else None)
        return {"user_id": user_id, "cluster": cluster, "avg_check": round(avg_check, 2),
                "price_range": price_range,
                "price_aware": self._describe(stats, cluster, priced),
                "plain": self._describe(stats, cluster, plain)}

    @staticmethod
    def _describe(stats, cluster: int, product_ids: list) -> list:
        rows = stats[(stats["cluster"] == cluster) & (stats["product_id"].isin(product_ids))]
        rows = rows.set_index("product_id")
        return [{"product_id": int(pid),
                 "price": round(float(rows.loc[pid, "price"]), 2),
                 "views": int(rows.loc[pid, "views"]),
                 "purchases": int(rows.loc[pid, "purchases"]),
                 "conversion": round(float(rows.loc[pid, "conversion"]), 4)}
                for pid in product_ids]

    def pca_page(self, dims: int) -> str:
        """Готова HTML-сторінка з інтерактивним Plotly-графіком (для iframe), кешується."""
        key = f"pca_page_{dims}"
        if key not in self._cache:
            from ml_pipeline.clustering import pca_figure
            fragment = pca_figure(self._load("users"), self._load("scaler"), dims)
            self._cache[key] = ('<!doctype html><html><head><meta charset="utf-8">'
                                '<style>html,body{margin:0;height:100%}</style></head>'
                                f'<body>{fragment}</body></html>')
        return self._cache[key]