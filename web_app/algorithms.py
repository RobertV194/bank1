"""Власні алгоритми сортування та пошуку (без sorted() / list.sort())."""
from typing import Any, List, Sequence, Union

Number = Union[int, float]


def bubble_sort(arr: Sequence[Number]) -> List[Number]:
    """Бульбашкове сортування, O(n²). Повертає новий список."""
    data = list(arr)
    n = len(data)
    for i in range(n):
        swapped = False
        for j in range(n - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
                swapped = True
        if not swapped:
            break
    return data


def quick_sort(arr: Sequence[Number]) -> List[Number]:
    """Швидке сортування, O(n log n) у середньому. Повертає новий список."""
    if len(arr) <= 1:
        return list(arr)
    pivot = arr[len(arr) // 2]

    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)


def linear_search(arr: Sequence[Any], target: Any) -> int:
    """Лінійний пошук, O(n). Індекс елемента або -1."""
    for index, value in enumerate(arr):
        if value == target:
            return index
    return -1


def binary_search(arr: Sequence[Number], target: Number) -> int:
    """Бінарний пошук, O(log n), лише для впорядкованого масиву. Індекс або -1."""
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        if arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
