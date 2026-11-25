# 購物網站（AI 協作開發・前後端分離）

## 使用方式
1. 把整個資料夾放到你的專案根目錄，執行 `git init`，在此資料夾啟動 Claude Code（或其他 Harness）。
2. 先請 Agent 讀取 AGENTS.md，並逐項回答第 7 章「待人決定事項」（尤其是第 12 項：老師對前端修改的要求）。
3. 依序：PO 寫 Epic/Story → SA/UI/DBA 設計並定案 API 契約 → Scrum Master 規劃 Sprint → 人核可 → 前後端平行開發 → PR + CI + 三種審查 → 人合併。
4. 學生要手動修改前端：先在 `docs/frontend-changes.md` 登記預計修改的項目，再用 `npm run dev:mock` 邊改邊看。
5. 每個 Sprint 結束後，請 scrum-master 更新 `docs/presentation/results-log.md`，之後照 `presentation-brief.md` 製作簡報。
6. 每個 Sprint 回顧後，把踩過的坑補進 AGENTS.md 第 9 章。

## 資料夾
- `backend/`：FastAPI 純 API
- `frontend/`：Vue 3 + Vite 單頁應用（可獨立運行）
- `docs/api/openapi.yaml`：前後端唯一契約
- `docs/presentation/`：老師的簡報大綱與內容規劃（presentation-brief.md）、素材與結果紀錄（results-log.md）
- `docs/code-guide.md`：程式碼導覽（給看得懂用）
- `.claude/agents/`：11 個角色
