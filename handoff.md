# 交接（handoff）

> AGENTS.md 3.6：進度寫進檔案，不要只留在對話裡。

## 目前狀態（2026-11-25）
- 分支 `feature/sprint-1-mvp`：Sprint 1 全部 Task（T-001～T-019）已實作並 commit，**尚未合併到 main**
- 本機檢查全部通過：後端 ruff／mypy／pytest 138 個（分支覆蓋率 97%）／pip-audit；前端 lint／typecheck／Vitest 42 個（行覆蓋率 95%）／build／npm audit／Playwright E2E 1 個
- 獨立 Agent 審查結果：`docs/reviews/sprint-1-review.md`

## 人已做的決定
見 `docs/decisions.md` 第一節（Vue 3、模擬付款、運費 60 滿 1000 免運、須登入結帳、做優惠券）。

## 等人處理（依序）
1. 確認 `docs/decisions.md` 第二節假設 A-01～A-15 與第三節新增套件
2. 推到 GitHub、開 PR，看 CI 是否通過（GitHub 上的結果尚未取得）
3. 人做 Code／Security／QA 審查後決定是否合併
4. 回覆第 7 章第 12、13 項（老師要求修改哪些前端項目、簡報形式），並在 `docs/frontend-changes.md` 登記
5. 正式部署前：設定 `SHOP_ENV=production`、隨機的 `SHOP_PAYMENT_WEBHOOK_SECRET`、正確的 `SHOP_CORS_ORIGINS`，資料庫改 PostgreSQL（需人同意新增驅動）

## 下一步建議（下一個 Sprint 候選）
- 已付款訂單的退款流程（金額規則須人決定，A-05）
- 未付款訂單逾時自動取消（A-14）
- 後台優惠券管理畫面
- 多台伺服器時的限速改用 Redis（A-07）
