"""防超賣並發測試（R-06、ADR-003）：多人同時搶最後一件，只能有一人成功。"""

import threading
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import AppError
from app.core.security import hash_password
from app.models import Address, CartItem, Product, User
from app.services import order_service

BUYERS = 8


def test_last_item_sold_only_once(session_factory: sessionmaker[Session]) -> None:
    pw = hash_password('buyer12345')
    with session_factory() as db:
        users = []
        for i in range(BUYERS):
            user = User(email=f'buyer{i}@example.com', password_hash=pw, name=f'買家{i}', role='member')
            db.add(user)
            db.flush()
            db.add(CartItem(user_id=user.id, product_id=12, quantity=1))  # 限量陶杯，庫存 1
            db.add(Address(user_id=user.id, recipient='買家', phone='0912345678', postal_code='100', city='台北市', line='某路 1 號'))
            users.append(user.id)
        db.commit()

    results: list[str] = []
    lock = threading.Lock()
    barrier = threading.Barrier(BUYERS)

    def buy(user_id: int) -> None:
        with session_factory() as db:
            user = db.get(User, user_id)
            assert user is not None
            address = db.query(Address).filter_by(user_id=user_id).one()
            barrier.wait()  # 大家同時開始
            outcome: Any
            try:
                order_service.create_order(db, user, address.id, None, f'concurrent-{user_id:04d}')
                outcome = 'ok'
            except AppError as exc:
                outcome = exc.code
            with lock:
                results.append(outcome)

    threads = [threading.Thread(target=buy, args=(uid,)) for uid in users]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count('ok') == 1
    assert all(r == 'ORDER_OUT_OF_STOCK' for r in results if r != 'ok')
    with session_factory() as db:
        product = db.get(Product, 12)
        assert product is not None and product.stock == 0
