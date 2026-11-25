# ADR-002 登入狀態用 Cookie Session ＋ CSRF
- 狀態：已採用
- 決定：登入後發一個隨機 session token，放在 `httpOnly`＋`SameSite=Lax`（正式環境＋`Secure`）的 Cookie `shop_session`；
  資料庫只存 token 的 SHA-256（資料庫外洩也拿不到可用的 token）。
  另發一個非 httpOnly 的 Cookie `shop_csrf`，前端讀出後放在 `X-CSRF-Token` 標頭；後端比對該值與 Session 中儲存的值（同步權杖模式）。
- 【為什麼】不把 token 放 localStorage：XSS 時 JavaScript 讀不到 httpOnly Cookie。CSRF token 防止其他網站借用使用者的 Cookie 送出請求。
