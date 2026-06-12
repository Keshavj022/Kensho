import { AnimatePresence, motion } from "framer-motion"
import { Loader2, Mic, Send, Volume2, VolumeX, X } from "lucide-react"
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react"
import { api } from "../lib/api"
import { cn } from "../lib/cn"
import { getThreadId } from "../lib/session"
import { useAuth } from "../state/auth"

type Status = "idle" | "listening" | "thinking" | "speaking"
interface Turn {
  id: string
  role: "user" | "assistant"
  content: string
}

interface VoiceCtx {
  open: () => void
  close: () => void
  isOpen: boolean
}
const Ctx = createContext<VoiceCtx>(null as unknown as VoiceCtx)
export const useVoice = () => useContext(Ctx)

export function VoiceProvider({ children }: { children: ReactNode }) {
  const [isOpen, setOpen] = useState(false)
  const open = useCallback(() => setOpen(true), [])
  const close = useCallback(() => setOpen(false), [])
  return (
    <Ctx.Provider value={{ open, close, isOpen }}>
      {children}
      <AnimatePresence>{isOpen && <VoiceOverlay onClose={close} />}</AnimatePresence>
    </Ctx.Provider>
  )
}

/** Full-screen, conversational voice experience: speak → transcribe → route through
 *  the supervisor → speak the reply back, with a living orb that reacts to state. */
function VoiceOverlay({ onClose }: { onClose: () => void }) {
  const { user } = useAuth()
  const [status, setStatus] = useState<Status>("idle")
  const [turns, setTurns] = useState<Turn[]>([])
  const [text, setText] = useState("")
  const [muted, setMuted] = useState(false)
  const [err, setErr] = useState<string>()
  const [sttOff, setSttOff] = useState(false)

  const mr = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const thread = useRef(getThreadId())
  const mutedRef = useRef(muted)
  mutedRef.current = muted

  useEffect(() => {
    return () => {
      mr.current?.stream?.getTracks().forEach((t) => t.stop())
      audioRef.current?.pause()
    }
  }, [])

  const speak = useCallback(async (text: string) => {
    if (mutedRef.current) return
    setStatus("speaking")
    const blob = await api.tts(text)
    if (!blob) {
      setStatus("idle")
      return
    }
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audioRef.current = audio
    audio.onended = () => {
      setStatus("idle")
      URL.revokeObjectURL(url)
    }
    audio.onerror = () => setStatus("idle")
    audio.play().catch(() => setStatus("idle"))
  }, [])

  const ask = useCallback(
    async (q: string) => {
      const query = q.trim()
      if (!query) return
      setErr(undefined)
      setTurns((t) => [...t, { id: "u" + Date.now(), role: "user", content: query }])
      setStatus("thinking")
      try {
        const res = await api.chat(query, thread.current, user?.user_id)
        const reply = res.message || "…"
        setTurns((t) => [...t, { id: "a" + Date.now(), role: "assistant", content: reply }])
        speak(reply)
      } catch {
        setErr("Kensho is unreachable — is the backend running?")
        setStatus("idle")
      }
    },
    [speak, user?.user_id],
  )

  async function startListening() {
    setErr(undefined)
    audioRef.current?.pause()
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const rec = new MediaRecorder(stream)
      chunks.current = []
      rec.ondataavailable = (e) => e.data.size && chunks.current.push(e.data)
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        setStatus("thinking")
        const blob = new Blob(chunks.current, { type: "audio/webm" })
        const form = new FormData()
        form.append("file", blob, "speech.webm")
        try {
          const r = await api.stt(form)
          if (r.status === "ok" && r.text.trim()) {
            ask(r.text)
          } else if (r.status === "not_configured") {
            setSttOff(true)
            setErr("Voice input needs ElevenLabs configured — type to chat for now.")
            setStatus("idle")
          } else {
            setErr("I didn't catch that — try again.")
            setStatus("idle")
          }
        } catch {
          setErr("Transcription failed — try typing instead.")
          setStatus("idle")
        }
      }
      rec.start()
      mr.current = rec
      setStatus("listening")
    } catch {
      setErr("Microphone access was blocked — type your message instead.")
      setSttOff(true)
    }
  }
  function stopListening() {
    mr.current?.stop()
  }

  const onOrb = () => {
    if (status === "listening") stopListening()
    else if (status === "idle") startListening()
    else if (status === "speaking") {
      audioRef.current?.pause()
      setStatus("idle")
    }
  }

  const label: Record<Status, string> = {
    idle: sttOff ? "Type below to chat" : "Tap to speak",
    listening: "Listening…",
    thinking: "Thinking…",
    speaking: "Speaking…",
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[80] flex flex-col bg-ink/95 text-paper-card backdrop-blur-xl"
    >
      <div className="flex items-center justify-between px-5 py-5 sm:px-8">
        <div className="flex items-center gap-2">
          <span className="label !text-paper/50">Kensho · voice</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMuted((m) => !m)}
            className="rounded-full border border-white/15 p-2.5 text-paper-card/80 transition hover:border-white/40"
            aria-label={muted ? "Unmute replies" : "Mute replies"}
          >
            {muted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
          </button>
          <button onClick={onClose} className="rounded-full border border-white/15 p-2.5 text-paper-card/80 transition hover:border-white/40" aria-label="Close voice">
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* transcript */}
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-end gap-3 overflow-y-auto px-5 pb-4 sm:px-8">
        <AnimatePresence initial={false}>
          {turns.slice(-6).map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn("max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-[0.95rem] leading-relaxed", t.role === "user" ? "self-end rounded-tr-sm bg-saffron text-paper-card" : "self-start rounded-tl-sm bg-white/10")}
            >
              {t.content}
            </motion.div>
          ))}
        </AnimatePresence>
        {err && <p className="self-center text-sm text-saffron-glow">{err}</p>}
      </div>

      {/* orb */}
      <div className="flex flex-col items-center gap-5 py-8">
        <button onClick={onOrb} className="relative flex h-40 w-40 items-center justify-center" aria-label={label[status]}>
          <Orb status={status} />
          <span className="relative z-10 flex h-20 w-20 items-center justify-center rounded-full bg-paper-card text-ink shadow-lift">
            {status === "thinking" ? <Loader2 className="h-7 w-7 animate-spin" /> : <Mic className="h-7 w-7" />}
          </span>
        </button>
        <p className="font-display text-xl">{label[status]}</p>

        {/* text fallback — always available */}
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (text.trim()) {
              ask(text)
              setText("")
            }
          }}
          className="flex w-[min(92vw,32rem)] items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4"
        >
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="…or type to Kensho"
            className="flex-1 bg-transparent py-3 text-paper-card outline-none placeholder:text-paper-card/40"
          />
          <button type="submit" disabled={!text.trim() || status === "thinking"} className="text-paper-card/70 transition hover:text-paper-card disabled:opacity-40">
            <Send className="h-5 w-5" />
          </button>
        </form>
      </div>
    </motion.div>
  )
}

function Orb({ status }: { status: Status }) {
  const active = status === "listening" || status === "speaking"
  return (
    <span className="pointer-events-none absolute inset-0">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className={cn("absolute inset-0 rounded-full", status === "speaking" ? "bg-saffron/30" : "bg-saffron/25", "border border-saffron/40")}
          animate={
            active
              ? { scale: [1, 1.35 + i * 0.12, 1], opacity: [0.5, 0, 0.5] }
              : status === "thinking"
                ? { scale: [1, 1.1, 1], opacity: [0.3, 0.5, 0.3] }
                : { scale: 1, opacity: 0.2 }
          }
          transition={{ duration: active ? 1.6 : 2.4, repeat: Infinity, delay: i * 0.25, ease: "easeInOut" }}
        />
      ))}
      <motion.span
        className="absolute inset-3 rounded-full bg-gradient-to-br from-saffron to-saffron-deep"
        animate={active ? { scale: [1, 1.06, 1] } : { scale: 1 }}
        transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
      />
    </span>
  )
}
