import { motion } from "framer-motion"
import { Clock, LocateFixed, Loader2, MapPin, Search, Soup, Sparkles, Store } from "lucide-react"
import { FormEvent, useState } from "react"
import { Link } from "react-router-dom"
import { Button, Chip, PriceTag, Stars, StatusNote } from "../components/ui"
import { Reveal } from "../components/fx"
import { api } from "../lib/api"
import { detectLocation } from "../lib/geo"
import { INR, cn } from "../lib/cn"
import type { Dish, Restaurant } from "../lib/types"
import { useAuth } from "../state/auth"

function dietChipFromProfile(t?: string): string | null {
  if (t === "vegan") return "Vegan"
  if (t === "non-vegetarian" || t === "pescatarian") return "Non-veg"
  if (t) return "Vegetarian" // vegetarian / eggetarian / jain
  return null
}

const CUISINES = ["Bengali", "Mughlai", "South Indian", "Chinese", "Italian", "Cafe", "Street Food"]
const DIETARY = ["Vegetarian", "Vegan", "Non-veg"]

export function Restaurants() {
  const [tab, setTab] = useState<"places" | "dishes">("places")

  return (
    <section className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-36">
      <Reveal>
        <span className="label text-saffron">01 · Eat</span>
        <h1 className="mt-3 font-display text-[clamp(2.6rem,6vw,4.6rem)] font-medium leading-[0.95]">
          Find a table, <span className="italic text-saffron">read the menu.</span>
        </h1>
        <p className="mt-4 max-w-xl text-lg text-ink-soft text-pretty">
          Search restaurants via Google Maps, then open one to see a menu Kensho extracts from photos — or search for a
          specific dish across every menu it has read.
        </p>
      </Reveal>

      <div className="mt-9 inline-flex rounded-full border border-ink-line bg-paper-card/60 p-1">
        {(["places", "dishes"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "relative rounded-full px-5 py-2 text-sm font-semibold transition-colors",
              tab === t ? "text-paper-card" : "text-ink-soft hover:text-ink",
            )}
          >
            {tab === t && (
              <motion.span layoutId="rtab" className="absolute inset-0 rounded-full bg-ink" transition={{ type: "spring", stiffness: 320, damping: 28 }} />
            )}
            <span className="relative flex items-center gap-2">
              {t === "places" ? <Store className="h-4 w-4" /> : <Soup className="h-4 w-4" />}
              {t === "places" ? "Find places" : "Find a dish"}
            </span>
          </button>
        ))}
      </div>

      <div className="mt-6">{tab === "places" ? <PlaceSearch /> : <DishSearch />}</div>
    </section>
  )
}

function PlaceSearch() {
  const { profile } = useAuth()
  const [query, setQuery] = useState("")
  const [location, setLocation] = useState(profile?.location || "Kolkata")
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(
    profile?.lat != null && profile?.lng != null ? { lat: profile.lat, lng: profile.lng } : null,
  )
  const [cuisine, setCuisine] = useState<string | null>(null)
  const [dietary, setDietary] = useState<string | null>(() => dietChipFromProfile(profile?.dietary_type))
  const [openNow, setOpenNow] = useState(false)
  const [results, setResults] = useState<Restaurant[] | null>(null)
  const [status, setStatus] = useState<string>()
  const [loading, setLoading] = useState(false)
  const [locating, setLocating] = useState(false)

  async function run(e?: FormEvent, override?: { lat: number; lng: number; location?: string }) {
    e?.preventDefault()
    const ll = override ?? coords
    setLoading(true)
    setStatus(undefined)
    try {
      const r = await api.searchRestaurants({
        query: query || undefined,
        location: override?.location ?? location ?? undefined,
        lat: ll?.lat,
        lng: ll?.lng,
        radius: ll ? 6000 : undefined,
        cuisine: cuisine?.toLowerCase(),
        dietary: dietary?.toLowerCase(),
        open_now: openNow || undefined,
        max_results: 18,
      })
      setResults(r.restaurants || [])
      if (r.status !== "ok") setStatus(r.status)
    } catch {
      setStatus("error")
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  async function useMyLocation() {
    setLocating(true)
    const r = await detectLocation()
    setLocating(false)
    if (r.lat != null) {
      setCoords({ lat: r.lat, lng: r.lng! })
      if (r.location) setLocation(r.location)
      run(undefined, { lat: r.lat, lng: r.lng!, location: r.location })
    }
  }

  return (
    <>
      <form onSubmit={run} className="card p-5">
        <div className="grid gap-3 sm:grid-cols-[1.3fr_1fr_auto]">
          <div className="flex items-center gap-2 rounded-xl border border-ink-line bg-paper px-3">
            <Search className="h-4 w-4 text-ink-faint" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="ramen, rooftop, thali…" className="w-full bg-transparent py-3 outline-none placeholder:text-ink-faint" />
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-ink-line bg-paper px-3">
            <MapPin className="h-4 w-4 text-ink-faint" />
            <input
              value={location}
              onChange={(e) => {
                setLocation(e.target.value)
                setCoords(null)
              }}
              placeholder="location"
              className="w-full bg-transparent py-3 outline-none placeholder:text-ink-faint"
            />
            <button type="button" onClick={useMyLocation} title="Use my location" className="shrink-0 text-ink-faint transition hover:text-saffron">
              {locating ? <Loader2 className="h-4 w-4 animate-spin" /> : <LocateFixed className="h-4 w-4" />}
            </button>
          </div>
          <Button variant="spice" loading={loading} icon={<Search className="h-4 w-4" />} className="h-full px-7">
            Search
          </Button>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="label mr-1">cuisine</span>
          {CUISINES.map((c) => (
            <Chip key={c} tone="saffron" active={cuisine === c} onClick={() => setCuisine(cuisine === c ? null : c)}>
              {c}
            </Chip>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="label mr-1">diet</span>
          {DIETARY.map((d) => (
            <Chip key={d} tone="pine" active={dietary === d} onClick={() => setDietary(dietary === d ? null : d)}>
              {d}
            </Chip>
          ))}
          <Chip tone="ink" active={openNow} onClick={() => setOpenNow((o) => !o)}>
            Open now
          </Chip>
          {coords && (
            <span className="ml-auto inline-flex items-center gap-1 font-mono text-xs text-pine">
              <LocateFixed className="h-3 w-3" /> within 6 km of you
            </span>
          )}
        </div>
      </form>

      <div className="mt-8">
        {loading && <Skeletons />}
        {!loading && status && <StatusNote status={status} />}
        {!loading && results && results.length > 0 && (
          <>
            <p className="label mb-4">{results.length} places</p>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {results.map((r, i) => (
                <RestaurantCard key={r.id} r={r} i={i} />
              ))}
            </div>
          </>
        )}
        {!loading && results && results.length === 0 && !status && (
          <p className="py-12 text-center text-ink-faint">No places matched — try a broader search.</p>
        )}
      </div>
    </>
  )
}

function RestaurantCard({ r, i }: { r: Restaurant; i: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(i * 0.05, 0.4), ease: [0.16, 1, 0.3, 1] }}
    >
      <Link to={`/restaurants/${encodeURIComponent(r.id)}`} state={{ restaurant: r }} className="group block">
        <motion.div whileHover={{ y: -6 }} transition={{ type: "spring", stiffness: 280, damping: 22 }} className="card h-full overflow-hidden">
          <div className="relative h-36 overflow-hidden bg-paper-deep">
            {r.thumbnail ? (
              <img src={r.thumbnail} alt="" className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" loading="lazy" />
            ) : (
              <div className="flex h-full items-center justify-center bg-gradient-to-br from-saffron-wash to-paper-deep">
                <Soup className="h-9 w-9 text-saffron/50" />
              </div>
            )}
            {r.open_now != null && (
              <span className={cn("absolute left-3 top-3 flex items-center gap-1 rounded-full px-2.5 py-1 font-mono text-[0.6rem] uppercase", r.open_now ? "bg-pine text-paper-card" : "bg-ink/70 text-paper-card")}>
                <Clock className="h-3 w-3" /> {r.open_now ? "open" : "closed"}
              </span>
            )}
          </div>
          <div className="p-5">
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-display text-xl leading-snug">{r.name}</h3>
              <PriceTag level={r.price_level} range={r.price_range} />
            </div>
            <div className="mt-2 flex items-center gap-3">
              <Stars value={r.rating} count={r.rating_count} />
              {r.primary_type && <span className="truncate text-xs text-ink-faint">{r.primary_type}</span>}
            </div>
            {r.address && <p className="mt-2 line-clamp-1 text-sm text-ink-faint">{r.address}</p>}
            <div className="mt-4 flex items-center gap-1.5 text-sm font-semibold text-saffron">
              View menu <Sparkles className="h-3.5 w-3.5" />
            </div>
          </div>
        </motion.div>
      </Link>
    </motion.div>
  )
}

function DishSearch() {
  const [query, setQuery] = useState("")
  const [dishes, setDishes] = useState<Dish[] | null>(null)
  const [indexed, setIndexed] = useState<number>()
  const [loading, setLoading] = useState(false)

  async function run(e?: FormEvent) {
    e?.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    try {
      const r = await api.searchDishes(query, 18)
      setDishes(r.dishes || [])
      setIndexed(r.indexed_items)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <form onSubmit={run} className="card flex items-center gap-2 p-2 pl-5">
        <Soup className="h-5 w-5 text-saffron" />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="spicy paneer · creamy pasta · cold brew…" className="flex-1 bg-transparent py-3 outline-none placeholder:text-ink-faint" />
        <Button variant="spice" loading={loading}>Search dishes</Button>
      </form>
      {indexed != null && <p className="mt-3 font-mono text-xs text-ink-faint">searching {indexed} indexed items across restaurants</p>}

      <div className="mt-8">
        {loading && <Skeletons rows />}
        {!loading && dishes && dishes.length > 0 && (
          <div className="space-y-3">
            {dishes.map((d, i) => (
              <motion.div key={d.id} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: Math.min(i * 0.04, 0.4) }}>
                <Link to={`/restaurants/${encodeURIComponent(d.restaurant_id)}`} className="card flex items-center gap-4 p-4 transition hover:border-saffron">
                  {d.score != null && <span className="font-mono text-xs text-saffron">{Math.round(d.score * 100)}%</span>}
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{d.name}</p>
                    <p className="truncate text-sm text-ink-faint">
                      {d.restaurant_name}
                      {d.section ? ` · ${d.section}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {d.dietary_flags?.slice(0, 2).map((f) => (
                      <span key={f} className="rounded-full bg-pine-wash px-2 py-0.5 font-mono text-[0.6rem] uppercase text-pine">{f}</span>
                    ))}
                    <span className="font-mono text-pine">{INR(d.price)}</span>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
        {!loading && dishes && dishes.length === 0 && (
          <StatusNote message="No dishes indexed yet — open a few restaurants first so Kensho extracts and embeds their menus, then dish search lights up." />
        )}
      </div>
    </>
  )
}

function Skeletons({ rows }: { rows?: boolean }) {
  if (rows)
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="skeleton h-16" />
        ))}
      </div>
    )
  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="skeleton h-72" />
      ))}
    </div>
  )
}
