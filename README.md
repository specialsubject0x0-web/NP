# 購物網站（AI 協作開發・前後端分離）

示範店名「小日子雜貨舖」。後端 FastAPI、前端 Vue 3，依 `AGENTS.md` 規範開發。

## 快速開始

### 只看前端（不需要後端，課堂展示與學生修改用）
```bash
cd frontend
npm install
npm run dev:mock        # 打開 http://localhost:5173
```
示範帳號：`demo@example.com／demo12345`（會員）、`admin@example.com／admin12345`（管理員）。
示範優惠碼：`WELCOME100`（滿 500 折 100）、`SAVE10`（9 折最多折 200）、`EXPIRED50`（已過期）。
Mock 模式的資料存在瀏覽器記憶體，**重新整理頁面會還原**。

### 前後端一起跑
```bash
# 終端機 1：後端（需要 uv 與 Python 3.14）
cd backend
cp .env.example .env
uv sync
uv run python -m scripts.seed               # 建資料表＋示範資料
uv run uvicorn app.main:app --reload        # http://127.0.0.1:8000/docs 可看 API 文件

# 終端機 2：前端
cd frontend
npm install
npm run dev             # http://localhost:5173，/api 會自動轉給後端
```

### 檢查（和 CI 相同）
```bash
cd backend && uv run ruff check . && uv run mypy app && uv run pytest --cov=app --cov-branch --cov-fail-under=80
cd frontend && npm run lint && npm run typecheck && npm run test && npm run build && npm run e2e
```

### 放上 GitHub
```bash
git remote add origin https://github.com/<你的帳號>/<倉庫>.git
git push -u origin main
git push -u origin feature/sprint-1-mvp   # 然後在 GitHub 開 Pull Request，CI 會自動執行
```
`main` 只有原始規範；全部程式在 `feature/sprint-1-mvp`，依 AGENTS.md 3.5「合併由人決定」。

## 重要文件
- `docs/decisions.md`：**請先看**。人已決定的事項，以及 Agent 先採用、需要你確認的假設
- `docs/regulations/business-rules.md`：業務規則 R-01～R-18
- `docs/code-guide.md`：程式碼導覽
- `handoff.md`：目前進度與下一步

## 原始使用說明

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
