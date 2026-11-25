"""安全相關的小工具：密碼雜湊、隨機 token、金流簽章。

名詞：
- 雜湊（hash）：把密碼變成無法還原的亂碼；登入時比對亂碼是否相同，資料庫不存明碼。
- HMAC 簽章：用只有我們和金流知道的金鑰，對內容算出一個「印章」，用來確認回呼真的是金流送的。
【重要】不要把這裡改成自己發明的加密方法；使用經過驗證的函式庫（argon2、hmac）。
"""

import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
# 【為什麼】帳號不存在時也做一次雜湊比對，讓「帳號不存在」和「密碼錯」花的時間差不多，攻擊者無法從回應時間猜帳號
_DUMMY_HASH = _hasher.hash('dummy-password-for-timing')


def hash_password(password: str) -> str:
    """把明碼密碼轉成 argon2 雜湊字串。"""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """比對密碼；password_hash 為 None（帳號不存在）時也會花相同時間再回傳 False。"""
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except VerificationError, InvalidHashError:
        return False


def new_token() -> str:
    """產生無法猜到的隨機字串（給 Session 與 CSRF 用）。"""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Session token 存進資料庫前先做 SHA-256，資料庫外洩也拿不到可登入的 token。"""
    return hashlib.sha256(token.encode()).hexdigest()


def tokens_equal(a: str | None, b: str | None) -> bool:
    """安全比較兩個字串（固定時間比較，避免時間差攻擊）。"""
    if not a or not b:
        return False
    return hmac.compare_digest(a, b)


def sign_payment(secret: str, transaction_id: str, order_id: int, amount: int, status: str) -> str:
    """計算金流回呼簽章：HMAC-SHA256(金鑰, "交易編號|訂單編號|金額|狀態")。"""
    message = f'{transaction_id}|{order_id}|{amount}|{status}'.encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
