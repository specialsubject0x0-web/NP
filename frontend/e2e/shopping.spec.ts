// 主流程 E2E（EP-001 成功指標）：找商品 → 加入購物車 → 結帳（含優惠碼）→ 付款 → 查訂單。
import { expect, test } from '@playwright/test'

test('會員完成一次購物', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('小日子雜貨舖')

  // 搜尋並進入商品
  await page.getByLabel('搜尋商品').fill('濾杯')
  await page.getByRole('button', { name: '搜尋' }).click()
  await page.getByRole('link', { name: /手沖咖啡濾杯/ }).click()

  // 未登入加入購物車 → 先登入，再回到商品頁
  await page.getByRole('button', { name: '加入購物車' }).click()
  await page.getByLabel('Email').fill('demo@example.com')
  await page.getByLabel('密碼').fill('demo12345')
  await page.getByRole('button', { name: '登入' }).click()
  await expect(page).toHaveURL(/\/products\/1$/)
  await page.getByRole('button', { name: '加入購物車' }).click()
  await expect(page.getByRole('status')).toContainText('已加入購物車')

  // 結帳：新增地址、套用優惠碼（680 − 100 + 運費 60 = 640）
  // 注意：Mock 模式的資料在記憶體，不能用 page.goto 重新載入（會還原），要用站內連結
  await page.getByRole('link', { name: '去結帳' }).click()
  await expect(page.getByRole('heading', { name: '購物車' })).toBeVisible()
  await page.getByRole('link', { name: '前往結帳' }).click()
  await page.getByLabel('收件人').fill('王小明')
  await page.getByLabel('電話').fill('0912345678')
  await page.getByLabel('郵遞區號').fill('100')
  await page.getByLabel('縣市').fill('台北市')
  await page.getByLabel('地址', { exact: true }).fill('重慶南路一段 1 號')
  await page.getByRole('button', { name: '儲存地址' }).click()
  await page.getByLabel('優惠碼（一次限用一張）').fill('WELCOME100')
  await page.getByRole('button', { name: '套用' }).click()
  await expect(page.locator('.total')).toContainText('NT$640')
  await page.getByRole('button', { name: '送出訂單' }).click()

  // 付款
  await expect(page.getByRole('status')).toContainText('訂單已成立')
  await page.getByRole('button', { name: '付款（模擬）' }).click()
  await expect(page.getByRole('status')).toContainText('付款完成')

  // 我的訂單
  await page.getByRole('link', { name: '我的訂單' }).click()
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await expect(page.locator('tbody')).toContainText('已付款')
})
