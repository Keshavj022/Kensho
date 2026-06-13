import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react"
import { api } from "../lib/api"
import { getThreadId, newThread } from "../lib/session"
import type { ChatReference } from "../lib/types"
import { useAuth } from "./auth"

export interface ChatMsg {
  id: string
  role: "user" | "assistant"
  content: string
  references?: ChatReference[]
}

export const CHAT_GREETING: ChatMsg = {
  id: "greet",
  role: "assistant",
  content:
    "I'm Kensho. Tell me what you're in the mood for — a place to eat, a trip to take, or something to buy — and I'll route it to the right specialist.",
}

const KEY = "kensho.chat"

interface ChatCtx {
  messages: ChatMsg[]
  busy: boolean
  thread: string
  send: (text: string) => Promise<void>
  reset: () => void
}
const Ctx = createContext<ChatCtx>(null as unknown as ChatCtx)
export const useChat = () => useContext(Ctx)

interface Persisted {
  thread: string
  messages: ChatMsg[]
}

function load(): Persisted {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) || "null")
    if (raw && typeof raw.thread === "string" && Array.isArray(raw.messages) && raw.messages.length) {
      return { thread: raw.thread, messages: raw.messages as ChatMsg[] }
    }
  } catch {}
  return { thread: getThreadId(), messages: [CHAT_GREETING] }
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [state, setState] = useState<Persisted>(load)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(state))
  }, [state])

  const send = useCallback(
    async (text: string) => {
      const q = text.trim()
      if (!q || busy) return
      const userMsg: ChatMsg = { id: "u" + Date.now(), role: "user", content: q }
      setState((s) => ({ ...s, messages: [...s.messages, userMsg] }))
      setBusy(true)
      try {
        const res = await api.chat(q, state.thread, user?.user_id)
        setState((s) => ({
          ...s,
          messages: [
            ...s.messages,
            { id: "a" + Date.now(), role: "assistant", content: res.message || "…", references: res.references ?? undefined },
          ],
        }))
      } catch {
        setState((s) => ({
          ...s,
          messages: [
            ...s.messages,
            { id: "e" + Date.now(), role: "assistant", content: "The assistant is unreachable right now — is the backend running on :8000?" },
          ],
        }))
      } finally {
        setBusy(false)
      }
    },
    [busy, state.thread, user?.user_id],
  )

  const reset = useCallback(() => {
    setState({ thread: newThread(), messages: [CHAT_GREETING] })
  }, [])

  return <Ctx.Provider value={{ messages: state.messages, busy, thread: state.thread, send, reset }}>{children}</Ctx.Provider>
}
