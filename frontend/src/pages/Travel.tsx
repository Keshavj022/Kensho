import { motion } from "framer-motion"
import { ExternalLink, Hotel, MapPinned, Plane, Sparkles, Star } from "lucide-react"
import { FormEvent, useEffect, useRef, useState } from "react"
import { Button, Chip, Field, Input, Select, StatusNote } from "../components/ui"
import { Reveal } from "../components/fx"
import { api } from "../lib/api"
import { money, cn } from "../lib/cn"
import type { Flight, FlightSearch, HotelSearch, TripPlan } from "../lib/types"
import { useAuth } from "../state/auth"

function useHomeAirport(): string | null {
  const { profile } = useAuth()
  const [iata, setIata] = useState<string | null>(null)
  useEffect(() => {
    if (profile?.lat == null && !profile?.location) return
    api
      .nearestAirport(profile.lat, profile.lng, profile.location)
      .then((a) => a.iata && setIata(a.iata))
      .catch(() => {})
  }, [profile])
  return iata
}

const future = (days: number) => {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}
const fmtDur = (m?: number) => (m == null ? "" : `${Math.floor(m / 60)}h ${m % 60}m`)
const timeOnly = (s?: string) => (s ? s.split(" ")[1]?.slice(0, 5) || s : "")

export function Travel() {
  const [tab, setTab] = useState<"flights" | "hotels" | "plan">("flights")
  return (
    <section className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-36">
      <Reveal>
        <span className="label text-pine">02 · Go</span>
        <h1 className="mt-3 font-display text-[clamp(2.1rem,6vw,4.6rem)] font-medium leading-[0.98]">
          Search the world, <span className="italic text-pine">skip the booking.</span>
        </h1>
        <p className="mt-4 max-w-xl text-lg text-ink-soft text-pretty">
          Metasearch for flights and stays — the cheapest option, who's offering it, a deep link, and price context. Or
          let Kensho assemble a day-by-day plan.
        </p>
      </Reveal>

      <div className="mt-9 inline-flex flex-wrap rounded-full border border-ink-line bg-paper-card/60 p-1">
        {([["flights", Plane], ["hotels", Hotel], ["plan", MapPinned]] as const).map(([t, Icon]) => (
          <button key={t} onClick={() => setTab(t)} className={cn("relative rounded-full px-5 py-2 text-sm font-semibold capitalize transition-colors", tab === t ? "text-paper-card" : "text-ink-soft hover:text-ink")}>
            {tab === t && <motion.span layoutId="ttab" className="absolute inset-0 rounded-full bg-pine" transition={{ type: "spring", stiffness: 320, damping: 28 }} />}
            <span className="relative flex items-center gap-2">
              <Icon className="h-4 w-4" />
              {t === "plan" ? "Plan a trip" : t}
            </span>
          </button>
        ))}
      </div>

      <div className="mt-6">
        {tab === "flights" && <Flights />}
        {tab === "hotels" && <Hotels />}
        {tab === "plan" && <Planner />}
      </div>
    </section>
  )
}

function Flights() {
  const [f, setF] = useState({ origin: "CCU", destination: "DEL", departure_date: future(14), return_date: "", adults: 1 })
  const [res, setRes] = useState<FlightSearch | null>(null)
  const [loading, setLoading] = useState(false)
  const home = useHomeAirport()
  const touched = useRef(false)
  useEffect(() => {
    if (home && !touched.current) setF((s) => ({ ...s, origin: home }))
  }, [home])

  async function run(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      setRes(await api.searchFlights({ ...f, return_date: f.return_date || undefined }))
    } catch {
      setRes({ status: "error", best_flights: [] })
    } finally {
      setLoading(false)
    }
  }

  const flights = res?.flights || res?.best_flights || res?.other_flights || []
  return (
    <>
      <form onSubmit={run} className="card grid gap-3 p-5 sm:grid-cols-[1fr_1fr_1fr_1fr_auto]">
        <Field label="From"><Input value={f.origin} onChange={(e) => { touched.current = true; setF({ ...f, origin: e.target.value.toUpperCase() }) }} placeholder="CCU" /></Field>
        <Field label="To"><Input value={f.destination} onChange={(e) => setF({ ...f, destination: e.target.value.toUpperCase() })} placeholder="DEL" /></Field>
        <Field label="Depart"><Input type="date" value={f.departure_date} onChange={(e) => setF({ ...f, departure_date: e.target.value })} /></Field>
        <Field label="Return"><Input type="date" value={f.return_date} onChange={(e) => setF({ ...f, return_date: e.target.value })} /></Field>
        <div className="flex items-end"><Button loading={loading} className="w-full bg-pine hover:bg-pine-ink">Search</Button></div>
      </form>

      <div className="mt-8 space-y-4">
        {loading && Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-24" />)}
        {!loading && res && res.status !== "ok" && <StatusNote status={res.status} message={res.message} />}
        {!loading && res?.price_insights?.lowest_price != null && (
          <div className="flex flex-wrap items-center gap-x-6 gap-y-1 rounded-2xl bg-pine px-5 py-3 text-paper-card">
            <span className="label !text-paper/60">price insight</span>
            <span className="font-mono">low {money(res.price_insights.lowest_price)}</span>
            {res.price_insights.typical_price_range && <span className="text-paper/70">typical {money(res.price_insights.typical_price_range[0])}–{money(res.price_insights.typical_price_range[1])}</span>}
            {res.price_insights.price_level && <span className="rounded-full bg-paper/15 px-2 py-0.5 text-xs uppercase">{res.price_insights.price_level}</span>}
          </div>
        )}
        {!loading && flights.map((fl, i) => <FlightCard key={i} f={fl} best={i === 0} cur={res?.currency} />)}
        {!loading && res?.status === "ok" && flights.length === 0 && <p className="py-8 text-center text-ink-faint">No flights found for those dates.</p>}
      </div>
    </>
  )
}

function FlightCard({ f, best, cur }: { f: Flight; best?: boolean; cur?: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className={cn("card flex flex-wrap items-center gap-x-8 gap-y-3 p-5", best && "ring-2 ring-pine")}>
      {best && <span className="absolute -top-2.5 left-5 rounded-full bg-pine px-2.5 py-0.5 font-mono text-[0.6rem] uppercase text-paper-card">cheapest</span>}
      <div className="min-w-[8rem]">
        <p className="font-semibold">{f.airlines?.join(", ") || "—"}</p>
        <p className="font-mono text-xs text-ink-faint">{(f.stops ?? 0) === 0 ? "nonstop" : `${f.stops} stop${(f.stops ?? 0) > 1 ? "s" : ""}`}</p>
      </div>
      <div className="flex items-center gap-3 font-mono">
        <span className="text-lg">{timeOnly(f.departure?.time)}</span>
        <span className="text-ink-line">———✈</span>
        <span className="text-lg">{timeOnly(f.arrival?.time)}</span>
      </div>
      <span className="text-sm text-ink-faint">{fmtDur(f.total_duration_minutes)}</span>
      <span className="ml-auto font-display text-3xl text-pine">{money(f.price, cur)}</span>
    </motion.div>
  )
}

function Hotels() {
  const [f, setF] = useState({ location: "Goa", check_in: future(14), check_out: future(17), guests: 2 })
  const [res, setRes] = useState<HotelSearch | null>(null)
  const [loading, setLoading] = useState(false)
  async function run(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      setRes(await api.searchHotels(f))
    } catch {
      setRes({ status: "error", hotels: [] })
    } finally {
      setLoading(false)
    }
  }
  return (
    <>
      <form onSubmit={run} className="card grid gap-3 p-5 sm:grid-cols-[1.4fr_1fr_1fr_0.7fr_auto]">
        <Field label="Where"><Input value={f.location} onChange={(e) => setF({ ...f, location: e.target.value })} placeholder="Goa" /></Field>
        <Field label="Check in"><Input type="date" value={f.check_in} onChange={(e) => setF({ ...f, check_in: e.target.value })} /></Field>
        <Field label="Check out"><Input type="date" value={f.check_out} onChange={(e) => setF({ ...f, check_out: e.target.value })} /></Field>
        <Field label="Guests"><Input type="number" min={1} value={f.guests} onChange={(e) => setF({ ...f, guests: +e.target.value })} /></Field>
        <div className="flex items-end"><Button loading={loading} className="w-full bg-pine hover:bg-pine-ink">Search</Button></div>
      </form>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {loading && Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-40" />)}
        {!loading && res && res.status !== "ok" && <div className="md:col-span-2"><StatusNote status={res.status} message={res.message} /></div>}
        {!loading && (res?.hotels || []).map((h, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i * 0.05, 0.4) }} className="card p-5">
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-display text-xl leading-snug">{h.name}</h3>
              {h.rating != null && <span className="flex items-center gap-1 font-mono text-sm"><Star className="h-3.5 w-3.5 fill-saffron-glow text-saffron-glow" />{h.rating}</span>}
            </div>
            {h.hotel_class && <p className="mt-1 text-xs text-ink-faint">{h.hotel_class}</p>}
            <div className="mt-4 flex items-end justify-between">
              <div>
                <p className="font-display text-2xl text-pine">{money(h.price_per_night, res?.currency)}<span className="text-sm text-ink-faint"> /night</span></p>
                {h.cheapest_provider?.source && (
                  <p className="mt-1 text-sm text-ink-faint">via {h.cheapest_provider.source}{h.cheapest_provider.official ? " · official" : ""}</p>
                )}
              </div>
              {h.cheapest_provider?.link && (
                <a href={h.cheapest_provider.link} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-paper-card hover:bg-pine">
                  View <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </>
  )
}

function Planner() {
  const [f, setF] = useState({ destination: "Goa", origin: "CCU", start_date: future(20), end_date: future(23), travelers: 2, pace: "moderate", interests: ["food", "beaches"] })
  const [plan, setPlan] = useState<TripPlan | null>(null)
  const [loading, setLoading] = useState(false)
  const home = useHomeAirport()
  const touched = useRef(false)
  useEffect(() => {
    if (home && !touched.current) setF((s) => ({ ...s, origin: home }))
  }, [home])
  const INTERESTS = ["food", "history", "nature", "beaches", "nightlife", "shopping"]

  async function run(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      setPlan(await api.planTrip({ ...f, origin: f.origin || undefined }))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <form onSubmit={run} className="card p-5">
        <div className="grid gap-3 sm:grid-cols-[1.2fr_0.8fr_1fr_1fr_0.7fr]">
          <Field label="Destination"><Input value={f.destination} onChange={(e) => setF({ ...f, destination: e.target.value })} /></Field>
          <Field label="From (opt)"><Input value={f.origin} onChange={(e) => { touched.current = true; setF({ ...f, origin: e.target.value.toUpperCase() }) }} placeholder="CCU" /></Field>
          <Field label="Start"><Input type="date" value={f.start_date} onChange={(e) => setF({ ...f, start_date: e.target.value })} /></Field>
          <Field label="End"><Input type="date" value={f.end_date} onChange={(e) => setF({ ...f, end_date: e.target.value })} /></Field>
          <Field label="Pace">
            <Select value={f.pace} onChange={(e) => setF({ ...f, pace: e.target.value })}>
              <option value="relaxed">relaxed</option>
              <option value="moderate">moderate</option>
              <option value="packed">packed</option>
            </Select>
          </Field>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="label mr-1">interests</span>
          {INTERESTS.map((it) => (
            <Chip key={it} tone="pine" active={f.interests.includes(it)} onClick={() => setF((s) => ({ ...s, interests: s.interests.includes(it) ? s.interests.filter((x) => x !== it) : [...s.interests, it] }))}>
              {it}
            </Chip>
          ))}
          <Button loading={loading} className="ml-auto bg-pine hover:bg-pine-ink" icon={<Sparkles className="h-4 w-4" />}>Plan trip</Button>
        </div>
      </form>

      <div className="mt-8">
        {loading && <div className="card flex flex-col items-center gap-3 py-16 text-center"><Sparkles className="h-7 w-7 animate-pulse text-pine" /><p className="font-display text-xl">Plotting your days…</p></div>}
        {!loading && plan && plan.status === "ok" && <PlanView plan={plan} />}
        {!loading && plan && plan.status !== "ok" && <StatusNote status={plan.status} message={plan.note} />}
      </div>
    </>
  )
}

function PlanView({ plan }: { plan: TripPlan }) {
  const cheapestFlight = (plan.flights as FlightSearch | undefined)?.cheapest
  return (
    <div>
      <div className="grid gap-4 sm:grid-cols-3">
        <SummaryCard k="Nights" v={`${plan.nights}`} sub={`${plan.travelers} traveller${plan.travelers > 1 ? "s" : ""} · ${plan.pace}`} />
        <SummaryCard k="Flight from" v={cheapestFlight?.price ? money(cheapestFlight.price, plan.currency) : "—"} sub={cheapestFlight?.airlines?.join(", ") || "no origin set"} />
        <SummaryCard k="Est. total" v={plan.estimated_cost ? money(plan.estimated_cost, plan.currency) : "—"} sub={plan.hotel?.name ? `stay: ${plan.hotel.name}` : "search-derived"} accent />
      </div>

      <div className="mt-8 space-y-4">
        {plan.daily.map((d, i) => (
          <motion.div key={d.day} initial={{ opacity: 0, x: -14 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: Math.min(i * 0.05, 0.4) }} className="card p-6">
            <div className="flex items-baseline gap-3 border-b border-ink-line pb-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-pine font-mono text-sm text-paper-card">{d.day}</span>
              <h3 className="font-display text-xl">{d.date}</h3>
              <span className="ml-auto text-sm text-ink-faint">{d.location}</span>
            </div>
            <div className="mt-4 grid gap-6 sm:grid-cols-[1.3fr_1fr]">
              <div>
                <p className="label mb-2">activities</p>
                {d.activities.length ? (
                  <ul className="space-y-2">
                    {d.activities.map((a, j) => (
                      <li key={j} className="flex items-start gap-3">
                        <span className="mt-0.5 font-mono text-xs text-pine">{a.time || "·"}</span>
                        <div>
                          <p className="font-medium">{a.name}</p>
                          {a.summary && <p className="text-sm text-ink-faint text-pretty">{a.summary}</p>}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-ink-faint">Free exploration (enable Tavily for suggested activities).</p>
                )}
              </div>
              <div>
                <p className="label mb-2">meals</p>
                <ul className="space-y-1.5 text-sm">
                  {d.meals.map((m) => (
                    <li key={m.type} className="flex gap-2">
                      <span className="font-mono text-xs text-ink-faint">{m.time}</span>
                      <span className="capitalize text-ink-soft">{m.type}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
      <p className="mt-6 text-center text-xs text-ink-faint">{plan.note}</p>
    </div>
  )
}

function SummaryCard({ k, v, sub, accent }: { k: string; v: string; sub?: string; accent?: boolean }) {
  return (
    <div className={cn("rounded-2xl border p-5", accent ? "border-pine bg-pine text-paper-card" : "border-ink-line bg-paper-card")}>
      <p className={cn("label", accent && "!text-paper/60")}>{k}</p>
      <p className="mt-2 font-display text-3xl">{v}</p>
      {sub && <p className={cn("mt-1 text-sm", accent ? "text-paper/70" : "text-ink-faint")}>{sub}</p>}
    </div>
  )
}
