import { motion } from "framer-motion"
import { ArrowRight, Clock, LocateFixed, Soup } from "lucide-react"
import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api } from "../lib/api"
import { cn } from "../lib/cn"
import type { Restaurant } from "../lib/types"
import { useAuth } from "../state/auth"
import { Reveal } from "./fx"
import { PriceTag, Stars } from "./ui"

function dietForSearch(t?: string): string | undefined {
  if (t === "vegan") return "vegan"
  if (t === "vegetarian" || t === "eggetarian" || t === "jain") return "vegetarian"
  return undefined
}

/** Home-page rail of restaurants near the signed-in diner's saved location. */
export function NearYou() {
  const { user, onboarded, profile } = useAuth()
  const [items, setItems] = useState<Restaurant[] | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!user || !onboarded) return
    const hasCoords = profile?.lat != null && profile?.lng != null
    if (!hasCoords && !profile?.location) return
    setLoading(true)
    api
      .searchRestaurants({
        lat: profile?.lat ?? undefined,
        lng: profile?.lng ?? undefined,
        location: profile?.location || undefined,
        radius: hasCoords ? 6000 : undefined,
        dietary: dietForSearch(profile?.dietary_type),
        min_rating: 4.0,
        max_results: 10,
      })
      .then((r) => setItems(r.status === "ok" ? r.restaurants : []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [user, onboarded, profile])

  if (!user || !onboarded) return null
  if (!loading && (!items || items.length === 0)) return null

  const where = profile?.location || "you"
  return (
    <section className="mx-auto max-w-7xl px-5 py-20 sm:px-8">
      <Reveal className="mb-8 flex items-end justify-between gap-4">
        <div>
          <span className="label inline-flex items-center gap-1.5 text-saffron">
            <LocateFixed className="h-3.5 w-3.5" /> Near you
          </span>
          <h2 className="mt-3 font-display text-4xl leading-tight sm:text-5xl">
            Tastes around <span className="italic text-saffron">{where}</span>.
          </h2>
        </div>
        <Link to="/restaurants" className="hidden shrink-0 items-center gap-2 text-ink-soft link-grow hover:text-ink sm:flex">
          See all <ArrowRight className="h-4 w-4" />
        </Link>
      </Reveal>

      <div className="-mx-5 flex snap-x gap-5 overflow-x-auto px-5 pb-4 sm:-mx-2 sm:px-2 [&::-webkit-scrollbar]:hidden" style={{ scrollbarWidth: "none" }}>
        {loading
          ? Array.from({ length: 5 }).map((_, i) => <div key={i} className="skeleton h-64 w-72 shrink-0 snap-start" />)
          : items!.map((r, i) => <NearCard key={r.id} r={r} i={i} />)}
        {!loading && (
          <Link to="/restaurants" className="flex w-44 shrink-0 snap-start flex-col items-center justify-center gap-2 rounded-xl2 border border-dashed border-ink-line text-ink-soft transition hover:border-saffron hover:text-saffron">
            <ArrowRight className="h-6 w-6" />
            <span className="text-sm font-medium">More</span>
          </Link>
        )}
      </div>
    </section>
  )
}

function NearCard({ r, i }: { r: Restaurant; i: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(i * 0.06, 0.5), ease: [0.16, 1, 0.3, 1] }}
      className="w-72 shrink-0 snap-start"
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
          <div className="p-4">
            <h3 className="line-clamp-1 font-display text-lg leading-snug">{r.name}</h3>
            <div className="mt-1.5 flex items-center justify-between">
              <Stars value={r.rating} count={r.rating_count} />
              <PriceTag level={r.price_level} range={r.price_range} />
            </div>
            {r.address && <p className="mt-1 line-clamp-1 text-xs text-ink-faint">{r.address}</p>}
          </div>
        </motion.div>
      </Link>
    </motion.div>
  )
}
