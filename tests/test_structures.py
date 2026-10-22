from web_app.structures import CustomerQueue, PriorityCustomerQueue, TransactionStack


def test_queue_fifo_order():
    queue = CustomerQueue()
    assert queue.is_empty() is True

    queue.enqueue("Клієнт 1")
    queue.enqueue("Клієнт 2")
    assert queue.is_empty() is False
    assert queue.get_all() == ["Клієнт 1", "Клієнт 2"]
    assert queue.peek() == "Клієнт 1"

    assert queue.dequeue() == "Клієнт 1"
    assert queue.get_all() == ["Клієнт 2"]


def test_queue_empty():
    queue = CustomerQueue()
    assert queue.dequeue() is None
    assert queue.peek() is None
    assert len(queue) == 0

    queue.enqueue("A")
    queue.dequeue()
    assert queue.is_empty() is True
    assert queue.dequeue() is None


def test_stack_lifo_order():
    stack = TransactionStack()
    assert stack.is_empty() is True

    stack.push("Транзакція A")
    stack.push("Транзакція B")
    assert stack.get_all() == ["Транзакція B", "Транзакція A"]
    assert stack.peek() == "Транзакція B"

    assert stack.pop() == "Транзакція B"
    assert stack.get_all() == ["Транзакція A"]


def test_stack_empty():
    stack = TransactionStack()
    assert stack.pop() is None
    assert stack.peek() is None

    stack.push("A")
    stack.pop()
    assert stack.is_empty() is True
    assert stack.pop() is None


def test_priority_queue_order():
    queue = PriorityCustomerQueue()
    queue.enqueue("Звичайний 1", 2)
    queue.enqueue("VIP 1", 1)
    queue.enqueue("Звичайний 2", 2)
    queue.enqueue("VIP 2", 1)

    assert [item["customer"] for item in queue.get_all()] == [
        "VIP 1", "VIP 2", "Звичайний 1", "Звичайний 2"]
    # VIP першими, а всередині пріоритету — за порядком надходження
    assert [queue.dequeue() for _ in range(4)] == ["VIP 1", "VIP 2", "Звичайний 1", "Звичайний 2"]


def test_priority_queue_empty():
    queue = PriorityCustomerQueue()
    assert queue.is_empty() is True
    assert queue.dequeue() is None
    assert queue.get_all() == []
