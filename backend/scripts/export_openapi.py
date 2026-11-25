"""把後端程式產生的 API 契約匯出到 docs/api/openapi.yaml（ADR-001）。

執行：在 backend/ 執行 `uv run python -m scripts.export_openapi`
【重要】契約變更需要人核可（AGENTS.md 3.7）。匯出後請在 PR 說明改了哪些欄位，由人同意後才能合併。
"""

from pathlib import Path
from typing import Any

import yaml

from app.core.config import Settings
from app.main import create_app

CONTRACT = Path(__file__).resolve().parents[2] / 'docs' / 'api' / 'openapi.yaml'


def build_contract() -> dict[str, Any]:
    """用開發設定產生 OpenAPI 文件（內容與環境無關）。"""
    return create_app(Settings(env='development')).openapi()


def dump(spec: dict[str, Any]) -> str:
    header = '# 本檔由 backend/scripts/export_openapi.py 產生，是前後端唯一的 API 契約。請勿手改；變更須經人核可。\n'
    return header + yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, width=200)


if __name__ == '__main__':
    CONTRACT.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT.write_text(dump(build_contract()), encoding='utf-8')
    print(f'已匯出 {CONTRACT}')
