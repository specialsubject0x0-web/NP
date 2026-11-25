# ADR-004 模擬金流與回呼簽章
- 狀態：已採用（人決定：模擬付款）
- 決定：`POST /orders/{id}/payments` 建立一筆付款（交易編號），由後端的「模擬金流」模組產生已簽章的回呼內容，
  再交給與真實金流**同一個**回呼處理函式 `payment_service.handle_callback`。外部也可呼叫 `POST /payments/callback`（測試用、未來接真金流用）。
  簽章：HMAC-SHA256(`PAYMENT_WEBHOOK_SECRET`, `transaction_id|order_id|amount|status`)，用 `hmac.compare_digest` 比對。
- 冪等：`payments.transaction_id` 唯一；已處理過的交易再次回呼直接回傳目前狀態。
- 未來換真金流時：只替換模擬金流模組與簽章格式，訂單狀態邏輯不用改。
