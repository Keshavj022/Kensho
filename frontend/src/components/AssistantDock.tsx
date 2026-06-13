import { AnimatePresence, motion } from "framer-motion"
import { MessageSquare, X } from "lucide-react"
import { useState } from "react"
import { useLocation } from "react-router-dom"
import { useAuth } from "../state/auth"
import { Chat } from "./Chat"

export function AssistantDock() {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  const { user, onboarded } = useAuth()
  if (!user || !onboarded || loc.pathname.startsWith("/assistant")) return null

  return (
    <>
      <motion.button
        onClick={() => setOpen((o) => !o)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="fixed bottom-5 right-5 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-ink text-paper-card shadow-lift"
        aria-label="Open assistant"
      >
        <AnimatePresence mode="wait">
          {open ? (
            <motion.span key="x" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }}>
              <X className="h-6 w-6" />
            </motion.span>
          ) : (
            <motion.span key="m" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }}>
              <MessageSquare className="h-6 w-6" />
            </motion.span>
          )}
        </AnimatePresence>
        {!open && <span className="absolute right-0 top-0 h-3 w-3 animate-ping rounded-full bg-saffron" />}
        {!open && <span className="absolute right-0 top-0 h-3 w-3 rounded-full bg-saffron" />}
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.96 }}
            transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
            className="fixed bottom-24 right-5 z-50 w-[min(92vw,26rem)] rounded-3xl border border-ink-line bg-paper p-4 shadow-lift"
          >
            <div className="mb-2 flex items-center justify-between px-1">
              <span className="label">Kensho · assistant</span>
              <span className="font-mono text-[0.6rem] text-ink-faint">supervisor → specialist</span>
            </div>
            <Chat variant="dock" />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
