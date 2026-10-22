"""Flask-застосунок банківського відділення: REST API, структури даних, алгоритми."""
import csv
import io
import json
import math
import random
import time
from types import SimpleNamespace

from flask import Blueprint, Flask, Response, current_app, jsonify, render_template, request
from sqlalchemy import or_
from werkzeug.exceptions import HTTPException

from .algorithms import binary_search, bubble_sort, linear_search, quick_sort
from .ml_routes import register_ml
from .models import OperationLog, db
from .structures import CustomerQueue, PriorityCustomerQueue, TransactionStack

api = Blueprint("api", __name__)

MAX_TEXT_LEN = 100
MAX_ARRAY_LEN = 10_000
MAX_BENCHMARK_SIZE = 100_000
BUBBLE_MAX_SIZE = 10_000
PRIORITIES = (1, 2)             # 1 — VIP, 2 — звичайний
DEFAULT_PRIORITY = 2
START_BALANCE_CENTS = 100_000    # початковий баланс рахунку: 1 000,00 (суми зберігаємо в копійках)
MAX_AMOUNT = 1_000_000          # максимальна сума однієї транзакції
SORTERS = {"bubble": bubble_sort, "quick": quick_sort}


# ---------------------------------------------------------------- валідація

class ApiError(Exception):
    """Помилка валідації, яка перетворюється на JSON-відповідь."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message, self.status = message, status


def _state() -> SimpleNamespace:
    """Структури даних поточного застосунку (свої для кожного create_app)."""
    return current_app.extensions["bank_state"]


def _payload() -> dict:
    """Тіло запиту як словник (некоректний JSON дає порожній словник, а не 500)."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _int(value, label: str, default=None) -> int:
    if value is None and default is not None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ApiError(f"{label} має бути цілим числом")
    try:
        return int(value)
    except ValueError:
        raise ApiError(f"{label} має бути цілим числом")


def _text(data: dict, key: str, missing_message: str) -> str:
    value = data.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = str(value)
    if not isinstance(value, str) or not value.strip():
        raise ApiError(missing_message)
    value = value.strip()
    if len(value) > MAX_TEXT_LEN:
        raise ApiError(f"Максимальна довжина — {MAX_TEXT_LEN} символів")
    return value


def _number(value, label: str):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ApiError(f"{label} має бути числом")
    return value


def _numbers(value, label: str = "array") -> list:
    if not isinstance(value, list):
        raise ApiError(f"{label} має бути списком чисел")
    if len(value) > MAX_ARRAY_LEN:
        raise ApiError(f"Максимальний розмір масиву — {MAX_ARRAY_LEN}")
    return [_number(x, "Елемент масиву") for x in value]


def _amount_cents(value) -> int:
    """Сума транзакції в копійках (None = без суми). Додатна — поповнення, від’ємна — списання."""
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ApiError("amount має бути числом")
    if abs(value) > MAX_AMOUNT:
        raise ApiError(f"Максимальна сума транзакції — {MAX_AMOUNT}")
    return round(value * 100)


def _label(name: str, cents: int) -> str:
    return f"{name} ({cents / 100:+.2f})" if cents else name


def _stack_payload() -> dict:
    """Стан стека й рахунку: 'stack' — назви, 'items' — з сумами, 'balance'."""
    state = _state()
    items = [{"name": t["name"], "amount": t["amount"] / 100} for t in state.stack.get_all()]
    return {"stack": [item["name"] for item in items], "items": items, "balance": state.balance_cents / 100}


def _record(user_id: int, structure: str, operation: str, value: str, description: str) -> None:
    """Зберігає операцію в журнал (SQLite)."""
    db.session.add(OperationLog(user_id=user_id, structure=structure, operation_type=operation,
                                value=value, description=description))
    db.session.commit()


def _timed(func, arg) -> tuple:
    start = time.perf_counter()
    result = func(arg)
    return result, round(time.perf_counter() - start, 5)


# ---------------------------------------------------------------- 1. FIFO черга

@api.get("/api/queue")
def get_queue():
    return jsonify({"queue": _state().queue.get_all()})


@api.post("/api/queue/enqueue")
def enqueue_customer():
    data = _payload()
    customer = _text(data, "customer", "Клієнт не вказаний")
    user_id = _int(data.get("user_id"), "user_id", default=1)

    _state().queue.enqueue(customer)
    _record(user_id, "Queue", "enqueue", customer, f"Додано клієнта {customer} у чергу")
    return jsonify({"message": f"Клієнта {customer} додано", "queue": _state().queue.get_all()}), 201


@api.post("/api/queue/dequeue")
def dequeue_customer():
    user_id = _int(_payload().get("user_id"), "user_id", default=1)

    customer = _state().queue.dequeue()
    if customer is None:
        raise ApiError("Черга порожня")
    _record(user_id, "Queue", "dequeue", customer, f"Вилучено клієнта {customer} з черги")
    return jsonify({"message": f"Клієнта {customer} обслуговано", "queue": _state().queue.get_all()})


# ---------------------------------------------------------------- 2. Пріоритетна черга

def _resolve_priority(data: dict) -> tuple:
    """Повертає (пріоритет, ML-прогноз). Явний priority важливіший за client_id.

    Якщо передано client_id, а priority ні: клієнт із high_engagement (за моделлю) стає VIP.
    """
    if "priority" in data:
        priority = _int(data["priority"], "priority")
        if priority not in PRIORITIES:
            raise ApiError("priority має бути 1 (VIP) або 2 (звичайний)")
        return priority, None
    if data.get("client_id") is not None:
        info = current_app.extensions["ml_service"].engagement(_int(data["client_id"], "client_id"))
        if info is None:
            raise ApiError("Клієнта не знайдено в ML-даних", 404)
        return (1 if info["high_engagement"] else DEFAULT_PRIORITY), info
    return DEFAULT_PRIORITY, None


@api.get("/api/priority-queue")
def get_priority_queue():
    return jsonify({"queue": _state().priority.get_all()})


@api.post("/api/priority-queue/enqueue")
def enqueue_priority_customer():
    data = _payload()
    customer = _text(data, "customer", "Клієнт не вказаний")
    user_id = _int(data.get("user_id"), "user_id", default=1)
    priority, ml_info = _resolve_priority(data)

    _state().priority.enqueue(customer, priority)
    source = " (визначено ML за high_engagement)" if ml_info else ""
    _record(user_id, "PriorityQueue", "enqueue", f"{customer} (Пріоритет: {priority})",
            f"Додано клієнта {customer} з пріоритетом {priority}{source}")
    return jsonify({"message": "Клієнта додано в пріоритетну чергу", "priority": priority,
                    "ml": ml_info, "queue": _state().priority.get_all()}), 201


@api.post("/api/priority-queue/dequeue")
def dequeue_priority_customer():
    user_id = _int(_payload().get("user_id"), "user_id", default=1)

    customer = _state().priority.dequeue()
    if customer is None:
        raise ApiError("Пріоритетна черга порожня")
    _record(user_id, "PriorityQueue", "dequeue", customer, f"Обслуговано клієнта {customer}")
    return jsonify({"message": f"Обслуговано клієнта: {customer}", "queue": _state().priority.get_all()})


# ---------------------------------------------------------------- 3. LIFO стек

@api.get("/api/stack")
def get_stack():
    return jsonify(_stack_payload())


@api.post("/api/stack/push")
def push_transaction():
    data = _payload()
    transaction = _text(data, "transaction", "Транзакція не вказана")
    user_id = _int(data.get("user_id"), "user_id", default=1)
    cents = _amount_cents(data.get("amount"))

    state = _state()
    if state.balance_cents + cents < 0:
        raise ApiError("Недостатньо коштів на рахунку")
    state.stack.push({"name": transaction, "amount": cents})
    state.balance_cents += cents

    label = _label(transaction, cents)
    balance = state.balance_cents / 100
    _record(user_id, "Stack", "push", label, f"Виконано транзакцію: {label}. Баланс: {balance:.2f}")
    return jsonify({**_stack_payload(), "message": f"Транзакцію додано. Баланс: {balance:.2f}"}), 201


@api.post("/api/stack/pop")
def pop_transaction():
    user_id = _int(_payload().get("user_id"), "user_id", default=1)

    state = _state()
    transaction = state.stack.pop()
    if transaction is None:
        raise ApiError("Стек транзакцій порожній")
    state.balance_cents -= transaction["amount"]   # Undo: скасування повертає баланс

    label = _label(transaction["name"], transaction["amount"])
    balance = state.balance_cents / 100
    _record(user_id, "Stack", "pop", label, f"Скасовано транзакцію: {label}. Баланс повернуто: {balance:.2f}")
    return jsonify({**_stack_payload(), "message": f"Транзакцію скасовано. Баланс: {balance:.2f}",
                    "undone": {"name": transaction["name"], "amount": transaction["amount"] / 100}})


# ---------------------------------------------------------------- 4. Журнал, фільтри, експорт

def _logs_query():
    """Запит до журналу з фільтрами ?structure= &operation_type= &q= (пошук за текстом)."""
    query = db.session.query(OperationLog)
    for field in ("structure", "operation_type"):
        value = request.args.get(field)
        if value:
            query = query.filter(getattr(OperationLog, field) == value)
    text = request.args.get("q", "").strip()
    if text:
        pattern = f"%{text}%"
        query = query.filter(or_(OperationLog.value.ilike(pattern),
                                 OperationLog.description.ilike(pattern)))
    return query.order_by(OperationLog.id.desc())


@api.get("/api/logs")
def get_logs():
    limit = min(max(request.args.get("limit", default=100, type=int), 1), 1000)
    return jsonify({"logs": [log.to_dict() for log in _logs_query().limit(limit)]})


@api.get("/api/logs/export")
def export_logs():
    fmt = request.args.get("format", "json").lower()
    if fmt not in ("json", "csv"):
        raise ApiError("format має бути json або csv")
    rows = [log.to_dict() for log in _logs_query()]
    headers = {"Content-Disposition": f"attachment; filename=operation_log.{fmt}"}

    if fmt == "json":
        return Response(json.dumps(rows, ensure_ascii=False, indent=2),
                        mimetype="application/json", headers=headers)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(OperationLog().to_dict().keys()))
    writer.writeheader()
    writer.writerows(rows)
    return Response("\ufeff" + buffer.getvalue(), mimetype="text/csv", headers=headers)


# ---------------------------------------------------------------- 5. Сортування, пошук, benchmark

@api.post("/api/algorithms/sort")
def sort_array():
    data = _payload()
    arr = _numbers(data.get("array", []))
    algo = data.get("algorithm", "quick")
    if algo not in SORTERS:
        raise ApiError("algorithm має бути bubble або quick")

    sorted_arr, elapsed = _timed(SORTERS[algo], arr)
    return jsonify({"algorithm": algo, "original": arr, "sorted": sorted_arr, "time_sec": elapsed})


@api.post("/api/algorithms/search")
def search_array():
    data = _payload()
    arr = _numbers(data.get("array", []))
    target = _number(data.get("target"), "target")
    algo = data.get("algorithm", "linear")

    if algo == "binary":
        sorted_arr = quick_sort(arr)
        return jsonify({"algorithm": "binary", "sorted_array": sorted_arr, "target": target,
                        "index": binary_search(sorted_arr, target)})
    if algo == "linear":
        return jsonify({"algorithm": "linear", "array": arr, "target": target,
                        "index": linear_search(arr, target)})
    raise ApiError("algorithm має бути linear або binary")


@api.post("/api/algorithms/benchmark")
def benchmark_sorting():
    sizes = _payload().get("sizes", [100, 1000, 10000])
    if (not isinstance(sizes, list) or not 1 <= len(sizes) <= 5
            or any(isinstance(s, bool) or not isinstance(s, int) or not 1 <= s <= MAX_BENCHMARK_SIZE
                   for s in sizes)):
        raise ApiError(f"sizes — список із 1–5 цілих чисел від 1 до {MAX_BENCHMARK_SIZE}")

    results = []
    for size in sizes:
        data = [random.randint(1, 100_000) for _ in range(size)]
        bubble_skipped = size > BUBBLE_MAX_SIZE
        bubble_time = None if bubble_skipped else _timed(bubble_sort, data)[1]
        results.append({"size": size, "bubble_sort_sec": bubble_time,
                        "bubble_skipped": bubble_skipped,
                        "quick_sort_sec": _timed(quick_sort, data)[1]})
    return jsonify({"benchmark_results": results})




def index():
    return render_template("index.html")


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify({"error": error.message}), error.status

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        if request.path.startswith("/api/"):
            return jsonify({"error": error.description}), error.code
        return error


def create_app(test_config: dict | None = None) -> Flask:
    """Фабрика: кожен застосунок має власні структури даних і власну БД."""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///bank_branch.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.extensions["bank_state"] = SimpleNamespace(
        queue=CustomerQueue(),
        stack=TransactionStack(),
        priority=PriorityCustomerQueue(),
        balance_cents=START_BALANCE_CENTS,
    )
    app.register_blueprint(api)
    register_ml(app)
    app.add_url_rule("/", "index", index)
    _register_error_handlers(app)

    with app.app_context():
        db.create_all()
    return app