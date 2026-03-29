import random
from typing import Dict, List, Tuple, TypeVar, Union

T = TypeVar("T")


def weighted_choice(options: Union[Dict[T, int], List[Tuple[T, int]]]) -> T:
    """
    Выбирает случайный элемент на основе весов.

    Args:
        options: dict {item: weight} или list [(item, weight), ...]

    Returns:
        Случайно выбранный элемент
    """
    if isinstance(options, dict):
        items = list(options.keys())
        weights = list(options.values())
    else:
        items, weights = zip(*options)

    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0

    for item, weight in zip(items, weights):
        cumulative += weight
        if r <= cumulative:
            return item

    return items[-1]


def weighted_choice_multiple(
        options: Union[Dict[T, int], List[Tuple[T, int]]],
        n: int,
        allow_duplicates: bool = False,
) -> List[T]:
    """
    Выбирает n уникальных элементов на основе весов.

    Args:
        options: dict {item: weight} или list [(item, weight), ...]
        n: количество элементов для выбора
        allow_duplicates: разрешить повторы (False = без повторов)

    Returns:
        Список из n случайных элементов
    """
    if isinstance(options, dict):
        items = list(options.keys())
        weights = list(options.values())
    else:
        items, weights = zip(*options)

    if not allow_duplicates and n > len(items):
        n = len(items)

    result = []
    remaining_items = list(zip(items, weights))

    for _ in range(n):
        if not remaining_items:
            break

        item_weights = dict(remaining_items)
        chosen = weighted_choice(item_weights)
        result.append(chosen)

        if not allow_duplicates:
            remaining_items = [(i, w) for i, w in remaining_items if i != chosen]

    return result


def percent_chance(percent: float) -> bool:
    """
    Проверяет шанс с заданной вероятностью.

    Args:
        percent: вероятность от 0 до 100

    Returns:
        True с вероятностью percent%
    """
    return random.random() * 100 < percent


def random_range(
        start: Union[int, float], end: Union[int, float], step: Union[int, float] = 1
) -> Union[int, float]:
    """
    Возвращает случайное число в диапазоне с шагом.

    Args:
        start: начало диапазона
        end: конец диапазона (включительно)
        step: шаг (для int и float)

    Returns:
        Случайное число в диапазоне
    """
    if step == 1 and isinstance(start, int) and isinstance(end, int):
        return random.randint(start, end)
    else:
        count = int((end - start) / step)
        return start + random.randint(0, count) * step
