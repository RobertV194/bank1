import random

import pytest

from web_app.algorithms import binary_search, bubble_sort, linear_search, quick_sort


@pytest.mark.parametrize("sort_func", [bubble_sort, quick_sort])
class TestSorting:
    def test_regular_array(self, sort_func):
        assert sort_func([5, 2, 9, 1, 5, 6]) == [1, 2, 5, 5, 6, 9]

    def test_already_sorted(self, sort_func):
        assert sort_func([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

    def test_reversed(self, sort_func):
        assert sort_func([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

    def test_empty_and_single(self, sort_func):
        assert sort_func([]) == []
        assert sort_func([42]) == [42]

    def test_negative_float_duplicates(self, sort_func):
        assert sort_func([3, -1, 2.5, -1, 0]) == [-1, -1, 0, 2.5, 3]

    def test_input_not_mutated(self, sort_func):
        data = [3, 1, 2]
        sort_func(data)
        assert data == [3, 1, 2]

    def test_matches_builtin_on_random_data(self, sort_func):
        data = [random.randint(-100, 100) for _ in range(300)]
        assert sort_func(data) == sorted(data)


def test_linear_search():
    arr = [10, 20, 30, 40, 50]
    assert linear_search(arr, 30) == 2
    assert linear_search(arr, 99) == -1
    assert linear_search([], 1) == -1


def test_binary_search():
    arr = [10, 20, 30, 40, 50]
    assert binary_search(arr, 30) == 2
    assert binary_search(arr, 10) == 0
    assert binary_search(arr, 50) == 4
    assert binary_search(arr, 99) == -1
    assert binary_search(arr, 5) == -1
    assert binary_search([], 1) == -1
    assert binary_search([7], 7) == 0


def test_binary_search_returns_valid_index_for_every_element():
    arr = quick_sort([random.randint(0, 1000) for _ in range(200)])
    for i, value in enumerate(arr):
        assert arr[binary_search(arr, value)] == value
