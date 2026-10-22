def post(client, url, **body):
    return client.post(url, json=body)


def test_index_route(client):
    assert client.get("/").status_code == 200


# ---- FIFO черга

def test_queue_enqueue_dequeue(client):
    response = post(client, "/api/queue/enqueue", customer="Петро", user_id=1)
    assert response.status_code == 201
    assert response.get_json()["queue"] == ["Петро"]

    post(client, "/api/queue/enqueue", customer="Ірина")
    response = post(client, "/api/queue/dequeue", user_id=1)
    assert response.status_code == 200
    assert response.get_json()["queue"] == ["Ірина"]
    assert client.get("/api/queue").get_json()["queue"] == ["Ірина"]


def test_queue_errors(client):
    assert post(client, "/api/queue/dequeue").status_code == 400
    assert post(client, "/api/queue/enqueue").status_code == 400
    assert post(client, "/api/queue/enqueue", customer="  ").status_code == 400
    assert post(client, "/api/queue/enqueue", customer="x" * 500).status_code == 400
    assert post(client, "/api/queue/enqueue", customer="A", user_id="abc").status_code == 400
    bad_body = client.post("/api/queue/enqueue", data="не json", content_type="text/plain")
    assert bad_body.status_code == 400
    assert "error" in bad_body.get_json()


def test_structures_are_isolated_between_apps(client):
    assert client.get("/api/queue").get_json()["queue"] == []


# ---- Пріоритетна черга

def test_priority_queue(client):
    post(client, "/api/priority-queue/enqueue", customer="Звичайний")
    response = post(client, "/api/priority-queue/enqueue", customer="VIP", priority=1)
    assert response.status_code == 201
    assert response.get_json()["queue"][0] == {"customer": "VIP", "priority": 1}

    assert "VIP" in post(client, "/api/priority-queue/dequeue").get_json()["message"]
    assert post(client, "/api/priority-queue/enqueue", customer="X", priority=7).status_code == 400
    assert post(client, "/api/priority-queue/dequeue").status_code == 200
    assert post(client, "/api/priority-queue/dequeue").status_code == 400


# ---- LIFO стек

def test_stack_push_pop(client):
    response = post(client, "/api/stack/push", transaction="Оплата послуг", user_id=1)
    assert response.status_code == 201
    post(client, "/api/stack/push", transaction="Переказ")
    assert client.get("/api/stack").get_json()["stack"] == ["Переказ", "Оплата послуг"]

    response = post(client, "/api/stack/pop", user_id=1)
    assert response.status_code == 200
    assert response.get_json()["stack"] == ["Оплата послуг"]


def test_stack_errors(client):
    assert post(client, "/api/stack/pop").status_code == 400
    assert post(client, "/api/stack/push").status_code == 400


def test_json_format_of_responses(client):
    """Успішні відповіді та помилки API мають формат JSON (Content-Type: application/json)."""
    responses = [
        post(client, "/api/queue/enqueue", customer="Петро"),        # 201
        post(client, "/api/queue/dequeue"),                           # 200
        post(client, "/api/queue/dequeue"),                           # 400: черга порожня
        post(client, "/api/stack/push", transaction="Оплата"),        # 201
        client.get("/api/queue"),                                     # 200
    ]
    assert [r.status_code for r in responses] == [201, 200, 400, 201, 200]
    assert all(r.is_json for r in responses)
    assert "error" in responses[2].get_json()


# ---- Журнал

def test_operations_are_logged_and_filterable(client):
    post(client, "/api/queue/enqueue", customer="Петро")
    post(client, "/api/stack/push", transaction="Оплата")
    post(client, "/api/stack/pop")

    logs = client.get("/api/logs").get_json()["logs"]
    assert len(logs) == 3
    assert logs[0]["operation_type"] == "pop"

    stack_logs = client.get("/api/logs?structure=Stack").get_json()["logs"]
    assert {log["structure"] for log in stack_logs} == {"Stack"}
    assert len(client.get("/api/logs?q=Петро").get_json()["logs"]) == 1


def test_logs_export(client):
    post(client, "/api/queue/enqueue", customer="Петро")

    csv_response = client.get("/api/logs/export?format=csv")
    assert csv_response.status_code == 200
    assert csv_response.mimetype == "text/csv"
    assert "Петро" in csv_response.get_data(as_text=True)

    json_response = client.get("/api/logs/export?format=json")
    assert json_response.get_json()[0]["value"] == "Петро"
    assert client.get("/api/logs/export?format=xml").status_code == 400


# ---- Алгоритми

def test_sort_route(client):
    for algo in ("bubble", "quick"):
        data = post(client, "/api/algorithms/sort", array=[3, 1, 2], algorithm=algo).get_json()
        assert data["sorted"] == [1, 2, 3]
    assert post(client, "/api/algorithms/sort", array=[]).get_json()["sorted"] == []


def test_sort_validation(client):
    assert post(client, "/api/algorithms/sort", array="abc").status_code == 400
    assert post(client, "/api/algorithms/sort", array=[1, "a"]).status_code == 400
    assert post(client, "/api/algorithms/sort", array=[1], algorithm="magic").status_code == 400


def test_search_route(client):
    linear = post(client, "/api/algorithms/search", array=[5, 3, 9], target=9, algorithm="linear")
    assert linear.get_json()["index"] == 2

    binary = post(client, "/api/algorithms/search", array=[9, 3, 5], target=9, algorithm="binary")
    assert binary.get_json()["sorted_array"] == [3, 5, 9]          # масив впорядковується
    assert binary.get_json()["index"] == 2

    assert post(client, "/api/algorithms/search", array=[1], target=5).get_json()["index"] == -1
    assert post(client, "/api/algorithms/search", array=[1]).status_code == 400


def test_benchmark_route(client):
    response = post(client, "/api/algorithms/benchmark", sizes=[50, 200])
    assert response.status_code == 200
    results = response.get_json()["benchmark_results"]
    assert [r["size"] for r in results] == [50, 200]
    assert all(r["bubble_sort_sec"] >= 0 and r["quick_sort_sec"] >= 0 for r in results)

    assert post(client, "/api/algorithms/benchmark", sizes=[0]).status_code == 400
    assert post(client, "/api/algorithms/benchmark", sizes=[10 ** 9]).status_code == 400
    assert post(client, "/api/algorithms/benchmark", sizes="100").status_code == 400