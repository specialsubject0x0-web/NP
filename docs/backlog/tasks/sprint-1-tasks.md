# Sprint 1 Task 清單

> 由 scrum-master 規劃。→ 表示有先後；‖ 表示可平行。API 契約（T-009）定案後，前端與後端可以平行。
> 每個 Task 的完成條件 = AGENTS.md 3.4 的 DoD。下表「狀態」以實際 commit 為準。

| Task | Story | 角色 | 範圍 | 內容 | 相依 | 狀態 |
|---|---|---|---|---|---|---|
| T-001 | — | dba | backend | 資料模型、ERD、Alembic 初始 Migration、種子資料 | — | done |
| T-002 | US-008 | backend-developer | backend | 註冊／登入／登出、Session Cookie、CSRF、登入限速、安全標頭 | → T-001 | done |
| T-003 | US-001, US-002 | backend-developer | backend | 商品與分類 API（搜尋、篩選、排序白名單、分頁） | → T-001 | done |
| T-004 | US-003, US-004 | backend-developer | backend | 購物車、地址 API（IDOR 防護） | → T-002 | done |
| T-005 | US-005, US-007 | backend-developer | backend | 結帳試算、建立訂單（同交易扣庫存、冪等）、訂單查詢與取消 | → T-004 | done |
| T-006 | US-006 | backend-developer | backend | 模擬金流、回呼簽章驗證、回呼冪等 | → T-005 | done |
| T-007 | US-009, US-010 | backend-developer | backend | 後台商品與訂單 API、狀態機 | → T-005 | done |
| T-008 | US-011 | backend-developer | backend | 優惠券計算 service（單一位置）＋規則測試 | → T-005 | done |
| T-009 | 全部 | system-analyst | docs | 匯出並凍結 `docs/api/openapi.yaml`、契約測試 | → T-002…T-008 | done |
| T-010 | — | frontend-developer | frontend | 專案骨架、手動修改區（config／theme／content）、API client、MSW | → T-009 | done |
| T-011 | US-008 | frontend-developer | frontend | 登入／註冊頁、登入狀態 store、路由守衛 | → T-010 | done |
| T-012 | US-001, US-002 | frontend-developer | frontend | 首頁、商品列表（搜尋篩選分頁）、商品詳情 | → T-010 ‖ T-011 | done |
| T-013 | US-003 | frontend-developer | frontend | 購物車頁 | → T-011 | done |
| T-014 | US-004 | frontend-developer | frontend | 地址選擇與新增 | → T-011 | done |
| T-015 | US-005, US-011 | frontend-developer | frontend | 結帳頁（後端試算、優惠碼、Idempotency-Key） | → T-013 ‖ T-014 | done |
| T-016 | US-006, US-007 | frontend-developer | frontend | 訂單列表／詳情、付款、取消 | → T-015 | done |
| T-017 | US-009, US-010 | frontend-developer | frontend | 後台商品與訂單頁 | → T-011 | done |
| T-018 | 全部 | tester | both | 後端負面測試、前端元件測試、Playwright E2E | ‖ 各 Task | done |
| T-019 | — | scrum-master | docs | CI 設定、code-guide、results-log | 最後 | done |
