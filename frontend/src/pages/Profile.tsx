import { motion } from "framer-motion"
import { LogOut, MapPin, Network, Pencil, ShieldAlert, Sparkles } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Onboarding } from "../components/Onboarding"
import { Reveal } from "../components/fx"
import { api } from "../lib/api"
import { cn } from "../lib/cn"
import type { TasteGraph } from "../lib/types"
import { useAuth } from "../state/auth"

export function Profile() {
  const { user, profile, logout, refreshProfile } = useAuth()
  const nav = useNavigate()
  const [editing, setEditing] = useState(false)

  if (editing) {
    return (
      <section className="mx-auto max-w-5xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
        <Reveal>
          <span className="label text-saffron">Edit profile</span>
          <h1 className="mt-3 font-display text-4xl">Update your taste.</h1>
          <p className="mt-2 text-ink-soft">Change anything — Kensho re-tunes your recommendations instantly.</p>
        </Reveal>
        <div className="mt-8">
          <Onboarding
            mode="complete"
            onDone={async () => {
              await refreshProfile()
              setEditing(false)
            }}
          />
        </div>
      </section>
    )
  }

  const name = profile?.name || user?.email?.split("@")[0] || "You"
  const initial = name.trim().charAt(0).toUpperCase() || "K"

  return (
    <section className="mx-auto max-w-5xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      {/* header card */}
      <Reveal>
        <div className="card overflow-hidden">
          <div className="relative bg-ink px-6 py-8 text-paper-card sm:px-8">
            <div className="pointer-events-none absolute -right-10 -top-12 h-44 w-44 rounded-full border-[18px] border-saffron/15" />
            <div className="relative flex flex-wrap items-center gap-5">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-saffron font-display text-3xl font-semibold">
                {initial}
              </div>
              <div className="min-w-0">
                <h1 className="font-display text-3xl leading-tight">{name}</h1>
                <p className="mt-1 flex flex-wrap items-center gap-x-3 text-sm text-paper/60">
                  {user?.email && <span>{user.email}</span>}
                  {profile?.location && (
                    <span className="inline-flex items-center gap-1">
                      <MapPin className="h-3 w-3" /> {profile.location}
                    </span>
                  )}
                  {profile?.age != null && <span>{profile.age} yrs</span>}
                </p>
              </div>
              <div className="ml-auto flex gap-2">
                <button onClick={() => setEditing(true)} className="inline-flex items-center gap-2 rounded-full bg-paper-card px-4 py-2 text-sm font-semibold text-ink transition hover:bg-saffron hover:text-paper-card">
                  <Pencil className="h-4 w-4" /> Edit
                </button>
                <button
                  onClick={() => {
                    logout()
                    nav("/")
                  }}
                  className="inline-flex items-center gap-2 rounded-full border border-white/15 px-4 py-2 text-sm text-paper-card/80 transition hover:border-white/40"
                >
                  <LogOut className="h-4 w-4" /> Sign out
                </button>
              </div>
            </div>
          </div>

          {/* facts */}
          <div className="grid gap-5 p-6 sm:grid-cols-2 sm:p-8">
            <Fact label="Diet" value={(profile?.dietary_type || "—").replace("-", " ")} />
            <Fact label="Spice tolerance" value={profile?.spice_tolerance || "—"} />
            <PillFact label="Allergies" items={profile?.allergies || []} tone="saffron" icon={<ShieldAlert className="h-3.5 w-3.5" />} empty="None" />
            <PillFact label="Goals" items={profile?.goals || []} tone="pine" empty="None set" />
            <PillFact label="Loves" items={profile?.likes || []} tone="ink" empty="Nothing yet" />
            <PillFact label="Cuisines" items={profile?.cuisines || []} tone="pine" empty="No favourites" />
          </div>
        </div>
      </Reveal>

      <TasteGraphView />
    </section>
  )
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="label mb-1">{label}</p>
      <p className="font-display text-xl capitalize text-ink">{value}</p>
    </div>
  )
}

function PillFact({ label, items, tone, icon, empty }: { label: string; items: string[]; tone: "saffron" | "pine" | "ink"; icon?: React.ReactNode; empty: string }) {
  const cls = { saffron: "bg-saffron text-paper-card", pine: "bg-pine-wash text-pine", ink: "border border-ink-line bg-paper text-ink-soft" }[tone]
  return (
    <div>
      <p className="label mb-1.5 flex items-center gap-1.5">
        {icon} {label}
      </p>
      {items.length ? (
        <div className="flex flex-wrap gap-1.5">
          {items.map((it) => (
            <span key={it} className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium capitalize", cls)}>{it}</span>
          ))}
        </div>
      ) : (
        <span className="text-sm text-ink-faint">{empty}</span>
      )}
    </div>
  )
}

const GROUP_COLORS: Record<string, string> = {
  user: "#E0531F",
  diet: "#2f6b4f",
  cuisine: "#E0531F",
  food: "#9a5b2c",
  allergy: "#c0392b",
  goal: "#7c3a6e",
}

function TasteGraphView() {
  const [g, setG] = useState<TasteGraph | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.tasteGraph().then(setG).catch(() => setG(null)).finally(() => setLoading(false))
  }, [])

  const layout = useMemo(() => {
    if (!g) return null
    const others = g.nodes.filter((n) => n.id !== "me")
    const cx = 300, cy = 300, R = 215
    const placed = others.map((n, i) => {
      const angle = (i / Math.max(1, others.length)) * Math.PI * 2 - Math.PI / 2
      const r = R - (i % 2) * 64
      return { ...n, x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r, angle }
    })
    return { cx, cy, placed }
  }, [g])

  if (loading) return <div className="skeleton mt-12 h-80" />
  if (!g || !layout) return null

  return (
    <div className="mt-12">
      <div className="mb-5 flex items-center gap-2">
        <Network className="h-4 w-4 text-saffron" />
        <h2 className="font-display text-3xl">Your taste graph</h2>
      </div>
      <div className="card overflow-hidden p-4 sm:p-6">
        <div className="grid items-center gap-6 lg:grid-cols-[1.4fr_1fr]">
          <svg viewBox="0 0 600 600" className="mx-auto w-full max-w-xl">
            {/* edges */}
            {layout.placed.map((n, i) => (
              <motion.line
                key={"e" + n.id}
                x1={layout.cx}
                y1={layout.cy}
                x2={n.x}
                y2={n.y}
                stroke={GROUP_COLORS[n.group] || "#ccc"}
                strokeOpacity={0.35}
                strokeWidth={1.4}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ delay: 0.1 + i * 0.03, duration: 0.6 }}
              />
            ))}
            {/* nodes */}
            {layout.placed.map((n, i) => (
              <motion.g
                key={n.id}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 + i * 0.04, type: "spring", stiffness: 240, damping: 16 }}
              >
                <circle cx={n.x} cy={n.y} r={6 + (n.weight || 3)} fill={GROUP_COLORS[n.group] || "#999"} />
                <text
                  x={n.x}
                  y={n.y - 14}
                  textAnchor="middle"
                  className="fill-ink"
                  style={{ fontSize: 13, fontWeight: 500 }}
                >
                  {n.label.length > 16 ? n.label.slice(0, 15) + "…" : n.label}
                </text>
              </motion.g>
            ))}
            {/* center */}
            <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 220, damping: 14 }}>
              <circle cx={layout.cx} cy={layout.cy} r={34} fill="#1a1714" />
              <text x={layout.cx} y={layout.cy + 5} textAnchor="middle" className="fill-paper" style={{ fontSize: 15, fontWeight: 600 }}>
                {g.center.label.length > 8 ? g.center.label.slice(0, 7) + "…" : g.center.label}
              </text>
            </motion.g>
          </svg>

          <div>
            <p className="text-pretty text-ink-soft">
              A living map of what shapes your recommendations — your diet, the cuisines and dishes you love, allergies
              Kensho avoids, and your goals.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              {Object.entries({ diet: "Diet", cuisine: "Cuisines", food: "Foods", allergy: "Allergies", goal: "Goals" }).map(([k, v]) => (
                <span key={k} className="inline-flex items-center gap-1.5 rounded-full border border-ink-line px-3 py-1 text-xs">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: GROUP_COLORS[k] }} /> {v}
                </span>
              ))}
            </div>
            {g.insights && Object.keys(g.insights).length > 0 && (
              <div className="mt-6 grid grid-cols-2 gap-3">
                {g.insights.total_interactions != null && <Insight label="Interactions" value={g.insights.total_interactions} />}
                {g.insights.total_searches != null && <Insight label="Searches" value={g.insights.total_searches} />}
                {Array.isArray(g.insights.favorite_cuisines) && g.insights.favorite_cuisines.length > 0 && (
                  <div className="col-span-2">
                    <p className="label mb-1.5 flex items-center gap-1.5"><Sparkles className="h-3.5 w-3.5 text-saffron" /> Graph says you love</p>
                    <div className="flex flex-wrap gap-1.5">
                      {g.insights.favorite_cuisines.slice(0, 6).map((c: string) => (
                        <span key={c} className="rounded-full bg-saffron-wash px-2.5 py-0.5 text-xs capitalize text-saffron-deep">{c}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function Insight({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-ink-line bg-paper-card/60 px-4 py-3">
      <div className="font-display text-2xl text-ink">{value}</div>
      <div className="label">{label}</div>
    </div>
  )
}
