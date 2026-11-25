"""訂單狀態機（R-08）。

狀態只能照下面的箭頭走：
    pending_payment（待付款）→ paid（已付款）→ shipped（已出貨）→ completed（已完成）
    pending_payment（待付款）→ cancelled（已取消）
【重要】要新增狀態或箭頭，必須先改 business-rules.md 並經人同意，再同步修改 tests/test_order_state.py。
"""

from app.core.errors import AppError

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    'pending_payment': frozenset({'paid', 'cancelled'}),
    'paid': frozenset({'shipped'}),
    'shipped': frozenset({'completed'}),
    'completed': frozenset(),
    'cancelled': frozenset(),
}


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def ensure_transition(current: str, target: str) -> None:
    """不合法的轉換 → 409 ORDER_INVALID_TRANSITION。"""
    if not can_transition(current, target):
        raise AppError(409, 'ORDER_INVALID_TRANSITION', '訂單目前的狀態不能進行這個操作', {'from': current, 'to': target})
