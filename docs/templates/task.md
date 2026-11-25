---
id: T-001
story: US-001
role: backend-developer   # 或 frontend-developer 等
scope: backend            # backend / frontend / docs
status: todo
depends_on: []
---
## 說明
為誰而做、要交出什麼。

## 使用者決定的設計輸入（附日期）
- YYYY-MM-DD：...

## 完成條件（具體列出檔案與內容）
- ...

## 對應 API 契約
- docs/api/openapi.yaml：...（無則寫「無」）

## ADR（重要技術選擇與原因）
- ADR-xxx：...

## 技術備註
- 只可修改：...（範圍限制）
- 相依：T-xxx 合併後才開始
- 前端 Task：可修改處需加註解標示；需先讀 git diff，保留人的手動修改

## 審查紀錄
| 日期 | 角色 | 結論 | 備註 |
|---|---|---|---|

## DoD（全部打勾才算完成）
- [ ] 後端：ruff／mypy 通過，pytest 通過且分支覆蓋率 ≥ 80%
- [ ] 前端：lint／typecheck／build 通過，Vitest 覆蓋率 ≥ 70%
- [ ] 與 openapi.yaml 一致
- [ ] Code Review  - [ ] Security Review  - [ ] QA 驗收
- [ ] 程式碼註解符合 AGENTS.md 5.4，docs/code-guide.md 已更新
- [ ] 文件已更新；若有手動修改，已登記於 docs/frontend-changes.md
