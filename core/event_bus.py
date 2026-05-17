from collections.abc import Callable


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable) -> Callable:
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)
        return callback

    def off(self, event: str, callback: Callable) -> None:
        if event in self._subscribers:
            self._subscribers[event].remove(callback)

    def emit(self, event: str, **data) -> None:
        for callback in self._subscribers.get(event, []):
            callback(**data)

    def clear(self) -> None:
        self._subscribers.clear()
