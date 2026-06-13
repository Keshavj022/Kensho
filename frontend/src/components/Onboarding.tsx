import { AnimatePresence, motion } from "framer-motion"
import { Cake, Check, ChevronLeft, ChevronRight, Flame, Heart, Loader2, LocateFixed, MapPin, Plus, ShieldAlert, Sparkles, Target, Utensils, X } from "lucide-react"
import { useMemo, useState, type ReactNode } from "react"
import { detectLocation } from "../lib/geo"
import {
  ALLERGENS,
  ALL_FOOD_NAMES,
  CUISINES,
  DIET_TYPES,
  foodsForDiet,
  GENDERS,
  GOALS,
  Opt,
  SPICE,
} from "../lib/onboardingData"
import { api } from "../lib/api"
import { cn } from "../lib/cn"
import type { ProfilePayload } from "../lib/types"
import { useAuth } from "../state/auth"
import { Input } from "./ui"

type Mode = "signup" | "complete"
interface Data extends ProfilePayload {
  email: string
  password: string
  allergies: string[]
  goals: string[]
  likes: string[]
  cuisines: string[]
}

const STEP_META: Record<string, { title: string; subtitle: string }> = {
  account: { title: "Create your account", subtitle: "This unlocks Kensho and remembers your taste." },
  about: { title: "About you", subtitle: "A few basics to personalise your recommendations." },
  location: { title: "Where are you?", subtitle: "So Kensho can find places near you and tailor suggestions." },
  diet: { title: "How do you eat?", subtitle: "Pick the one that fits you best." },
  allergies: { title: "Any allergies?", subtitle: "We treat these as strict — Kensho will never suggest them." },
  goals: { title: "What are you working toward?", subtitle: "Optional — helps us nudge healthier picks." },
  tastes: { title: "What do you love?", subtitle: "Foods, cuisines, and how much heat you can take." },
  review: { title: "Looks good?", subtitle: "You can change any of this later in your profile." },
}

export function Onboarding({ mode, onDone }: { mode: Mode; onDone: () => void }) {
  const { register, saveProfile, profile } = useAuth()
  const steps = mode === "signup"
    ? ["account", "about", "location", "diet", "allergies", "goals", "tastes", "review"]
    : ["about", "location", "diet", "allergies", "goals", "tastes", "review"]

  const [i, setI] = useState(0)
  const [dir, setDir] = useState(1)
  const [busy, setBusy] = useState(false)
  const [checking, setChecking] = useState(false)
  const [emailErr, setEmailErr] = useState<string>()
  const [err, setErr] = useState<string>()
  const [done, setDone] = useState(false)

  const [d, setD] = useState<Data>({
    email: "",
    password: "",
    name: profile?.name ?? "",
    dob: profile?.dob ?? "",
    gender: profile?.gender ?? "",
    location: profile?.location ?? "",
    lat: profile?.lat ?? null,
    lng: profile?.lng ?? null,
    dietary_type: profile?.dietary_type ?? "",
    spice_tolerance: profile?.spice_tolerance ?? "",
    allergies: profile?.allergies ?? [],
    goals: profile?.goals ?? [],
    likes: profile?.likes ?? [],
    cuisines: profile?.cuisines ?? [],
  })
  const set = (patch: Partial<Data>) => setD((s) => ({ ...s, ...patch }))
  const step = steps[i]

  const age = useMemo(() => {
    if (!d.dob) return null
    const b = new Date(d.dob)
    if (isNaN(+b)) return null
    const t = new Date()
    let a = t.getFullYear() - b.getFullYear()
    if (t.getMonth() < b.getMonth() || (t.getMonth() === b.getMonth() && t.getDate() < b.getDate())) a--
    return a >= 0 && a < 120 ? a : null
  }, [d.dob])

  const valid = (s: string): boolean => {
    if (s === "account") return /^\S+@\S+\.\S+$/.test(d.email) && (d.password?.length ?? 0) >= 8
    if (s === "about") return (d.name ?? "").trim().length >= 1
    if (s === "diet") return !!d.dietary_type
    return true // allergies / goals / tastes / review are optional
  }

  function go(n: number) {
    setErr(undefined)
    setDir(n)
    setI((x) => Math.min(steps.length - 1, Math.max(0, x + n)))
  }

  async function next() {
    if (!valid(step)) return
    if (step === "account") {
      setChecking(true)
      setEmailErr(undefined)
      try {
        const r = await api.checkEmail(d.email)
        if (!r.available) {
          setEmailErr("That email is already registered — sign in instead.")
          return
        }
      } catch {} finally {
        setChecking(false)
      }
    }
    go(1)
  }

  async function finish() {
    setBusy(true)
    setErr(undefined)
    try {
      const payload: ProfilePayload = {
        name: d.name,
        dob: d.dob || null,
        gender: d.gender || null,
        age,
        location: d.location || "",
        lat: d.lat ?? null,
        lng: d.lng ?? null,
        dietary_type: d.dietary_type || "non-vegetarian",
        spice_tolerance: d.spice_tolerance || null,
        allergies: d.allergies,
        goals: d.goals,
        likes: d.likes,
        cuisines: d.cuisines,
      }
      if (mode === "signup") await register(d.email, d.password)
      await saveProfile(payload)
      setDone(true)
      setTimeout(onDone, 1100)
    } catch (e: any) {
      setErr(e?.message || "Something went wrong — please try again.")
    } finally {
      setBusy(false)
    }
  }

  if (done) return <Success name={d.name} />

  const pct = ((i + 1) / steps.length) * 100
  const last = i === steps.length - 1

  return (
    <div className="mx-auto flex min-h-[34rem] w-full max-w-xl flex-col">
      {/* progress */}
      <div className="mb-8">
        <div className="mb-2 flex items-center justify-between">
          <span className="label">
            Step {i + 1} / {steps.length}
          </span>
          <span className="font-mono text-xs text-ink-faint">{Math.round(pct)}%</span>
        </div>
        <div className="h-1 overflow-hidden rounded-full bg-ink-line">
          <motion.div className="h-full rounded-full bg-saffron" animate={{ width: `${pct}%` }} transition={{ ease: [0.16, 1, 0.3, 1] }} />
        </div>
      </div>

      <div className="mb-6">
        <h2 className="font-display text-3xl leading-tight sm:text-4xl">{STEP_META[step].title}</h2>
        <p className="mt-2 text-ink-soft text-pretty">{STEP_META[step].subtitle}</p>
      </div>

      <div className="flex-1">
        <AnimatePresence mode="wait" custom={dir}>
          <motion.div
            key={step}
            custom={dir}
            variants={{
              enter: (k: number) => ({ x: k > 0 ? 64 : -64, opacity: 0 }),
              center: { x: 0, opacity: 1 },
              exit: (k: number) => ({ x: k > 0 ? -64 : 64, opacity: 0 }),
            }}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.36, ease: [0.16, 1, 0.3, 1] }}
          >
            {step === "account" && <AccountStep d={d} set={set} emailErr={emailErr} clearErr={() => setEmailErr(undefined)} checking={checking} />}
            {step === "about" && <AboutStep d={d} set={set} age={age} />}
            {step === "location" && <LocationStep d={d} set={set} />}
            {step === "diet" && (
              <PickOne
                options={DIET_TYPES}
                value={d.dietary_type}
                onPick={(k) => {
                  const allowed = foodsForDiet(k)
                  set({ dietary_type: k, likes: d.likes.filter((l) => allowed.includes(l) || !ALL_FOOD_NAMES.includes(l)) })
                }}
              />
            )}
            {step === "allergies" && (
              <MultiPick options={ALLERGENS} values={d.allergies} onChange={(v) => set({ allergies: v })} tone="saffron" allowCustom placeholder="Add another allergy…" noneLabel="No allergies" />
            )}
            {step === "goals" && <MultiPick options={GOALS} values={d.goals} onChange={(v) => set({ goals: v })} tone="pine" />}
            {step === "tastes" && <TastesStep d={d} set={set} />}
            {step === "review" && <Review d={d} age={age} mode={mode} />}
          </motion.div>
        </AnimatePresence>
      </div>

      {err && <p className="mt-4 text-sm text-saffron-deep">{err}</p>}

      <div className="mt-8 flex items-center justify-between">
        <button
          onClick={() => go(-1)}
          disabled={i === 0}
          className="inline-flex items-center gap-1 rounded-full px-4 py-2.5 text-sm font-medium text-ink-soft transition hover:text-ink disabled:opacity-0"
        >
          <ChevronLeft className="h-4 w-4" /> Back
        </button>

        {!last ? (
          <button
            onClick={next}
            disabled={!valid(step) || checking}
            className="inline-flex items-center gap-1.5 rounded-full bg-ink px-6 py-3 text-sm font-semibold text-paper-card transition hover:bg-saffron disabled:cursor-not-allowed disabled:opacity-40"
          >
            {checking ? (
              <>Checking… <Loader2 className="h-4 w-4 animate-spin" /></>
            ) : (
              <>Continue <ChevronRight className="h-4 w-4" /></>
            )}
          </button>
        ) : (
          <motion.button
            whileTap={{ scale: 0.97 }}
            onClick={finish}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-full bg-saffron px-7 py-3 text-sm font-semibold text-paper-card transition hover:bg-saffron-deep disabled:opacity-60"
          >
            {busy ? "Setting up…" : mode === "signup" ? "Create my account" : "Save profile"}
            <Sparkles className="h-4 w-4" />
          </motion.button>
        )}
      </div>
    </div>
  )
}

function AccountStep({ d, set, emailErr, clearErr, checking }: { d: Data; set: (p: Partial<Data>) => void; emailErr?: string; clearErr: () => void; checking?: boolean }) {
  return (
    <div className="space-y-4">
      <Labelled label="Email">
        <Input
          type="email"
          value={d.email}
          onChange={(e) => {
            set({ email: e.target.value })
            clearErr()
          }}
          placeholder="you@example.com"
          autoFocus
          disabled={checking}
          aria-invalid={!!emailErr}
        />
        {emailErr && (
          <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} className="mt-1.5 text-sm text-saffron-deep">
            {emailErr}
          </motion.p>
        )}
      </Labelled>
      <Labelled label="Password" hint="At least 8 characters.">
        <Input type="password" value={d.password} onChange={(e) => set({ password: e.target.value })} placeholder="••••••••" disabled={checking} />
      </Labelled>
    </div>
  )
}

function AboutStep({ d, set, age }: { d: Data; set: (p: Partial<Data>) => void; age: number | null }) {
  return (
    <div className="space-y-5">
      <Labelled label="Your name">
        <Input value={d.name} onChange={(e) => set({ name: e.target.value })} placeholder="What should we call you?" autoFocus />
      </Labelled>
      <Labelled label="Date of birth" hint="Optional — helps tailor portion & nutrition cues.">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Cake className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
            <Input type="date" value={d.dob ?? ""} max={new Date().toISOString().slice(0, 10)} onChange={(e) => set({ dob: e.target.value })} className="pl-9" />
          </div>
          <AnimatePresence>
            {age != null && (
              <motion.span initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0, opacity: 0 }} className="rounded-full bg-saffron-wash px-3 py-2 font-mono text-sm text-saffron-deep">
                {age} yrs
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </Labelled>
      <div>
        <span className="label mb-2 block">Gender</span>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {GENDERS.map((g) => (
            <SelectTile key={g.key} active={d.gender === g.key} onClick={() => set({ gender: d.gender === g.key ? "" : g.key })} emoji={g.emoji} label={g.label} compact />
          ))}
        </div>
      </div>
    </div>
  )
}

function LocationStep({ d, set }: { d: Data; set: (p: Partial<Data>) => void }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string>()
  const pinned = d.lat != null && d.lng != null

  async function detect() {
    setBusy(true)
    setErr(undefined)
    const r = await detectLocation()
    if (r.lat != null) set({ lat: r.lat, lng: r.lng, location: r.location ?? d.location })
    else if (r.location) set({ location: r.location })
    else setErr("Couldn't get your location — type your city below.")
    setBusy(false)
  }

  return (
    <div className="space-y-5">
      <motion.button
        whileTap={{ scale: 0.98 }}
        onClick={detect}
        disabled={busy}
        className="group flex w-full items-center gap-4 rounded-2xl border-2 border-dashed border-ink-line bg-paper-card/60 p-5 text-left transition hover:border-saffron"
      >
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-saffron text-paper-card">
          {busy ? <Loader2 className="h-5 w-5 animate-spin" /> : <LocateFixed className="h-5 w-5" />}
        </span>
        <div>
          <p className="font-semibold text-ink">{busy ? "Finding you…" : "Use my current location"}</p>
          <p className="text-sm text-ink-faint">One tap — we reverse-geocode it to a place name.</p>
        </div>
      </motion.button>

      <Labelled label="City / area" hint="We use this to find restaurants near you and tailor suggestions.">
        <div className="relative">
          <MapPin className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
          <Input
            value={d.location ?? ""}
            onChange={(e) => set({ location: e.target.value, lat: null, lng: null })}
            placeholder="e.g. Park Street, Kolkata"
            className="pl-9"
          />
        </div>
      </Labelled>

      <AnimatePresence>
        {pinned && (
          <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="inline-flex items-center gap-2 rounded-full bg-pine-wash px-3 py-1.5 text-sm text-pine">
            <Check className="h-3.5 w-3.5" /> Pinned to your exact coordinates
          </motion.div>
        )}
      </AnimatePresence>
      {err && <p className="text-sm text-saffron-deep">{err}</p>}
    </div>
  )
}

function PickOne({ options, value, onPick }: { options: Opt[]; value?: string; onPick: (k: string) => void }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {options.map((o) => (
        <SelectTile key={o.key} active={value === o.key} onClick={() => onPick(o.key)} emoji={o.emoji} label={o.label} note={o.note} />
      ))}
    </div>
  )
}

function MultiPick({
  options,
  values,
  onChange,
  tone,
  allowCustom,
  placeholder,
  noneLabel,
}: {
  options: Opt[]
  values: string[]
  onChange: (v: string[]) => void
  tone: "saffron" | "pine"
  allowCustom?: boolean
  placeholder?: string
  noneLabel?: string
}) {
  const toggle = (k: string) => onChange(values.includes(k) ? values.filter((x) => x !== k) : [...values, k])
  const labels = new Set(options.map((o) => o.key))
  const custom = values.filter((v) => !labels.has(v))
  return (
    <div>
      {noneLabel && (
        <button onClick={() => onChange([])} className={cn("mb-3 rounded-full border px-4 py-1.5 text-sm transition", values.length === 0 ? "border-ink bg-ink text-paper-card" : "border-ink-line text-ink-soft hover:border-ink/40")}>
          {noneLabel}
        </button>
      )}
      <div className="flex flex-wrap gap-2">
        {options.map((o) => (
          <Pill key={o.key} active={values.includes(o.key)} tone={tone} onClick={() => toggle(o.key)}>
            {o.emoji && <span className="mr-1">{o.emoji}</span>}
            {o.label}
          </Pill>
        ))}
        {custom.map((c) => (
          <Pill key={c} active tone={tone} onClick={() => toggle(c)}>
            {c} <X className="ml-1 inline h-3 w-3" />
          </Pill>
        ))}
      </div>
      {allowCustom && <CustomAdd placeholder={placeholder} onAdd={(v) => !values.includes(v) && onChange([...values, v])} />}
    </div>
  )
}

function TastesStep({ d, set }: { d: Data; set: (p: Partial<Data>) => void }) {
  const toggleLike = (f: string) => set({ likes: d.likes.includes(f) ? d.likes.filter((x) => x !== f) : [...d.likes, f] })
  const toggleCui = (c: string) => set({ cuisines: d.cuisines.includes(c) ? d.cuisines.filter((x) => x !== c) : [...d.cuisines, c] })
  const foods = foodsForDiet(d.dietary_type) // diet-aware list
  const dietLabel = DIET_TYPES.find((t) => t.key === d.dietary_type)?.label
  const customLikes = d.likes.filter((l) => !foods.includes(l))
  return (
    <div className="space-y-6">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <span className="label">Foods you love</span>
          {dietLabel && <span className="rounded-full bg-pine-wash px-2 py-0.5 font-mono text-[0.6rem] uppercase text-pine">{dietLabel}</span>}
        </div>
        <motion.div layout className="flex flex-wrap gap-2">
          <AnimatePresence mode="popLayout">
            {foods.map((f) => (
              <motion.div key={f} layout initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }} transition={{ duration: 0.2 }}>
                <Pill active={d.likes.includes(f)} tone="saffron" onClick={() => toggleLike(f)}>
                  {f}
                </Pill>
              </motion.div>
            ))}
          </AnimatePresence>
          {customLikes.map((c) => (
            <Pill key={c} active tone="saffron" onClick={() => toggleLike(c)}>
              {c} <X className="ml-1 inline h-3 w-3" />
            </Pill>
          ))}
        </motion.div>
        <CustomAdd placeholder="Add a dish you love…" onAdd={(v) => !d.likes.includes(v) && set({ likes: [...d.likes, v] })} />
      </div>
      <div>
        <span className="label mb-2 block">Favourite cuisines</span>
        <div className="flex flex-wrap gap-2">
          {CUISINES.map((c) => (
            <Pill key={c.key} active={d.cuisines.includes(c.key)} tone="pine" onClick={() => toggleCui(c.key)}>
              {c.label}
            </Pill>
          ))}
        </div>
      </div>
      <div>
        <span className="label mb-2 block">Spice tolerance</span>
        <div className="grid grid-cols-4 gap-2">
          {SPICE.map((s) => (
            <SelectTile key={s.key} active={d.spice_tolerance === s.key} onClick={() => set({ spice_tolerance: d.spice_tolerance === s.key ? "" : s.key })} emoji={s.emoji} label={s.label} compact />
          ))}
        </div>
      </div>
    </div>
  )
}

const _labelFrom = (opts: Opt[], key: string) => opts.find((o) => o.key === key)?.label || key

function Review({ d, age }: { d: Data; age: number | null; mode: Mode }) {
  const dietOpt = DIET_TYPES.find((t) => t.key === d.dietary_type)
  const spiceOpt = SPICE.find((s) => s.key === d.spice_tolerance)
  const initial = (d.name || d.email || "K").trim().charAt(0).toUpperCase() || "K"
  const allergyLabels = d.allergies.map((a) => _labelFrom(ALLERGENS, a))
  const goalLabels = d.goals.map((g) => _labelFrom(GOALS, g))
  const cuisineLabels = d.cuisines.map((c) => _labelFrom(CUISINES, c))

  const rows = [
    { icon: ShieldAlert, label: "Allergies", accent: "saffron" as const, items: allergyLabels, empty: "None — eat freely" },
    { icon: Heart, label: "Loves", accent: "ink" as const, items: d.likes, empty: "Nothing added yet" },
    { icon: Utensils, label: "Cuisines", accent: "pine" as const, items: cuisineLabels, empty: "No favourites yet" },
    { icon: Target, label: "Goals", accent: "pine" as const, items: goalLabels, empty: "No goals set" },
  ]

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="overflow-hidden rounded-3xl border border-ink-line bg-paper-card shadow-lift">
      {/* passport header */}
      <div className="relative overflow-hidden bg-ink px-6 py-7 text-paper-card">
        <div className="pointer-events-none absolute -right-10 -top-12 h-44 w-44 rounded-full border-[18px] border-saffron/15" />
        <div className="relative flex items-center gap-4">
          <motion.div initial={{ scale: 0, rotate: -12 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: "spring", stiffness: 240, damping: 14 }} className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-saffron font-display text-2xl font-semibold text-paper-card">
            {initial}
          </motion.div>
          <div className="min-w-0">
            <p className="label !text-paper/40">taste passport</p>
            <h3 className="truncate font-display text-2xl leading-tight">{d.name || "Your profile"}</h3>
            <p className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-sm text-paper/60">
              {age != null && <span>{age} yrs</span>}
              {d.location && (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {d.location}
                  {d.lat != null && <Check className="h-3 w-3 text-saffron-glow" />}
                </span>
              )}
            </p>
          </div>
          {dietOpt && (
            <span className="ml-auto hidden shrink-0 items-center gap-1.5 rounded-full bg-paper/10 px-3 py-1.5 text-sm sm:inline-flex">
              <span>{dietOpt.emoji}</span> {dietOpt.label}
            </span>
          )}
        </div>
      </div>

      {/* passport body */}
      <div className="space-y-1 p-5 sm:p-6">
        {dietOpt && (
          <div className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-saffron-wash px-3 py-1 text-sm text-saffron-deep sm:hidden">
            <span>{dietOpt.emoji}</span> {dietOpt.label}
          </div>
        )}
        {rows.map((row, idx) => (
          <motion.div key={row.label} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.12 + idx * 0.07 }} className="flex items-start gap-3 border-b border-ink-line/60 py-3 last:border-0">
            <span className={cn("mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full", row.accent === "saffron" ? "bg-saffron-wash text-saffron-deep" : row.accent === "pine" ? "bg-pine-wash text-pine" : "bg-ink/5 text-ink-soft")}>
              <row.icon className="h-3.5 w-3.5" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="label mb-1.5">{row.label}</p>
              {row.items.length ? (
                <div className="flex flex-wrap gap-1.5">
                  {row.items.map((it) => (
                    <span key={it} className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", row.accent === "saffron" ? "bg-saffron text-paper-card" : row.accent === "pine" ? "bg-pine-wash text-pine" : "border border-ink-line bg-paper text-ink-soft")}>
                      {it}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="text-sm text-ink-faint">{row.empty}</span>
              )}
            </div>
          </motion.div>
        ))}
        <motion.div initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.12 + rows.length * 0.07 }} className="flex items-center gap-3 pt-3">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-saffron-wash text-saffron-deep">
            <Flame className="h-3.5 w-3.5" />
          </span>
          <p className="label">Spice</p>
          <span className="ml-1 font-medium text-ink">{spiceOpt ? `${spiceOpt.emoji} ${spiceOpt.label}` : "Not set"}</span>
        </motion.div>
      </div>
    </motion.div>
  )
}

function Success({ name }: { name?: string }) {
  return (
    <div className="flex min-h-[34rem] flex-col items-center justify-center text-center">
      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 260, damping: 16 }} className="flex h-20 w-20 items-center justify-center rounded-full bg-pine text-paper-card">
        <Check className="h-9 w-9" />
      </motion.div>
      <motion.h2 initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="mt-6 font-display text-4xl">
        You're all set{name ? `, ${name}` : ""}.
      </motion.h2>
      <p className="mt-2 text-ink-soft">Kensho will tailor everything to your taste.</p>
    </div>
  )
}

function Labelled({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="label mb-1.5 block">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-ink-faint">{hint}</span>}
    </label>
  )
}

function SelectTile({ active, onClick, emoji, label, note, compact }: { active: boolean; onClick: () => void; emoji?: string; label: string; note?: string; compact?: boolean }) {
  return (
    <motion.button
      whileTap={{ scale: 0.96 }}
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "relative flex flex-col items-start rounded-2xl border-2 text-left transition",
        compact ? "items-center gap-1 px-2 py-3 text-center" : "gap-1 p-4",
        active ? "border-saffron bg-saffron-wash" : "border-ink-line bg-paper-card/60 hover:border-ink/30",
      )}
    >
      {emoji && <span className={compact ? "text-xl" : "text-2xl"}>{emoji}</span>}
      <span className="font-semibold leading-tight text-ink">{label}</span>
      {note && <span className="text-xs text-ink-faint">{note}</span>}
      <AnimatePresence>
        {active && (
          <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }} className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-saffron text-paper-card">
            <Check className="h-3 w-3" />
          </motion.span>
        )}
      </AnimatePresence>
    </motion.button>
  )
}

function Pill({ children, active, tone, onClick }: { children: ReactNode; active: boolean; tone: "saffron" | "pine"; onClick: () => void }) {
  const on = tone === "saffron" ? "bg-saffron text-paper-card border-saffron" : "bg-pine text-paper-card border-pine"
  return (
    <motion.button
      whileTap={{ scale: 0.94 }}
      onClick={onClick}
      aria-pressed={active}
      className={cn("rounded-full border px-3.5 py-1.5 text-sm font-medium transition", active ? on : "border-ink-line bg-paper-card/60 text-ink-soft hover:border-ink/40")}
    >
      {children}
    </motion.button>
  )
}

function CustomAdd({ placeholder, onAdd }: { placeholder?: string; onAdd: (v: string) => void }) {
  const [v, setV] = useState("")
  const add = () => {
    const t = v.trim()
    if (t) {
      onAdd(t)
      setV("")
    }
  }
  return (
    <div className="mt-3 flex items-center gap-2 rounded-full border border-dashed border-ink-line bg-paper px-3 py-1 sm:max-w-xs">
      <input
        value={v}
        onChange={(e) => setV(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault()
            add()
          }
        }}
        placeholder={placeholder || "Add your own…"}
        className="flex-1 bg-transparent py-1.5 text-sm outline-none placeholder:text-ink-faint"
      />
      <button onClick={add} className="flex h-7 w-7 items-center justify-center rounded-full bg-ink text-paper-card transition hover:bg-saffron">
        <Plus className="h-4 w-4" />
      </button>
    </div>
  )
}
