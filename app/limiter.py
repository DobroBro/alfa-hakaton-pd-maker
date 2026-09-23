class InFlightLimiter:
    def __init__(self, max_in_flight: int) -> None:
        self._max = max_in_flight
        self._current = 0

    def try_acquire(self) -> bool:
        if self._current >= self._max:
            return False
        self._current += 1
        return True

    def release(self) -> None:
        self._current -= 1