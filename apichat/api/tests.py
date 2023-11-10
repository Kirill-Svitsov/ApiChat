# from django.test import TestCase
import time
from functools import wraps

unsorted_array = [3, 2, 4, 2, 5, 1, 0, 4, 6, 9, 3, 7, 8, 4, 3, 3, 3]


def time_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        print(f'Функция {func.__name__} начала свою работу')
        result = func(*args, **kwargs)
        time.sleep(1.5)
        finish = time.time() - start
        print(f'Функция {func.__name__} завершила свою работу,'
              f'потребовалось {finish} секунд')
        print(f'Результат = {result}')
        return result

    return wrapper


@time_decorator
def bubble_sort(array: list) -> list:
    """Квардратичная сортировка пузырьком. O(N**2)"""
    for index in range(1, len(array)):
        for bubble in range(len(array) - index):
            if array[bubble] > array[bubble + 1]:
                (array[bubble],
                 array[bubble + 1]) = array[bubble + 1], array[bubble]
    return array


def merge_sort(array: list) -> list:
    """Сортировка слиянием. O(logN)"""
    if len(array) < 2:
        return array
    left_array = merge_sort(array[0: len(array) // 2])
    right_array = merge_sort(array[len(array) // 2:])
    sorted_array = [0] * len(array)
    sort = left = right = 0
    while left < len(left_array) and right < len(right_array):
        if left_array[left] <= right_array[right]:
            sorted_array[sort] = left_array[left]
            left += 1
        else:
            sorted_array[sort] = right_array[right]
            right += 1
        sort += 1
    while left < len(left_array):
        sorted_array[sort] = left_array[left]
        left += 1
        sort += 1
    while right < len(right_array):
        sorted_array[sort] = right_array[right]
        right += 1
        sort += 1
    return sorted_array


sorted_array = bubble_sort(unsorted_array)
lookup = 3
left = 0
right = len(unsorted_array)


def binary_search(array: list, lookup: int, left: int, right: int) -> int:
    """Бинарный поиск в отсортированном массиве. O(logN)"""
    if right <= left:
        return -1
    middle = (left + right) // 2
    if lookup == array[0]:
        return 0
    elif array[middle] == lookup:
        for index in range(middle, 0, -1):
            if array[index - 1] < array[index]:
                return index
    elif lookup < array[middle]:
        return binary_search(array, lookup, left, middle)
    return binary_search(array, lookup, middle + 1, right)


print(binary_search(sorted_array, lookup, left, right))
