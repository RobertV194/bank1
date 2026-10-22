"""KMeans-сегментація: метод ліктя, кластеризація та PCA-візуалізація (Plotly)."""
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .config import CLUSTER_FEATURES, RANDOM_STATE


def scale_features(df: pd.DataFrame) -> tuple:
    """StandardScaler по ознаках кластеризації (відсутні колонки -> явна помилка)."""
    missing = [c for c in CLUSTER_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Відсутні ознаки для кластеризації: {missing}")
    scaler = StandardScaler()
    return scaler.fit_transform(df[CLUSTER_FEATURES]), scaler


def find_optimal_k(X_scaled: np.ndarray, k_min: int = 2, k_max: int = 10) -> tuple:
    """Метод ліктя: обираємо k, де крива інерції найдалі від прямої між крайніми точками."""
    ks = list(range(k_min, k_max + 1))
    inertias = [
        KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit(X_scaled).inertia_
        for k in ks
    ]
    # Нормалізуємо обидві осі, щоб відстань до прямої була порівнянною
    x = (np.array(ks) - ks[0]) / (ks[-1] - ks[0])
    y = (np.array(inertias) - min(inertias)) / (max(inertias) - min(inertias))
    distances = np.abs(y - (1 - x)) / np.sqrt(2)
    return ks[int(np.argmax(distances))], ks, inertias


def elbow_figure(ks: list, inertias: list):
    """Графік ліктя для звіту/вебпанелі."""
    return px.line(x=ks, y=inertias, markers=True, title="Метод ліктя (Elbow)",
                   labels={"x": "Кількість кластерів k", "y": "Інерція"})


def perform_kmeans(df: pd.DataFrame, n_clusters: int | None = None) -> tuple:
    """Кластеризує користувачів. Якщо n_clusters не задано, k береться з методу ліктя."""
    df = df.copy()
    X_scaled, scaler = scale_features(df)
    if n_clusters is None:
        n_clusters, _, _ = find_optimal_k(X_scaled)

    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_scaled)
    return df, kmeans, scaler


def pca_figure(df: pd.DataFrame, scaler: StandardScaler, dims: int = 2) -> str:
    """Інтерактивна 2D/3D PCA-проєкція кластерів. Повертає HTML-фрагмент для вебпанелі."""
    if dims not in (2, 3):
        raise ValueError("dims має бути 2 або 3")
    X_scaled = scaler.transform(df[CLUSTER_FEATURES])
    coords = PCA(n_components=dims, random_state=RANDOM_STATE).fit_transform(X_scaled)

    plot_df = df[["user_id", "views", "purchases", "cluster"]].copy()
    plot_df["cluster"] = plot_df["cluster"].astype(str)
    for i in range(dims):
        plot_df[f"PC{i + 1}"] = coords[:, i]

    kwargs = dict(color="cluster", hover_data=["user_id", "views", "purchases"],
                  title=f"{dims}D PCA-проєкція кластерів KMeans")
    fig = (px.scatter(plot_df, x="PC1", y="PC2", **kwargs) if dims == 2
           else px.scatter_3d(plot_df, x="PC1", y="PC2", z="PC3", **kwargs))
    return fig.to_html(full_html=False, include_plotlyjs="cdn")
