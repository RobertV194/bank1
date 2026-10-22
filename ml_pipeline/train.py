import joblib

from .clustering import elbow_figure, find_optimal_k, perform_kmeans, scale_features
from .config import ARTIFACTS_DIR, DATA_PATH
from .eda_and_cleaning import clean_data, engineer_features, load_data, run_eda
from .generate_data import save_synthetic_dataset
from .modeling import train_engagement_classifier, train_spend_regression
from .recommender import build_product_stats, recommend_top_n

TOP_N = 5


def main() -> None:
    if not DATA_PATH.exists():
        print("Датасет не знайдено, генерую синтетичний.")
        save_synthetic_dataset()

    raw = load_data(DATA_PATH)
    run_eda(raw)
    events = clean_data(raw)
    users = engineer_features(events)

    X_scaled, _ = scale_features(users)
    best_k, ks, inertias = find_optimal_k(X_scaled)
    print(f"Оптимальна кількість кластерів (лікоть): {best_k}")
    users, kmeans, scaler = perform_kmeans(users, best_k)

    classifier, clf_metrics = train_engagement_classifier(users)
    regressor, reg_metrics = train_spend_regression(users)
    print("Класифікатор:", clf_metrics)
    print("Регресія:", reg_metrics)

    # Жадібні рекомендації: топ-N продуктів кожного кластера за purchases / views
    product_stats = build_product_stats(events, users)
    for cluster in sorted(users["cluster"].unique()):
        top_products = recommend_top_n(product_stats, int(cluster), top_n=TOP_N)
        print(f"Топ-{TOP_N} продуктів кластера {cluster}: {top_products}")

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    artifacts = {
        "kmeans": kmeans, "scaler": scaler, "classifier": classifier, "regressor": regressor,
        "users": users, "product_stats": product_stats,
        "metrics": {"classifier": clf_metrics, "regression": reg_metrics, "best_k": best_k},
    }
    for name, obj in artifacts.items():
        joblib.dump(obj, ARTIFACTS_DIR / f"{name}.joblib")
    elbow_figure(ks, inertias).write_html(ARTIFACTS_DIR / "elbow.html")
    print(f"Артефакти збережено в {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()