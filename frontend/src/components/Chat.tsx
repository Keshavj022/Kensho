import { AnimatePresence, motion } from "framer-motion"
import { ArrowUp, RefreshCw } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { api } from "../lib/api"
import { cn } from "../lib/cn"
import { getThreadId, newThread } from "../lib/session"
import { useAuth } from "../state/auth"
import { Mark } from "./Logo"

interface Msg {
  id: string
  role: "user" | "assistant"
  content: string
}

const SUGGESTIONS = [
  "Best biryani in Kolkata",
  "Cheapest flight CCU → DEL next month",
  "Plan 3 relaxed days in Goa",
  "Noise-cancelling headphones under ₹10k",
]

const GREETING: Msg = {
  id: "greet",
  role: "assistant",
  content:
    "I'm Kensho. Tell me what you're in the mood for — a place to eat, a trip to take, or something to buy — and I'll route it to the right specialist.",
}

export function Chat({ variant = "page", initial }: { variant?: "page" | "dock"; initial?: string }) {
  const [messages, setMessages] = useState<Msg[]>([GREETING])
  const [input, setInput] = useState("")
  const [busy, setBusy] = useState(false)
  const [thread, setThread] = useState(getThreadId())
  const scroller = useRef<HTMLDivElement>(null)
  const sentInitial = useRef(false)
  const { user } = useAuth()

  useEffect(() => {
    if (initial && initial.trim() && !sentInitial.current) {
      sentInitial.current = true
      send(initial)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initial])

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" })
  }, [messages, busy])

  async function send(text: string) {
    const q = text.trim()
    if (!q || busy) return
    setInput("")
    const userMsg: Msg = { id: "u" + Date.now(), role: "user", content: q }
    setMessages((m) => [...m, userMsg])
    setBusy(true)
    try {
      const res = await api.chat(q, thread, user?.user_id)
      setMessages((m) => [...m, { id: "a" + Date.now(), role: "assistant", content: res.message || "…" }])
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { id: "e" + Date.now(), role: "assistant", content: "The assistant is unreachable right now — is the backend running on :8000?" },
      ])
    } finally {
      setBusy(false)
    }
  }

  function reset() {
    setThread(newThread())
    setMessages([GREETING])
  }

  return (
    <div className={cn("flex flex-col", variant === "page" ? "h-[min(72vh,640px)]" : "h-[28rem]")}>
      <div ref={scroller} className="flex-1 space-y-5 overflow-y-auto px-1 py-2">
        <AnimatePresence initial={false}>
          {messages.map((m) => (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
              className={cn("flex gap-3", m.role === "user" ? "flex-row-reverse" : "flex-row")}
            >
              {m.role === "assistant" && (
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink">
                  <Mark className="h-5 w-5 text-paper" animate={false} />
                </div>
              )}
              <div
                className={cn(
                  "max-w-[82%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-[0.95rem] leading-relaxed",
                  m.role === "user"
                    ? "rounded-tr-sm bg-ink text-paper-card"
                    : "rounded-tl-sm border border-ink-line bg-paper-card text-ink",
                )}
              >
                {m.content}
              </div>
            </motion.div>
          ))}
          {busy && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink">
                <Mark className="h-5 w-5 text-paper" animate={false} />
              </div>
              <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm border border-ink-line bg-paper-card px-4 py-4">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="h-1.5 w-1.5 rounded-full bg-saffron"
                    animate={{ opacity: [0.2, 1, 0.2], y: [0, -3, 0] }}
                    transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15 }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {messages.length <= 1 && (
        <div className="mb-2 flex flex-wrap gap-2 px-1">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="rounded-full border border-ink-line bg-paper-card/70 px-3 py-1.5 text-xs text-ink-soft transition hover:border-saffron hover:text-ink"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
        className="flex items-end gap-2 rounded-2xl border border-ink-line bg-paper-card p-2"
      >
        <button type="button" onClick={reset} className="rounded-xl p-2.5 text-ink-faint transition hover:text-ink" title="New conversation">
          <RefreshCw className="h-4 w-4" />
        </button>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()
              send(input)
            }
          }}
          rows={1}
          placeholder="Ask Kensho anything…"
          className="max-h-32 flex-1 resize-none bg-transparent py-2.5 text-ink outline-none placeholder:text-ink-faint"
        />
        <motion.button
          whileTap={{ scale: 0.9 }}
          type="submit"
          disabled={busy || !input.trim()}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-ink text-paper-card transition-colors hover:bg-saffron disabled:opacity-40"
        >
          <ArrowUp className="h-5 w-5" />
        </motion.button>
      </form>
    </div>
  )
}
