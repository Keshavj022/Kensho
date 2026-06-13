import { motion } from "framer-motion"
import { ArrowRight, Clock, Compass, History, Search, ShoppingBag, Soup, Sparkles, Store, Utensils, type LucideIcon } from "lucide-react"
import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Reveal } from "../components/fx"
import { PriceTag, Stars } from "../components/ui"
import { api } from "../lib/api"
import { INR, cn } from "../lib/cn"
import type { Dashboard as DashboardData, Dish, Restaurant } from "../lib/types"
import { useAuth } from "../state/auth"

export function Dashboard() {
  const { user, profile } = useAuth()
  const [data, setData] = useState<DashboardData | null>(null)
  const [recRestaurants, setRecRestaurants] = useState<Restaurant[] | null>(null)
  const [recDishes, setRecDishes] = useState<Dish[] | null>(null)

  useEffect(() => {
    api.dashboard().then(setData).catch(() => setData(null))
    api
      .recommendations({ lat: profile?.lat, lng: profile?.lng, location: profile?.location, limit: 12 })
      .then((r) => {
        setRecRestaurants(r.restaurants?.restaurants ?? [])
        setRecDishes(r.dishes?.dishes ?? [])
      })
      .catch(() => {
        setRecRestaurants([])
        setRecDishes([])
      })
  }, [profile])

  const name = profile?.name || user?.email?.split("@")[0] || "there"
  const counts = data?.counts

  return (
    <section className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32">
      <Reveal>
        <span className="label text-saffron">Your space</span>
        <h1 className="mt-3 font-display text-[clamp(2rem,6vw,4.2rem)] font-medium leading-[0.95]">
          Welcome back, <span className="italic text-saffron">{name}.</span>
        </h1>
        <p className="mt-4 max-w-xl text-lg text-ink-soft text-pretty">
          Everything Kensho has learned about your taste — recent searches, the places you opened, your orders, and what
          to try next.
        </p>
      </Reveal>

      {/* stat tiles */}
      <div className="mt-10 grid gap-4 sm:grid-cols-3">
        <StatTile icon={Search} label="Searches" value={counts?.searches} tone="saffron" />
        <StatTile icon={Store} label="Places opened" value={counts?.views} tone="pine" />
        <StatTile icon={Utensils} label="Orders started" value={counts?.orders} tone="plum" />
      </div>

      {/* quick actions */}
      <div className="mt-6 grid gap-3 sm:grid-cols-4">
        <QuickAction to="/restaurants" icon={Soup} label="Eat" tone="bg-saffron" />
        <QuickAction to="/travel" icon={Compass} label="Go" tone="bg-pine" />
        <QuickAction to="/shopping" icon={ShoppingBag} label="Buy" tone="bg-plum" />
        <QuickAction to="/assistant" icon={Sparkles} label="Ask" tone="bg-ink" />
      </div>

      {/* recommended restaurants */}
      <Rail
        title="Recommended for you"
        hint="From your taste profile, searches & orders"
        empty="Search a few places and your picks will appear here."
        loading={recRestaurants === null}
        count={recRestaurants?.length ?? 0}
      >
        {recRestaurants?.map((r, i) => <RecRestaurant key={r.id} r={r} i={i} />)}
      </Rail>

      {/* recommended dishes */}
      {recDishes && recDishes.length > 0 && (
        <Rail title="Dishes you'll love" hint="Matched across menus Kensho has read" count={recDishes.length}>
          {recDishes.map((d, i) => <RecDish key={d.id} d={d} i={i} />)}
        </Rail>
      )}

      {/* activity */}
      <div className="mt-16 grid gap-8 lg:grid-cols-3">
        <ActivityCol title="Recent searches" icon={History}>
          {data?.recent_searches?.length ? (
            data.recent_searches.map((s) => (
              <SearchRow key={s.id} query={s.query || ""} />
            ))
          ) : (
            <Empty>No searches yet.</Empty>
          )}
        </ActivityCol>
        <ActivityCol title="Places you opened" icon={Store}>
          {data?.recent_views?.length ? (
            data.recent_views.map((v) => (
              <Link key={v.id} to={`/restaurants/${encodeURIComponent(v.restaurant_id || "")}`} className="block rounded-xl px-3 py-2.5 text-sm transition hover:bg-ink/5">
                <span className="font-medium text-ink">{v.restaurant_name || "Restaurant"}</span>
                {v.cuisine && <span className="ml-2 text-xs text-ink-faint">{v.cuisine}</span>}
              </Link>
            ))
          ) : (
            <Empty>Open a restaurant to see it here.</Empty>
          )}
        </ActivityCol>
        <ActivityCol title="Orders started" icon={Utensils}>
          {data?.recent_orders?.length ? (
            data.recent_orders.map((o) => (
              <div key={o.id} className="rounded-xl px-3 py-2.5 text-sm">
                <span className="font-medium text-ink">{o.restaurant_name || "Order"}</span>
                {o.payload?.total != null && <span className="ml-2 font-mono text-xs text-pine">{INR(o.payload.total)}</span>}
              </div>
            ))
          ) : (
            <Empty>Build a cart and hand off to order.</Empty>
          )}
        </ActivityCol>
      </div>
    </section>
  )
}

function StatTile({ icon: Icon, label, value, tone }: { icon: LucideIcon; label: string; value?: number; tone: "saffron" | "pine" | "plum" }) {
  const bg = { saffron: "bg-saffron-wash text-saffron-deep", pine: "bg-pine-wash text-pine", plum: "bg-plum/10 text-plum" }[tone]
  return (
    <div className="card flex items-center gap-4 p-5">
      <span className={cn("flex h-12 w-12 items-center justify-center rounded-full", bg)}>
        <Icon className="h-5 w-5" />
      </span>
      <div>
        <div className="font-display text-3xl text-ink">{value ?? "—"}</div>
        <div className="label">{label}</div>
      </div>
    </div>
  )
}

function QuickAction({ to, icon: Icon, label, tone }: { to: string; icon: LucideIcon; label: string; tone: string }) {
  return (
    <Link to={to} className="group">
      <motion.div whileHover={{ y: -4 }} className="card flex items-center justify-between p-4">
        <span className="flex items-center gap-3">
          <span className={cn("flex h-9 w-9 items-center justify-center rounded-full text-paper-card", tone)}>
            <Icon className="h-4 w-4" />
          </span>
          <span className="font-semibold">{label}</span>
        </span>
        <ArrowRight className="h-4 w-4 text-ink-faint transition-transform group-hover:translate-x-1" />
      </motion.div>
    </Link>
  )
}

function Rail({
  title,
  hint,
  empty,
  loading,
  count,
  children,
}: {
  title: string
  hint?: string
  empty?: string
  loading?: boolean
  count: number
  children: React.ReactNode
}) {
  return (
    <div className="mt-16">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl leading-tight sm:text-4xl">{title}</h2>
          {hint && <p className="mt-1 text-sm text-ink-faint">{hint}</p>}
        </div>
      </div>
      {loading ? (
        <div className="-mx-5 flex gap-5 overflow-hidden px-5 sm:-mx-2 sm:px-2">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-64 w-72 shrink-0" />)}
        </div>
      ) : count === 0 ? (
        empty ? <p className="rounded-2xl border border-dashed border-ink-line px-5 py-10 text-center text-ink-faint">{empty}</p> : null
      ) : (
        <div className="-mx-5 flex snap-x gap-5 overflow-x-auto px-5 pb-4 sm:-mx-2 sm:px-2 [&::-webkit-scrollbar]:hidden" style={{ scrollbarWidth: "none" }}>
          {children}
        </div>
      )}
    </div>
  )
}

function RecRestaurant({ r, i }: { r: Restaurant; i: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(i * 0.05, 0.4) }}
      className="w-72 shrink-0 snap-start"
    >
      <Link to={`/restaurants/${encodeURIComponent(r.id)}`} state={{ restaurant: r }} className="group block">
        <motion.div whileHover={{ y: -6 }} className="card h-full overflow-hidden">
          <div className="relative h-36 overflow-hidden bg-paper-deep">
            {r.thumbnail ? (
              <img src={r.thumbnail} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" />
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
          <div className="p-4">
            <h3 className="line-clamp-1 font-display text-lg leading-snug">{r.name}</h3>
            <div className="mt-1.5 flex items-center justify-between">
              <Stars value={r.rating} count={r.rating_count} />
              <PriceTag level={r.price_level} range={r.price_range} />
            </div>
            {r.reason && <p className="mt-2 line-clamp-1 text-xs font-medium text-saffron">{r.reason}</p>}
          </div>
        </motion.div>
      </Link>
    </motion.div>
  )
}

function RecDish({ d, i }: { d: Dish; i: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(i * 0.05, 0.4) }}
      className="w-64 shrink-0 snap-start"
    >
      <Link to={`/restaurants/${encodeURIComponent(d.restaurant_id)}`} className="card block h-full p-5 transition hover:border-saffron">
        <div className="flex h-full flex-col">
          <Soup className="h-5 w-5 text-saffron" />
          <h3 className="mt-3 font-display text-lg leading-snug">{d.name}</h3>
          <p className="mt-1 line-clamp-1 text-sm text-ink-faint">{d.restaurant_name}</p>
          <div className="mt-auto flex items-center justify-between pt-4">
            <span className="font-mono text-pine">{INR(d.price)}</span>
            {d.reason && <span className="line-clamp-1 text-[0.65rem] font-medium text-saffron">{d.reason}</span>}
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

function ActivityCol({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-4 w-4 text-saffron" />
        <span className="label">{title}</span>
      </div>
      <div className="space-y-1">{children}</div>
    </div>
  )
}

function SearchRow({ query }: { query: string }) {
  const nav = useNavigate()
  return (
    <button
      onClick={() => nav("/assistant", { state: { q: query } })}
      className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm transition hover:bg-ink/5"
    >
      <span className="line-clamp-1 text-ink">{query}</span>
      <ArrowRight className="h-3.5 w-3.5 shrink-0 text-ink-faint" />
    </button>
  )
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="px-3 py-4 text-sm text-ink-faint">{children}</p>
}
