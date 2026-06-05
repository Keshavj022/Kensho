import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, Check, ChevronRight, MapPin, Sparkles, X } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { cn } from "../lib/cn"
import { useAuth } from "../state/auth"

const DEMO = {
  name: "Arjun Sharma",
  dob: "15 Mar 2001",
  age: 24,
  gender: "male",
  location: "Park Street, Kolkata",
  diet: { key: "non-vegetarian", emoji: "🍗", label: "Non-vegetarian" },
  spice: { key: "spicy", emoji: "🔥", label: "Spicy" },
  allergies: ["Peanuts"],
  goals: [
    { key: "high-protein", emoji: "💪", label: "High protein" },
    { key: "muscle-gain", emoji: "🏋️", label: "Muscle gain" },
  ],
  cuisines: ["Indian", "Japanese", "Italian", "Korean"],
  likes: ["Biryani", "Butter Chicken", "Sushi", "Pizza", "Ramen"],
}

const STEP_MS = 1800

function FakeInput({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="mb-1 text-[0.6rem] font-semibold uppercase tracking-[0.18em] text-ink-faint">{label}</p>
      <div className="flex items-center gap-1 rounded-xl border border-ink-line bg-paper-card/60 px-4 py-2.5">
        <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }} className="flex-1 text-sm text-ink">
          {value}
        </motion.span>
        <motion.span animate={{ opacity: [1, 0] }} transition={{ repeat: Infinity, duration: 0.85 }} className="h-4 w-px bg-saffron" />
      </div>
    </div>
  )
}

function Chip({ children, tone = "default", delay = 0 }: { children: React.ReactNode; tone?: "saffron" | "pine" | "default"; delay?: number }) {
  return (
    <motion.span
      initial={{ scale: 0.78, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay, type: "spring", stiffness: 260, damping: 20 }}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[0.7rem] font-semibold",
        tone === "saffron" && "border-saffron/30 bg-saffron-wash text-saffron-deep",
        tone === "pine" && "border-pine/30 bg-pine-wash text-pine",
        tone === "default" && "border-ink-line bg-paper text-ink-soft",
      )}
    >
      {children}
    </motion.span>
  )
}

function Tile({ emoji, label, selected, delay = 0 }: { emoji?: string; label: string; selected?: boolean; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.88 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, type: "spring", stiffness: 250, damping: 22 }}
      className={cn("flex flex-col items-center gap-1 rounded-xl border p-2.5 text-xs", selected ? "border-saffron bg-saffron-wash text-ink shadow-sm" : "border-ink-line bg-paper text-ink-soft")}
    >
      {emoji && <span className="text-lg leading-none">{emoji}</span>}
      <span className="text-center font-medium leading-tight">{label}</span>
      {selected && <Check className="h-3 w-3 text-saffron" />}
    </motion.div>
  )
}

function AccountFrame() {
  return (
    <div className="space-y-3">
      <FakeInput label="Email" value="arjun.sharma@demo.kensho" />
      <div>
        <p className="mb-1 text-[0.6rem] font-semibold uppercase tracking-[0.18em] text-ink-faint">Password</p>
        <div className="rounded-xl border border-ink-line bg-paper-card/60 px-4 py-2.5 font-mono text-sm tracking-widest text-ink-faint">••••••••••••</div>
      </div>
    </div>
  )
}

function AboutFrame() {
  return (
    <div className="space-y-3">
      <FakeInput label="Your name" value={DEMO.name} />
      <div className="flex items-end gap-3">
        <div className="flex-1"><FakeInput label="Date of birth" value={DEMO.dob} /></div>
        <Chip tone="saffron" delay={0.3}>{DEMO.age} yrs</Chip>
      </div>
      <div>
        <p className="mb-2 text-[0.6rem] font-semibold uppercase tracking-[0.18em] text-ink-faint">Gender</p>
        <div className="grid grid-cols-2 gap-2">
          {[{ key: "female", emoji: "♀", label: "Female" }, { key: "male", emoji: "♂", label: "Male" }, { key: "non-binary", emoji: "⚧", label: "Non-binary" }, { key: "undisclosed", emoji: "•", label: "Prefer not to say" }].map((g, i) => (
            <Tile key={g.key} emoji={g.emoji} label={g.label} selected={g.key === DEMO.gender} delay={i * 0.06} />
          ))}
        </div>
      </div>
    </div>
  )
}

function LocationFrame() {
  return (
    <div className="space-y-3">
      <motion.div
        initial={{ borderColor: "#DCD2BE" }} animate={{ borderColor: "#E0531F" }} transition={{ delay: 0.5, duration: 0.4 }}
        className="flex items-center gap-3 rounded-xl border-2 border-dashed bg-saffron-wash/40 p-4"
      >
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-saffron text-paper-card"><MapPin className="h-4 w-4" /></span>
        <div>
          <p className="text-sm font-semibold text-ink">Location detected</p>
          <p className="text-xs text-ink-faint">Reverse-geocoded from GPS coordinates</p>
        </div>
      </motion.div>
      <FakeInput label="City / area" value={DEMO.location} />
      <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }} className="inline-flex items-center gap-1.5 rounded-full bg-pine-wash px-3 py-1.5 text-xs font-semibold text-pine">
        <Check className="h-3 w-3" /> Pinned to exact coordinates
      </motion.div>
    </div>
  )
}

function DietFrame() {
  const diets = [
    { key: "vegetarian", emoji: "🥗", label: "Vegetarian" }, { key: "eggetarian", emoji: "🥚", label: "Eggetarian" },
    { key: "non-vegetarian", emoji: "🍗", label: "Non-veg" }, { key: "vegan", emoji: "🌱", label: "Vegan" },
    { key: "pescatarian", emoji: "🐟", label: "Pescatarian" }, { key: "halal", emoji: "☪", label: "Halal" },
  ]
  return (
    <div className="grid grid-cols-3 gap-2">
      {diets.map((d, i) => <Tile key={d.key} emoji={d.emoji} label={d.label} selected={d.key === DEMO.diet.key} delay={i * 0.06} />)}
    </div>
  )
}

function AllergiesFrame() {
  const all = ["Peanuts", "Tree nuts", "Milk", "Eggs", "Soy", "Wheat", "Fish", "Sesame"]
  return (
    <div className="flex flex-wrap gap-2">
      {all.map((a, i) => (
        <motion.span key={a} initial={{ opacity: 0, scale: 0.82 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}
          className={cn("rounded-full border px-3 py-1.5 text-xs font-semibold", a === "Peanuts" ? "border-saffron/40 bg-saffron-wash text-saffron-deep" : "border-ink-line text-ink-soft")}
        >
          {a === "Peanuts" ? "⚠ " : ""}{a}
        </motion.span>
      ))}
    </div>
  )
}

function GoalsFrame() {
  const goals = [
    { key: "high-protein", emoji: "💪", label: "High protein" }, { key: "heart-healthy", emoji: "❤️", label: "Heart healthy" },
    { key: "weight-loss", emoji: "⚖️", label: "Weight loss" }, { key: "muscle-gain", emoji: "🏋️", label: "Muscle gain" },
    { key: "low-carb", emoji: "🥑", label: "Low-carb / Keto" }, { key: "balanced", emoji: "🧘", label: "Balanced" },
  ]
  const sel = new Set(["high-protein", "muscle-gain"])
  return (
    <div className="flex flex-wrap gap-2">
      {goals.map((g, i) => (
        <motion.span key={g.key} initial={{ opacity: 0, scale: 0.82 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.07 }}
          className={cn("rounded-full border px-3 py-1.5 text-xs font-semibold", sel.has(g.key) ? "border-pine/40 bg-pine-wash text-pine" : "border-ink-line text-ink-soft")}
        >
          {g.emoji} {g.label}
        </motion.span>
      ))}
    </div>
  )
}

function TastesFrame() {
  const label = (t: string) => <p className="mb-1.5 text-[0.6rem] font-semibold uppercase tracking-[0.18em] text-ink-faint">{t}</p>
  return (
    <div className="space-y-3">
      <div>
        {label("Foods you love")}
        <div className="flex flex-wrap gap-1.5">{DEMO.likes.map((l, i) => <Chip key={l} tone="saffron" delay={i * 0.07}>{l}</Chip>)}</div>
      </div>
      <div>
        {label("Favourite cuisines")}
        <div className="flex flex-wrap gap-1.5">{DEMO.cuisines.map((c, i) => <Chip key={c} tone="pine" delay={0.35 + i * 0.07}>{c}</Chip>)}</div>
      </div>
      <div>
        {label("Spice tolerance")}
        <div className="flex gap-2">
          {[{ key: "mild", emoji: "🌤", label: "Mild" }, { key: "medium", emoji: "🌶", label: "Medium" }, { key: "spicy", emoji: "🔥", label: "Spicy" }, { key: "fiery", emoji: "🌋", label: "Fiery" }].map((s, i) => (
            <Tile key={s.key} emoji={s.emoji} label={s.label} selected={s.key === DEMO.spice.key} delay={0.6 + i * 0.06} />
          ))}
        </div>
      </div>
    </div>
  )
}

function TastePassport() {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15, type: "spring", stiffness: 220, damping: 26 }} className="overflow-hidden rounded-2xl bg-ink text-paper shadow-lift">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
        <span className="font-display text-sm font-medium tracking-wider">TASTE PASSPORT</span>
        <span className="font-mono text-[0.55rem] text-paper/40">見性 · KENSHO</span>
      </div>
      <div className="px-5 pt-4">
        <div className="font-display text-lg font-medium tracking-wide">{DEMO.name.toUpperCase()}</div>
        <div className="mt-0.5 font-mono text-[0.6rem] text-paper/50">{DEMO.age} · {DEMO.gender} · {DEMO.location}</div>
      </div>
      <div className="mx-5 mt-3 flex flex-wrap gap-1.5 border-t border-white/10 pt-3">
        {[DEMO.diet, DEMO.spice].map((d) => (
          <span key={d.key} className="rounded-full bg-saffron/20 px-2.5 py-1 text-[0.68rem] font-semibold text-saffron-glow">{d.emoji} {d.label}</span>
        ))}
        {DEMO.allergies.map((a) => <span key={a} className="rounded-full bg-white/10 px-2.5 py-1 text-[0.68rem] font-semibold text-paper/60">⚠ {a}</span>)}
      </div>
      <div className="mx-5 mt-3 flex flex-wrap gap-1.5 border-t border-white/10 pt-3">
        {DEMO.goals.map((g) => <span key={g.key} className="rounded-full bg-pine/30 px-2.5 py-1 text-[0.68rem] font-semibold text-pine-wash">{g.emoji} {g.label}</span>)}
      </div>
      <div className="mx-5 mt-3 border-t border-white/10 pt-3">
        <p className="mb-1.5 font-mono text-[0.52rem] uppercase tracking-widest text-paper/35">Cuisines</p>
        <div className="flex flex-wrap gap-1.5">
          {DEMO.cuisines.map((c) => <span key={c} className="rounded-full border border-white/10 px-2.5 py-1 text-[0.65rem] text-paper/60">{c}</span>)}
        </div>
      </div>
      <div className="mx-5 mb-5 mt-3 border-t border-white/10 pt-3">
        <p className="mb-1 font-mono text-[0.52rem] uppercase tracking-widest text-paper/35">Loves</p>
        <p className="font-mono text-[0.62rem] text-paper/50">{DEMO.likes.join(" · ")}</p>
      </div>
    </motion.div>
  )
}

interface StepDef { id: string; title: string; subtitle: string; Frame: () => React.ReactElement }

const STEPS: StepDef[] = [
  { id: "account", title: "Create your account", subtitle: "This unlocks Kensho and remembers your taste.", Frame: AccountFrame },
  { id: "about", title: "About you", subtitle: "A few basics to personalise your recommendations.", Frame: AboutFrame },
  { id: "location", title: "Where are you?", subtitle: "Kensho finds places near you and tailors suggestions.", Frame: LocationFrame },
  { id: "diet", title: "How do you eat?", subtitle: "Pick the one that fits you best.", Frame: DietFrame },
  { id: "allergies", title: "Any allergies?", subtitle: "Treated as strict constraints — never suggested.", Frame: AllergiesFrame },
  { id: "goals", title: "What are you working toward?", subtitle: "Optional — helps nudge healthier picks.", Frame: GoalsFrame },
  { id: "tastes", title: "What do you love?", subtitle: "Foods, cuisines, and how much heat you can take.", Frame: TastesFrame },
]

export function DemoModal({ onClose }: { onClose: () => void }) {
  const { startDemo } = useAuth()
  const nav = useNavigate()
  const [phase, setPhase] = useState<"steps" | "passport">("steps")
  const [idx, setIdx] = useState(0)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (phase !== "steps") return
    const t = setTimeout(() => {
      if (idx < STEPS.length - 1) setIdx((x) => x + 1)
      else setPhase("passport")
    }, STEP_MS)
    return () => clearTimeout(t)
  }, [idx, phase])

  function advance() {
    if (idx < STEPS.length - 1) setIdx((x) => x + 1)
    else setPhase("passport")
  }

  async function enter() {
    setLoading(true)
    try {
      await startDemo()
      onClose()
      nav("/assistant")
    } catch {
      onClose()
      nav("/auth")
    }
  }

  const step = STEPS[idx]
  const Frame = step.Frame
  const pct = phase === "passport" ? 100 : ((idx + 1) / STEPS.length) * 100

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center p-3 sm:items-center sm:p-0">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-ink/75 backdrop-blur-sm" onClick={onClose} />

      <motion.div
        initial={{ opacity: 0, y: 48, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 32, scale: 0.96 }}
        transition={{ type: "spring", stiffness: 300, damping: 28 }}
        className="relative z-10 w-full max-w-md overflow-hidden rounded-3xl border border-ink-line bg-paper shadow-lift"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-ink-line px-5 py-3.5">
          <div className="flex items-center gap-2">
            <motion.span animate={{ scale: [1, 1.5, 1] }} transition={{ repeat: Infinity, duration: 2 }} className="h-2 w-2 rounded-full bg-saffron" />
            <span className="text-[0.65rem] font-semibold uppercase tracking-widest text-saffron">Live demo · Arjun Sharma</span>
          </div>
          <button onClick={onClose} className="rounded-full p-1.5 text-ink-faint transition hover:text-ink" aria-label="Close"><X className="h-4 w-4" /></button>
        </div>

        {/* Overall progress */}
        <div className="h-0.5 bg-ink-line">
          <motion.div className="h-full bg-saffron" animate={{ width: `${pct}%` }} transition={{ ease: [0.16, 1, 0.3, 1] }} />
        </div>

        {/* Content */}
        <div className="p-5">
          <AnimatePresence mode="wait">
            {phase === "steps" ? (
              <motion.div
                key={`step-${idx}`}
                initial={{ x: 28, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -28, opacity: 0 }}
                transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
              >
                <div className="mb-4">
                  <div className="mb-0.5 flex items-center justify-between">
                    <span className="text-[0.6rem] font-semibold uppercase tracking-widest text-ink-faint">Step {idx + 1} / {STEPS.length}</span>
                    <span className="font-mono text-[0.58rem] text-ink-faint">{Math.round(pct)}%</span>
                  </div>
                  <h3 className="font-display text-lg leading-snug">{step.title}</h3>
                  <p className="mt-0.5 text-[0.78rem] text-ink-soft">{step.subtitle}</p>
                </div>

                <div className="mb-4 max-h-56 overflow-auto"><Frame /></div>

                <div className="mb-4 h-px overflow-hidden rounded-full bg-ink-line">
                  <motion.div key={`bar-${idx}`} className="h-full origin-left bg-saffron" initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ duration: STEP_MS / 1000, ease: "linear" }} />
                </div>

                <div className="flex items-center justify-between">
                  <button onClick={() => setPhase("passport")} className="text-[0.72rem] text-ink-soft transition hover:text-ink">Skip to result</button>
                  <button onClick={advance} className="flex items-center gap-1.5 rounded-full bg-ink px-4 py-2 text-[0.72rem] font-semibold text-paper-card transition hover:bg-saffron">
                    {idx < STEPS.length - 1 ? <><span>Next</span> <ChevronRight className="h-3 w-3" /></> : <><span>See profile</span> <Sparkles className="h-3 w-3" /></>}
                  </button>
                </div>
              </motion.div>
            ) : (
              <motion.div key="passport" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
                <motion.div initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} className="mb-4 flex items-center gap-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-pine text-paper-card"><Check className="h-3 w-3" /></span>
                  <span className="text-sm font-semibold text-pine">Profile ready</span>
                </motion.div>

                <TastePassport />

                <motion.button
                  whileTap={{ scale: 0.98 }} onClick={enter} disabled={loading}
                  className="mt-5 flex w-full items-center justify-center gap-2 rounded-full bg-saffron py-3.5 text-sm font-semibold text-paper-card transition hover:bg-saffron-deep disabled:opacity-60"
                >
                  {loading ? "Setting up…" : <><span>Enter Kensho as Arjun</span> <ArrowRight className="h-4 w-4" /></>}
                </motion.button>

                <p className="mt-3 text-center text-xs text-ink-soft">
                  Want your own profile?{" "}
                  <button onClick={onClose} className="font-semibold text-ink transition hover:text-saffron">Sign up →</button>
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="border-t border-ink-line px-5 py-2 text-center">
          <span className="text-[0.6rem] text-ink-faint">Demo account · no real data stored</span>
        </div>
      </motion.div>
    </div>
  )
}
