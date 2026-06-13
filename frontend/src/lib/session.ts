
const rid = (p: string) => p + "_" + Math.random().toString(36).slice(2, 12)

function persisted(key: string, prefix: string): string {
  let v = localStorage.getItem(key)
  if (!v) {
    v = rid(prefix)
    localStorage.setItem(key, v)
  }
  return v
}

export const getThreadId = () => persisted("kensho.thread", "thread")
export const newThread = () => {
  const t = rid("thread")
  localStorage.setItem("kensho.thread", t)
  return t
}
export const getSessionId = () => persisted("kensho.session", "session")

const TOKEN = "kensho.token"
const USER = "kensho.user"
export const getToken = () => localStorage.getItem(TOKEN)
export const setToken = (t: string | null) =>
  t ? localStorage.setItem(TOKEN, t) : localStorage.removeItem(TOKEN)
export const getStoredUser = () => {
  const u = localStorage.getItem(USER)
  return u ? JSON.parse(u) : null
}
export const setStoredUser = (u: unknown | null) =>
  u ? localStorage.setItem(USER, JSON.stringify(u)) : localStorage.removeItem(USER)
