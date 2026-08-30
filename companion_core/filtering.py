from collections import deque
from typing import Deque, Optional

from companion_core.config import HEALTH


class Ema:
    def __init__(self, alpha: float = HEALTH.ema_alpha):
        self.alpha = alpha
        self.value: Optional[float] = None

    def update(self, x: Optional[float]) -> Optional[float]:
        if x is None:
            return self.value
        if self.value is None:
            self.value = x
        else:
            self.value = self.alpha * x + (1.0 - self.alpha) * self.value
        return self.value


class Trend:
    def __init__(self, window: int = HEALTH.trend_window):
        self.buf: Deque[float] = deque(maxlen=window)

    def update(self, x: Optional[float]) -> Optional[float]:
        if x is None:
            return self.slope()
        self.buf.append(x)
        return self.slope()

    def slope(self) -> Optional[float]:
        n = len(self.buf)
        if n < 3:
            return None
        # simple endpoint slope per sample
        return (self.buf[-1] - self.buf[0]) / float(n - 1)
