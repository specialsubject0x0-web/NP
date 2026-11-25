// 【手動修改區】站台設定（AGENTS.md 3.9）
// 這個檔案放「全站都會用到、可以放心改」的設定。改完存檔，瀏覽器會立刻更新（熱更新）。
// 改之前請先到 docs/frontend-changes.md 登記你要改什麼。
// 注意：這裡的數字只影響「畫面」，不會改變後端的價格、運費等規則（那些由後端決定）。

export const siteConfig = {
  // 【可修改】店名：出現在頁首、瀏覽器分頁標題、頁尾
  shopName: '小日子雜貨舖',

  // 【可修改】標語：出現在首頁大標題下方與頁首店名旁
  tagline: '把日常用品挑得仔細一點',

  // 【可修改】商品列表每頁顯示幾個（1–50；超過 50 後端會拒絕）
  productsPerPage: 12,

  // 【可修改】寬螢幕時，商品卡片每列顯示幾個（建議 2–5）。手機上會自動變少
  productsPerRow: 4,

  // 【可修改】庫存少於等於這個數字時，商品卡片會蓋上紅色「僅剩 N 件」印章
  lowStockThreshold: 3,

  // 【可修改】首頁要不要顯示「精選商品」區塊（true 顯示／false 隱藏）
  showFeaturedOnHome: true,

  // 【可修改】首頁精選商品顯示幾個
  featuredCount: 4,

  // 【可修改】首頁要不要顯示分類捷徑
  showCategoriesOnHome: true,

  // 【可修改】頁首要不要顯示「常見問題」連結
  showFaqLink: true,

  // 【重要】語系與時區：影響金額與時間的顯示格式。後端時間是 UTC，這裡轉成台灣時間顯示
  locale: 'zh-TW',
  timeZone: 'Asia/Taipei',
} as const

export type SiteConfig = typeof siteConfig
