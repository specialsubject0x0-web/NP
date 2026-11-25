# 程式碼導覽（給看不熟程式的人）

> 由開發角色在**每個 Task 完成時**更新自己負責的部分。目的：讓學生與老師看得懂「這個檔案是做什麼的、怎麼改」。
> 每個程式檔案開頭也都有 3–5 行中文說明；標記 `【可修改】` 的地方可以放心改，`【重要】` 的地方改之前要先問。

## 先看這裡：一個請求怎麼走
```
使用者按「加入購物車」
 → frontend/src/views/ProductDetailView.vue（畫面）
 → frontend/src/stores/cart.ts（記住購物車內容）
 → frontend/src/api/cart.ts → api/client.ts（唯一送出 HTTP 的地方，自動帶 CSRF）
 → backend/app/routers/cart.py（收到請求、檢查格式與登入）
 → backend/app/services/cart_service.py（商業規則：不能超過庫存）
 → backend/app/repositories/cart_repo.py（存進資料庫）
```

## 前端（frontend/）
| 檔案 | 用途 | 重要概念 | 怎麼改（【可修改】） |
|---|---|---|---|
| `src/config/site.config.ts` | 店名、標語、每頁商品數、每列幾個、首頁區塊開關 | 設定驅動：可變的東西集中在這裡 | 直接改數值或文字，存檔即時更新 |
| `src/theme/tokens.css` | 顏色、字型、字級、間距、圓角 | CSS 變數（design token） | 改顏色值，全站一起變；注意文字對比 |
| `src/content/*.json` | 首頁、頁尾、常見問題的文字 | 內容與程式分開 | 只改引號內文字；FAQ 照格式新增一組 |
| `src/theme/base.css` | 按鈕、表單、表格等共用樣式 | 使用 tokens.css 的變數 | 一般不用改；要改外觀先改 tokens |
| `src/views/*.vue` | 每個網址一個頁面 | 頁面＝組合元件＋呼叫 api | 調整版面、文字、元件順序 |
| `src/components/ProductImage.vue` | 商品佔位圖（色塊＋第一個字） | 沒有授權照片時的替代方案 | 換成 `<img>`（記得 alt） |
| `src/components/StockStamp.vue` | 「僅剩 N 件／已售完」印章 | 門檻在 site.config.ts | 改文字或樣式 |
| `src/components/ProductGrid.vue` | 商品格線 | 每列數量來自設定 | 改 site.config.ts 的 productsPerRow |
| `src/components/*.vue`（其他） | 頁首、頁尾、數量、分頁、地址、金額明細… | 小而單一職責 | 看檔案開頭說明 |
| `src/api/client.ts` | 【重要】唯一呼叫後端的地方 | Cookie、CSRF、錯誤格式 | 不要在元件裡直接 fetch |
| `src/api/*.ts` | 每個功能一組 API 函式 | 型別來自 openapi.yaml | 後端有新 API 時在這裡加函式 |
| `src/types/api.d.ts` | API 型別（自動產生） | `npm run gen:api` 產生 | **勿手改** |
| `src/stores/*.ts` | 登入狀態、購物車（Pinia） | 多個畫面共用的資料 | — |
| `src/router/index.ts` | 網址對應頁面、登入檢查 | 前端檢查只是體驗，權限在後端 | 新增頁面時在這裡加一行 |
| `src/composables/format.ts` | 金額、時間、訂單狀態中文 | UTC → 台灣時間 | 改狀態中文名稱 |
| `src/mocks/*` | Mock 模式假後端（MSW） | `npm run dev:mock` 不需後端 | 想多幾個示範商品改 seed-data.json |
| `tests/*.spec.ts` | Vitest 元件與頁面測試 | 用同一份 Mock 假後端 | — |
| `e2e/shopping.spec.ts` | Playwright 主流程測試 | 真瀏覽器跑一遍購物 | — |

## 後端（backend/）
| 檔案 | 用途 | 重要概念 | 注意事項（【重要】） |
|---|---|---|---|
| `app/main.py` | 程式進入點、CORS、安全標頭 | 所有 API 前綴 `/api/v1` | CORS 不可設 `*` |
| `app/core/config.py` | 設定（讀 .env） | 機密只放 .env | 正式環境必須換金流金鑰 |
| `app/core/business_rules.py` | 運費、上限等數字 | 金錢規則 | **人決定的數字，Agent 不得自改** |
| `app/core/deps.py` | 登入、管理員、CSRF、限速、冪等鍵檢查 | FastAPI 依賴 | 權限一律在後端判斷 |
| `app/core/security.py` | 密碼雜湊、token、金流簽章 | argon2、HMAC | 不要自己發明加密 |
| `app/core/errors.py` | 統一錯誤格式 | 不洩露內部細節 | — |
| `app/models/*.py` | 資料表（dba） | 金額是整數元 | 改了要產生 Migration |
| `migrations/versions/*.py` | 資料庫結構變更腳本 | Alembic | `tests/test_migrations.py` 檢查一致 |
| `app/schemas/*.py` | API 輸入輸出格式＝契約 | 拒絕多餘欄位 | 改了要重新匯出契約並經人核可 |
| `app/routers/*.py` | 收 HTTP 請求 | 只處理 HTTP | 不寫商業規則 |
| `app/services/pricing_service.py` | 【重要】全站唯一算金額的地方 | 運費、優惠券 | 改前先讀 R-03、R-12 |
| `app/services/order_service.py` | 建立／取消訂單 | 同一交易扣庫存、冪等 | 不要拆開扣庫存與建單 |
| `app/services/order_state.py` | 訂單狀態機 | 只允許規定的轉換 | 新增狀態須經人同意 |
| `app/services/payment_service.py` | 模擬金流與回呼 | 簽章驗證、冪等 | 不存卡號 |
| `app/repositories/product_repo.py` | 商品查詢、扣庫存 | 條件式 UPDATE 防超賣 | 不要改成先查再扣 |
| `scripts/seed.py` | 建表＋示範資料 | 開發用 | 正式環境禁止執行 |
| `scripts/export_openapi.py` | 匯出 API 契約 | 契約來源 | 匯出後要人核可 |
| `tests/` | pytest（含負面測試、並發測試、契約測試） | 每個 Bug 先寫重現測試 | — |

## 名詞小辭典
| 名詞 | 白話說明 |
|---|---|
| API | 前端向後端要資料或送資料的「窗口」 |
| Mock | 假的後端，讓前端不需真的後端也能跑 |
| 元件（Component） | 畫面上可重複使用的一小塊，例如商品卡片 |
| 契約（OpenAPI） | 前後端約定好「網址、要送什麼、會收到什麼」的文件 |
| Cookie／httpOnly | 瀏覽器幫網站保存的小資料；httpOnly 代表 JavaScript 讀不到，比較安全 |
| CSRF | 壞網站冒用你的登入狀態送請求；用 CSRF token 擋 |
| 冪等（Idempotency） | 同一個請求送很多次，結果跟送一次一樣（不會重複下單） |
| 交易（Transaction） | 一組資料庫動作「全部成功或全部取消」 |
| Migration | 資料庫結構的版本紀錄，像資料表的 git |
| 雜湊（Hash） | 把密碼變成無法還原的亂碼 |
