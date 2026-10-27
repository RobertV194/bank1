# Banking Fintech Platform

Вебсервіс банківського відділення: черга клієнтів (FIFO + VIP), стек транзакцій із балансом рахунку,
власні алгоритми сортування й пошуку, журнал операцій у SQLite та ML-модуль
(KMeans-сегментація, прогноз залученості клієнтів, персональні рекомендації).

## Можливості

- **Черга клієнтів:** звичайні клієнти обслуговуються за порядком надходження (FIFO), VIP: першими (Priority Queue). Тип клієнта обирається в інтерфейсі.
- **Стек транзакцій (LIFO):** `push()` фіксує транзакцію й змінює баланс, `pop()` скасовує найновішу та повертає баланс (Undo).
- **Алгоритми:** Bubble Sort, Quick Sort, лінійний і бінарний пошук (власні реалізації) та Live Benchmark для 100, 1 000 і 10 000 елементів.
- **Журнал операцій** (`OperationLog`, SQLite): миттєвий пошук і фільтри, експорт у CSV та JSON.
- **ML-аналітика:** метрики моделей, інтерактивна 2D/3D PCA-проєкція кластерів, рекомендації з ціновим фільтром.
- Інтерфейс працює через AJAX: списки оновлюються без перезавантаження сторінки, є «живе» оновлення кожні 3 секунди.

## Технології

Python 3.10+, Flask, Flask-SQLAlchemy (SQLite), pandas, scikit-learn, Plotly, pytest.

## Структура проєкту

```text
ml_pipeline/    очищення даних, ознаки, KMeans, моделі, рекомендації, train.py
web_app/        Flask API (app.py), структури даних, алгоритми, модель БД, ML-маршрути, templates/
tests/          pytest: test_structures.py, test_algorithms.py, test_flask_routes.py
data/           опис набору даних (README.md); сам CSV не зберігається в Git
run.py          запуск сервера
```

## Встановлення та запуск

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

1. Навчіть моделі (створює `data/events.csv`, якщо його ще немає, і артефакти в `ml_pipeline/artifacts/`):
   ```bash
   python -m ml_pipeline.train
   ```
   У терміналі з'являться оптимальне `k` (метод ліктя), метрики класифікатора (Accuracy, Precision, Recall, F1), метрики регресії (R², MAE) і топ-5 продуктів кожного кластера.
2. Запустіть сервер:
   ```bash
   python run.py
   ```
3. Відкрийте http://127.0.0.1:5000

Вкладка «ML-аналітика» працює після кроку 1. Без нього решта сайту працює, а ML-блок підкаже, що потрібно навчити моделі.

## Тести

```bash
pytest
```

Команда запускається з кореня проєкту й перевіряє структури даних (порядок FIFO/LIFO, порожні структури), алгоритми (звичайний, відсортований і порожній масив, індекси `binary_search`) та Flask-маршрути (статуси 200/201, формат JSON).

## Дані

Для розробки використано **синтетичний датасет**, який генерує `ml_pipeline/generate_data.py`. Його структура повністю збігається з Kaggle-набором *eCommerce behavior data from multi-category store* (посилання в [data/README.md](data/README.md)). Метрики моделей отримано саме на синтетичних даних, тому на реальних результат буде інший. Щоб використати справжній набір, покладіть CSV у `data/events.csv` і повторіть `python -m ml_pipeline.train`.

## API

| Метод | Шлях | Призначення |
|---|---|---|
| GET, POST | `/api/queue`, `/api/queue/enqueue`, `/api/queue/dequeue` | звичайна FIFO-черга |
| GET, POST | `/api/priority-queue`, `.../enqueue`, `.../dequeue` | VIP-черга (`priority` 1 або 2; також `client_id`, тоді пріоритет визначає модель `high_engagement`) |
| GET, POST | `/api/stack`, `/api/stack/push`, `/api/stack/pop` | стек транзакцій і баланс (`amount` у `push`) |
| GET | `/api/logs`, `/api/logs/export?format=csv\|json` | журнал, фільтри `structure`, `operation_type`, `q` |
| POST | `/api/algorithms/sort`, `/search`, `/benchmark` | алгоритми та Live Benchmark |
| GET | `/api/ml/summary`, `/api/ml/recommendations/<id>`, `/api/ml/engagement/<id>`, `/ml/pca?dims=2\|3` | результати ML |

Створення повертає `201`, інші успішні відповіді `200`, помилки валідації `400` у форматі `{"error": "..."}`.

## Додаткові функції (Custom Features)

- **Напрямок A (Data Science):** 2D/3D PCA-графіки (Plotly), регресійна модель суми витрат з метриками R² і MAE, жадібні рекомендації з прив'язкою до типового чека клієнта.
- **Напрямок B (Алгоритми):** Live Benchmark (Bubble Sort проти Quick Sort), Priority Queue для VIP-клієнтів.
- **Напрямок C (Web & UX):** повне скасування (Undo) з поверненням балансу при `pop()`, експорт журналу в CSV/JSON, миттєві фільтри в інтерфейсі.

## Обмеження

- Черги, стек і баланс зберігаються в пам'яті сервера й скидаються після перезапуску. Журнал операцій залишається в базі `instance/bank_branch.db`.
- Для відображення PCA-графіка потрібен інтернет: Plotly підвантажується з CDN.
