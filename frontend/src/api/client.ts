// 【重要】全站「唯一」直接呼叫後端的地方（AGENTS.md 3.9 B5）。元件請用 src/api/ 裡其他檔案的函式。
// 這個檔案負責：
//   1. 帶上登入 Cookie（credentials: 'include'）
//   2. 會改資料的請求自動帶上 CSRF token（X-CSRF-Token 標頭），防止別的網站冒用你的登入狀態
//   3. 把後端的錯誤格式 { code, message, details } 轉成 ApiError，畫面可以直接顯示 message

export const API_BASE = '/api/v1'
const CSRF_COOKIE = 'shop_csrf'

/** 後端回傳的錯誤。code 給程式判斷，message 給人看。 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: Record<string, unknown> = {},
  ) {
    super(message)
  }
}

let csrfToken: string | null = null

function readCookie(name: string): string | null {
  const match = document.cookie.split('; ').find((c) => c.startsWith(`${name}=`))
  return match ? decodeURIComponent(match.slice(name.length + 1)) : null
}

/** 取得 CSRF token：優先讀 Cookie（登入後會換新），沒有就向後端要一個。 */
async function getCsrfToken(): Promise<string> {
  const fromCookie = readCookie(CSRF_COOKIE)
  if (fromCookie) return fromCookie
  if (!csrfToken) {
    const data = await request<{ csrf_token: string }>('GET', '/auth/csrf')
    csrfToken = readCookie(CSRF_COOKIE) ?? data.csrf_token
  }
  return csrfToken
}

type Query = Record<string, string | number | undefined | null>

interface RequestOptions {
  body?: unknown
  query?: Query
  headers?: Record<string, string>
}

/** 送出 API 請求並回傳 JSON。失敗時丟出 ApiError。 */
export async function request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
  const url = new URL(API_BASE + path, window.location.origin)
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value))
  }
  const headers: Record<string, string> = { Accept: 'application/json', ...options.headers }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET') headers['X-CSRF-Token'] = await getCsrfToken()

  let response: Response
  try {
    response = await fetch(url, {
      method,
      headers,
      credentials: 'include',
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', '連不上伺服器，請確認網路或後端是否已啟動')
  }

  if (response.status === 204) return undefined as T
  const data: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const err = (data ?? {}) as { code?: string; message?: string; details?: Record<string, unknown> }
    throw new ApiError(
      response.status,
      err.code ?? 'HTTP_ERROR',
      err.message ?? '請求失敗',
      err.details ?? {},
    )
  }
  return data as T
}

/** 產生冪等鍵（Idempotency-Key）：同一次「送出訂單」重送時要用同一個，後端就不會重複建立訂單。 */
export function newIdempotencyKey(): string {
  return crypto.randomUUID()
}

/** 測試用：清除記住的 CSRF token。 */
export function resetCsrfForTests(): void {
  csrfToken = null
}
