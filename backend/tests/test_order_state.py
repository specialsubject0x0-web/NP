"""訂單狀態機（R-08）：把所有「狀態 × 狀態」的組合都測一遍，只有規定的箭頭會通過。"""

import pytest

from app.core.errors import AppError
from app.services.order_state import can_transition, ensure_transition

STATUSES = ['pending_payment', 'paid', 'shipped', 'completed', 'cancelled']
ALLOWED = {('pending_payment', 'paid'), ('pending_payment', 'cancelled'), ('paid', 'shipped'), ('shipped', 'completed')}


@pytest.mark.parametrize('current', STATUSES)
@pytest.mark.parametrize('target', STATUSES)
def test_every_transition(current: str, target: str) -> None:
    expected = (current, target) in ALLOWED
    assert can_transition(current, target) is expected
    if expected:
        ensure_transition(current, target)
    else:
        with pytest.raises(AppError) as exc:
            ensure_transition(current, target)
        assert exc.value.status_code == 409 and exc.value.code == 'ORDER_INVALID_TRANSITION'


def test_unknown_status_rejected() -> None:
    assert can_transition('hacked', 'paid') is False
