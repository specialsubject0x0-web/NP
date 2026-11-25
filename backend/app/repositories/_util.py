"""repositories 共用的小工具。"""

from typing import Any, cast

from sqlalchemy import CursorResult, Result


def affected_one(result: Result[Any]) -> bool:
    """UPDATE／DELETE 是否剛好影響 1 列（條件式更新成功的判斷方式）。"""
    return cast(CursorResult[Any], result).rowcount == 1
