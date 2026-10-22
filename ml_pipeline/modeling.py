"""Supervised ML: класифікація high_engagement (GridSearchCV) та регресія total_spend."""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error,
                             precision_score, r2_score, recall_score)
from sklearn.model_selection import GridSearchCV, train_test_split

from .config import CLASSIFIER_FEATURES, RANDOM_STATE, REGRESSION_FEATURES

PARAM_GRID = {
    "n_estimators": [100, 200],
    "max_depth": [None, 5, 10],
    "min_samples_leaf": [1, 3],
}


def train_engagement_classifier(df: pd.DataFrame) -> tuple:
    """RandomForestClassifier + GridSearchCV (оптимізація за F1). Повертає (модель, метрики)."""
    X, y = df[CLASSIFIER_FEATURES], df["high_engagement"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)

    search = GridSearchCV(
        RandomForestClassifier(random_state=RANDOM_STATE, class_weight="balanced"),
        PARAM_GRID, scoring="f1", cv=3, n_jobs=-1)
    search.fit(X_train, y_train)

    y_pred = search.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "best_params": search.best_params_,
    }
    return search.best_estimator_, metrics


def train_spend_regression(df: pd.DataFrame) -> tuple:
    """Регресія суми витрат користувача (R², MAE) на реальній цільовій total_spend."""
    X, y = df[REGRESSION_FEATURES], df["total_spend"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE)

    model = RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return model, {"R2": r2_score(y_test, y_pred), "MAE": mean_absolute_error(y_test, y_pred)}
