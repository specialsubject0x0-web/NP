"""契約測試（ADR-001）：程式產生的 API 契約必須和 docs/api/openapi.yaml 完全一致。

失敗代表：有人改了 API 的輸入輸出，卻沒有更新契約。
修正方式：確認變更已經人核可後，執行 `uv run python -m scripts.export_openapi` 並 commit 契約檔。
"""

import yaml

from scripts.export_openapi import CONTRACT, build_contract


def test_contract_matches_code() -> None:
    committed = yaml.safe_load(CONTRACT.read_text(encoding='utf-8'))
    assert committed == build_contract(), '程式與 docs/api/openapi.yaml 不一致，請見本檔說明'


def test_contract_never_exposes_password_hash() -> None:
    assert 'password_hash' not in CONTRACT.read_text(encoding='utf-8')
