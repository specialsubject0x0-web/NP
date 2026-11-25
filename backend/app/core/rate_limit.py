"""簡單的限速器（R-15）：在一段時間內，同一個 key 最多允許幾次。

用在：登入失敗、下單、優惠券試算，避免被暴力嘗試或洗單。
【重要】計數存在程式記憶體中，只適用單一台伺服器（假設 A-07）。多台伺服器要改用 Redis（需人同意新增服務）。
"""

import threading
import time
from collections import defaultdict, deque

from app.core import business_rules as rules


class RateLimiter:
    """滑動視窗限速器。limit：最多幾次；window_seconds：幾秒內。"""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()  # 多個請求同時進來時，避免計數算錯

    def _prune(self, key: str, now: float) -> deque[float]:
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        return hits

    def is_blocked(self, key: str) -> bool:
        """這個 key 是否已經用完次數（不增加次數）。"""
        with self._lock:
            return len(self._prune(key, time.monotonic())) >= self.limit

    def hit(self, key: str) -> bool:
        """記錄一次；回傳 True 代表「還在限制內」，False 代表超過了。"""
        with self._lock:
            now = time.monotonic()
            hits = self._prune(key, now)
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    def reset(self, key: str | None = None) -> None:
        """清除紀錄（登入成功時清除該帳號的失敗次數；測試時清除全部）。"""
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)


login_failures = RateLimiter(rules.LOGIN_MAX_FAILURES, rules.LOGIN_WINDOW_SECONDS)
order_actions = RateLimiter(rules.ORDER_RATE_LIMIT, rules.ORDER_RATE_WINDOW_SECONDS)


def reset_all() -> None:
    """測試用：清空所有限速紀錄。"""
    login_failures.reset()
    order_actions.reset()
