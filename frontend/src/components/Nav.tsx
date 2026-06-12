import { AnimatePresence, motion } from "framer-motion"
import { Mic, Menu, ShoppingBag, Sparkles, User, X } from "lucide-react"
import { useEffect, useState } from "react"
import { Link, NavLink, useLocation } from "react-router-dom"
import { cn } from "../lib/cn"
import { useAuth } from "../state/auth"
import { useCart } from "../state/cart"
import { useVoice } from "./VoiceAssistant"
import { Logo } from "./Logo"
import { Magnetic } from "./fx"

const LINKS = [
  { to: "/restaurants", label: "Eat", n: "01" },
  { to: "/travel", label: "Go", n: "02" },
  { to: "/shopping", label: "Buy", n: "03" },
  { to: "/assistant", label: "Ask", n: "04" },
]

export function Nav() {
  const [scrolled, setScrolled] = useState(false)
  const [mobile, setMobile] = useState(false)
  const { count, setOpen } = useCart()
  const { user, onboarded, profile, isDemoMode, logout } = useAuth()
  const voice = useVoice()
  const loc = useLocation()
  const displayName = profile?.name || user?.email?.split("@")[0] || "Account"
  const signedIn = !!user && onboarded
  const homeTo = signedIn ? "/dashboard" : "/"

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])
  useEffect(() => setMobile(false), [loc.pathname])

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-500",
        scrolled ? "border-b border-ink-line bg-paper/80 backdrop-blur-xl" : "border-b border-transparent",
      )}
    >
      <AnimatePresence>
        {isDemoMode && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden bg-saffron"
          >
            <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-1.5 sm:px-8">
              <div className="flex items-center gap-2">
                <motion.span
                  animate={{ scale: [1, 1.4, 1] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                  className="h-1.5 w-1.5 rounded-full bg-paper-card"
                />
                <span className="text-[0.65rem] font-semibold text-paper-card/90">
                  Demo mode · Browsing as Arjun Sharma
                </span>
              </div>
              <div className="flex items-center gap-4">
                <Link
                  to="/auth"
                  className="text-[0.65rem] font-semibold text-paper-card underline underline-offset-2 transition hover:text-paper-card/70"
                >
                  Sign up for real →
                </Link>
                <button
                  onClick={logout}
                  className="text-[0.65rem] font-semibold text-paper-card/70 transition hover:text-paper-card"
                  aria-label="Exit demo"
                >
                  Exit ×
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3.5 sm:px-8">
        <Link to={homeTo} aria-label={signedIn ? "Kensho dashboard" : "Kensho home"}>
          <Logo />
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                cn(
                  "group relative rounded-full px-4 py-2 text-[0.95rem] font-medium transition-colors",
                  isActive ? "text-ink" : "text-ink-soft hover:text-ink",
                )
              }
            >
              {({ isActive }) => (
                <span className="relative flex items-center gap-1.5">
                  <span className="font-mono text-[0.6rem] text-saffron opacity-70">{l.n}</span>
                  {l.label}
                  {isActive && (
                    <motion.span
                      layoutId="nav-dot"
                      className="absolute -bottom-1 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-saffron"
                    />
                  )}
                </span>
              )}
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => voice.open()}
            className="relative rounded-full border border-ink-line bg-paper-card/60 p-2.5 text-ink transition hover:border-saffron hover:text-saffron"
            aria-label="Talk to Kensho"
            title="Talk to Kensho"
          >
            <Mic className="h-[1.1rem] w-[1.1rem]" />
          </button>
          <button
            onClick={() => setOpen(true)}
            className="relative rounded-full border border-ink-line bg-paper-card/60 p-2.5 text-ink transition hover:border-ink/40"
            aria-label="Cart"
          >
            <ShoppingBag className="h-[1.1rem] w-[1.1rem]" />
            <AnimatePresence>
              {count > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="absolute -right-1 -top-1 flex h-[1.1rem] min-w-[1.1rem] items-center justify-center rounded-full bg-saffron px-1 font-mono text-[0.6rem] font-bold text-paper-card"
                >
                  {count}
                </motion.span>
              )}
            </AnimatePresence>
          </button>

          <Link
            to={signedIn ? "/profile" : "/auth"}
            className="hidden items-center gap-2 rounded-full border border-ink-line bg-paper-card/60 px-3.5 py-2 text-sm font-medium text-ink transition hover:border-ink/40 sm:inline-flex"
          >
            <User className="h-4 w-4" />
            {isDemoMode ? (
              <span className="flex items-center gap-1.5">
                {displayName}
                <span className="rounded-full bg-saffron px-1.5 py-0.5 text-[0.55rem] font-bold uppercase tracking-wide text-paper-card">
                  demo
                </span>
              </span>
            ) : (
              user ? displayName : "Sign in"
            )}
          </Link>

          <Magnetic className="hidden md:inline-block">
            <Link
              to="/assistant"
              className="inline-flex items-center gap-2 rounded-full bg-ink px-4 py-2.5 text-sm font-semibold text-paper-card transition-colors hover:bg-saffron"
            >
              <Sparkles className="h-4 w-4" />
              Ask Kensho
            </Link>
          </Magnetic>

          <button onClick={() => setMobile((m) => !m)} className="p-2 text-ink md:hidden" aria-label="Menu">
            {mobile ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </nav>

      <AnimatePresence>
        {mobile && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-ink-line bg-paper/95 backdrop-blur-xl md:hidden"
          >
            <div className="flex flex-col gap-1 px-5 py-4">
              {signedIn && (
                <NavLink to="/dashboard" className="flex items-center justify-between rounded-xl px-4 py-3 text-lg font-medium text-ink hover:bg-ink/5">
                  <span>Dashboard</span>
                  <span className="font-mono text-xs text-saffron">★</span>
                </NavLink>
              )}
              {LINKS.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  className="flex items-center justify-between rounded-xl px-4 py-3 text-lg font-medium text-ink hover:bg-ink/5"
                >
                  <span>{l.label}</span>
                  <span className="font-mono text-xs text-saffron">{l.n}</span>
                </NavLink>
              ))}
              <button
                onClick={() => voice.open()}
                className="flex items-center gap-2 rounded-xl px-4 py-3 text-left text-lg font-medium text-ink hover:bg-ink/5"
              >
                <Mic className="h-5 w-5 text-saffron" /> Talk to Kensho
              </button>
              <Link to={signedIn ? "/profile" : "/auth"} className="mt-2 rounded-xl bg-ink px-4 py-3 text-center font-medium text-paper-card">
                {signedIn ? `Profile · ${displayName}` : "Sign in / Register"}
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
