"""Власні структури даних: FIFO-черга, LIFO-стек, пріоритетна черга."""
import heapq
from typing import Any, Dict, List, Optional


class CustomerQueue:
    """Банківська черга клієнтів (FIFO: перший прийшов — перший пішов)."""

    def __init__(self) -> None:
        self._items: List[Any] = []

    def enqueue(self, customer: Any) -> None:
        """Додає клієнта в кінець черги."""
        self._items.append(customer)

    def dequeue(self) -> Optional[Any]:
        """Вилучає клієнта з початку черги (None, якщо черга порожня)."""
        return self._items.pop(0) if self._items else None

    def peek(self) -> Optional[Any]:
        """Повертає першого клієнта без вилучення."""
        return self._items[0] if self._items else None

    def is_empty(self) -> bool:
        return not self._items

    def __len__(self) -> int:
        return len(self._items)

    def get_all(self) -> List[Any]:
        """Поточний стан черги (від першого до останнього)."""
        return list(self._items)


class TransactionStack:
    """Стек транзакцій (LIFO: остання операція обробляється першою)."""

    def __init__(self) -> None:
        self._items: List[Any] = []

    def push(self, transaction: Any) -> None:
        """Додає транзакцію на верх стеку."""
        self._items.append(transaction)

    def pop(self) -> Optional[Any]:
        """Скасовує останню транзакцію (None, якщо стек порожній)."""
        return self._items.pop() if self._items else None

    def peek(self) -> Optional[Any]:
        return self._items[-1] if self._items else None

    def is_empty(self) -> bool:
        return not self._items

    def __len__(self) -> int:
        return len(self._items)

    def get_all(self) -> List[Any]:
        """Транзакції у зворотному порядку: найсвіжіша перша."""
        return list(reversed(self._items))


class PriorityCustomerQueue:
    """Пріоритетна черга: 1 — VIP / high_engagement, 2 — звичайні клієнти."""

    def __init__(self) -> None:
        self._items: List[tuple] = []
        self._counter = 0

    def enqueue(self, customer: str, priority: int = 2) -> None:
        heapq.heappush(self._items, (priority, self._counter, customer))
        self._counter += 1

    def dequeue(self) -> Optional[str]:
        """Вилучає клієнта з найменшим номером пріоритету."""
        if not self._items:
            return None
        return heapq.heappop(self._items)[2]

    def is_empty(self) -> bool:
        return not self._items

    def __len__(self) -> int:
        return len(self._items)

    def get_all(self) -> List[Dict[str, Any]]:
        """Клієнти у порядку обслуговування."""
        return [{"customer": c, "priority": p} for p, _, c in sorted(self._items)]