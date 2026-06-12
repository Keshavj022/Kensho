import { ArrowLeft } from "lucide-react"
import { FormEvent, useEffect, useRef, useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { Mark } from "../components/Logo"
import { Onboarding } from "../components/Onboarding"
import { Button, Field, Input } from "../components/ui"
import { Reveal } from "../components/fx"
import { useAuth } from "../state/auth"

export function Auth() {
  const { user, onboarded, login, logout } = useAuth()
  const loc = useLocation()
  const nav = useNavigate()
  const st = loc.state as { from?: string; onboard?: boolean } | null
  const from = st?.from || "/restaurants"
  const [mode, setMode] = useState<"login" | "signup">("login")

  const mustComplete = !!user && !onboarded // legacy account finishing onboarding
  const showWizard = mustComplete || mode === "signup"
  // Freeze the wizard's mode for its whole lifetime. If the user explicitly chose
  // signup, it stays "signup" even after register() sets `user` mid-completion —
  // otherwise the steps array would shrink under the current index and the user
  // would be bounced back to re-enter their basics. Once the wizard has been shown,
  // navigation is owned solely by its onDone (so the success screen isn't cut off).
  const wizardMode: "signup" | "complete" = mode === "signup" ? "signup" : "complete"
  const showedWizard = useRef(false)
  if (showWizard) showedWizard.current = true

  useEffect(() => {
    if (user && onboarded && !showedWizard.current) nav(from, { replace: true })
  }, [user, onboarded, from, nav])

  if (user && onboarded && !showedWizard.current) return null // redirecting

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute -right-20 top-10 hidden lg:block">
        <Mark className="h-[28rem] w-[28rem] text-ink/[0.04]" animate={false} />
      </div>

      {/* top bar */}
      <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-5 sm:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <Mark className="h-8 w-8 text-ink" animate={false} />
          <span className="font-display text-2xl font-semibold">Kensho</span>
        </Link>
        {mustComplete ? (
          <button onClick={logout} className="text-sm text-ink-soft link-grow hover:text-ink">
            Sign out
          </button>
        ) : (
          <button onClick={() => setMode(mode === "login" ? "signup" : "login")} className="text-sm text-ink-soft link-grow hover:text-ink">
            {mode === "login" ? "New here? Create account" : "Have an account? Sign in"}
          </button>
        )}
      </div>

      <main className="mx-auto flex max-w-5xl items-start justify-center px-5 pb-24 pt-6 sm:px-8 sm:pt-12">
        {showWizard ? (
          <Reveal className="w-full">
            {mustComplete && (
              <p className="mx-auto mb-6 max-w-xl text-pretty text-ink-soft">
                Welcome back, {user?.username}. Let's finish your taste profile so recommendations feel made for you.
              </p>
            )}
            <Onboarding mode={wizardMode} onDone={() => nav(from, { replace: true })} />
          </Reveal>
        ) : (
          <LoginCard onSubmit={login} onSignup={() => setMode("signup")} />
        )}
      </main>
    </div>
  )
}

function LoginCard({ onSubmit, onSignup }: { onSubmit: (u: string, p: string) => Promise<void>; onSignup: () => void }) {
  const [u, setU] = useState("")
  const [p, setP] = useState("")
  const [err, setErr] = useState<string>()
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setErr(undefined)
    setBusy(true)
    try {
      await onSubmit(u, p)
    } catch (e: any) {
      setErr(e?.message || "Couldn't sign you in.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <Reveal className="mx-auto mt-8 w-full max-w-sm">
      <Link to="/" className="mb-6 inline-flex items-center gap-1.5 text-sm text-ink-faint link-grow hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> Back home
      </Link>
      <h1 className="font-display text-4xl">Welcome back.</h1>
      <p className="mt-2 text-ink-soft">Sign in to pick up where you left off.</p>
      <form onSubmit={submit} className="mt-8 space-y-4">
        <Field label="Email">
          <Input type="email" value={u} onChange={(e) => setU(e.target.value)} autoComplete="email" placeholder="you@example.com" required />
        </Field>
        <Field label="Password">
          <Input type="password" value={p} onChange={(e) => setP(e.target.value)} autoComplete="current-password" required />
        </Field>
        {err && <p className="text-sm text-saffron-deep">{err}</p>}
        <Button type="submit" loading={busy} variant="spice" className="w-full py-3">
          Sign in
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-ink-soft">
        New to Kensho?{" "}
        <button onClick={onSignup} className="font-semibold text-saffron link-grow">
          Create your taste profile
        </button>
      </p>
    </Reveal>
  )
}
