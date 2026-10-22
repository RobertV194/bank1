"""ML-маршрути вебпанелі: підсумок моделей, PCA-проєкція кластерів, рекомендації."""
from flask import Blueprint, Flask, Response, current_app, jsonify, request

from ml_pipeline.config import ARTIFACTS_DIR

from .ml_service import ArtifactsNotFound, MLService

ml_api = Blueprint("ml_api", __name__)


def _service() -> MLService:
    return current_app.extensions["ml_service"]


@ml_api.get("/api/ml/summary")
def ml_summary():
    return jsonify(_service().summary())


@ml_api.get("/api/ml/engagement/<int:user_id>")
def ml_engagement(user_id: int):
    """Прогноз high_engagement для клієнта (за ним інтерфейс вирішує, чи ставити клієнта як VIP)."""
    result = _service().engagement(user_id)
    if result is None:
        return jsonify({"error": "Клієнта не знайдено в ML-даних"}), 404
    return jsonify(result)


@ml_api.get("/api/ml/recommendations/<int:user_id>")
def ml_recommendations(user_id: int):
    top_n = request.args.get("top_n", default=5, type=int)
    if not 1 <= top_n <= 20:
        return jsonify({"error": "top_n має бути від 1 до 20"}), 400
    result = _service().recommendations(user_id, top_n)
    if result is None:
        return jsonify({"error": "Користувача не знайдено"}), 404
    return jsonify(result)


@ml_api.get("/ml/pca")
def ml_pca():
    """HTML-сторінка з Plotly-графіком; вставляється у вебпанель через iframe."""
    dims = request.args.get("dims", default=2, type=int)
    if dims not in (2, 3):
        return Response("dims має бути 2 або 3", status=400, mimetype="text/plain")
    try:
        return Response(_service().pca_page(dims), mimetype="text/html")
    except ArtifactsNotFound as error:
        return Response(f"<p style='font-family:sans-serif'>{error}</p>", status=503, mimetype="text/html")


def register_ml(app: Flask) -> None:
    """Підключає ML-блок до застосунку (викликається у create_app)."""
    app.config.setdefault("ARTIFACTS_DIR", ARTIFACTS_DIR)
    app.extensions["ml_service"] = MLService(app.config["ARTIFACTS_DIR"])
    app.register_blueprint(ml_api)

    @app.errorhandler(ArtifactsNotFound)
    def handle_missing_artifacts(error: ArtifactsNotFound):
        return jsonify({"error": str(error)}), 503