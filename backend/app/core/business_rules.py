"""金錢與數量相關的業務規則常數（對應 docs/regulations/business-rules.md）。

【重要】這裡每個數字都是「人決定的金錢規則」（AGENTS.md 3.7），Agent 不得自行修改。
要改請先更新 business-rules.md 並經人同意，再改這裡，並同步修改測試。
"""

CURRENCY = 'TWD'  # R-01：只用新台幣，金額單位為「元」（整數）

SHIPPING_FEE = 60  # R-03：運費 60 元
FREE_SHIPPING_THRESHOLD = 1000  # R-03：折扣後商品金額達 1000 元免運

CART_MAX_QUANTITY = 99  # R-05：購物車單一商品數量上限

PAGE_SIZE_MAX = 50  # R-18：分頁每頁最多 50 筆

LOGIN_MAX_FAILURES = 5  # R-15：登入失敗次數上限
LOGIN_WINDOW_SECONDS = 300  # R-15：在 5 分鐘內計算
ORDER_RATE_LIMIT = 20  # R-15：下單／試算每分鐘上限
ORDER_RATE_WINDOW_SECONDS = 60

PERCENT_COUPON_MAX = 90  # R-12：百分比折扣最多 90%
