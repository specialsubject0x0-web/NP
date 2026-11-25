---
id: US-001
epic: EP-001
title: （Story 名稱）
points: 0
priority: must   # must / could
scope: fe+be     # fe / be / fe+be
api_contract: 無 # 涉及的 openapi.yaml 路徑，如 POST /api/v1/orders
status: todo
---
## 使用者故事
身為〔角色〕，我想要〔功能〕，以便〔價值〕。

## 驗收條件（Given / When / Then）
- AC1（正面）：Given ... When ... Then ...（引用 R-xx）
- AC2（負面）：Given ... When ... Then ...（例：越權、非法輸入）
- AC3（錯誤）：id 不存在或格式錯誤 → 404，不洩露內部細節

## 業務規則
- R-xx：...

## 假設（需人確認）
- ...

## 相依
- 無 / US-xxx

## 安全考量
- 權限 / 輸入驗證 / 輸出轉義 / 個人資料

## Task 清單（Sprint 規劃時由開發者拆出；前端、後端分開）
- T-xxx（backend）...
- T-xxx（frontend）...

## DoR（五項打勾才能放進 Sprint）
- [ ] 價值明確  - [ ] 驗收條件可測試  - [ ] 已估點  - [ ] 無未解決相依  - [ ] API 契約已定案
