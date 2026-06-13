import { motion } from "framer-motion"
import type { ReactNode } from "react"
import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../state/auth"
import { Mark } from "./Logo"

function Splash() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 2.4, repeat: Infinity, ease: "linear" }}>
        <Mark className="h-12 w-12 text-ink" animate={false} />
      </motion.div>
      <span className="label">finding your seat…</span>
    </div>
  )
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, onboarded, ready } = useAuth()
  const loc = useLocation()

  if (!ready) return <Splash />
  if (!user) return <Navigate to="/auth" state={{ from: loc.pathname }} replace />
  if (!onboarded) return <Navigate to="/auth" state={{ from: loc.pathname, onboard: true }} replace />
  return <>{children}</>
}
