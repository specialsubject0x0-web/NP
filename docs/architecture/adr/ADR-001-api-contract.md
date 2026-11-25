# ADR-001 前後端分離與 API 契約產生方式
- 狀態：已採用（2026-11-25）
- 背景：AGENTS.md 要求 `docs/api/openapi.yaml` 是唯一介面，且「後端由 FastAPI 自動產生並與契約比對」。
- 決定：契約內容以後端 pydantic schema 為來源，用 `backend/scripts/export_openapi.py` 匯出成 `docs/api/openapi.yaml` 後**凍結並 commit**。
  後端測試 `tests/test_contract.py` 比對「程式目前產生的契約」與「commit 的契約」，不一致就失敗。
  前端用 `npm run gen:api` 由同一份 yaml 產生型別。
- 後果：任何人改了 schema 卻沒更新契約，CI 會擋下；要更新契約必須重新匯出並在 PR 中由人核可（AGENTS.md 3.7）。
