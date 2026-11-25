# ADR-003 防超賣用條件式 UPDATE
- 狀態：已採用
- 選項：(a) `SELECT ... FOR UPDATE` 列鎖（SQLite 不支援）；(b) 樂觀鎖 version 欄位；(c) 條件式 UPDATE `WHERE stock >= :qty`。
- 決定：(c)。單一 SQL 即可原子完成「檢查＋扣除」，SQLite 與 PostgreSQL 行為一致，程式最短、學生最好懂。
- 驗證：`tests/test_concurrency.py` 用多執行緒同時搶最後一件，斷言只有一筆成功、庫存不為負。
