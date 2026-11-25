# ADR-005 金額用整數元
- 狀態：已採用（假設 A-01，待人確認）
- 決定：所有金額欄位為 `int`，單位「新台幣元」，回應中同時帶 `currency: "TWD"`。禁止 float。
- 百分比折扣計算：`discount = subtotal * percent // 100`（無條件捨去，對顧客與店家都可預期），再套用 `max_discount` 上限。
