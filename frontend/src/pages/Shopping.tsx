import { motion } from "framer-motion"
import { ExternalLink, Search, ShoppingBag, Star } from "lucide-react"
import { FormEvent, useState } from "react"
import { Button, StatusNote } from "../components/ui"
import { Reveal } from "../components/fx"
import { api } from "../lib/api"
import { money } from "../lib/cn"
import type { Product } from "../lib/types"

const IDEAS = ["noise cancelling headphones under ₹10k", "ergonomic chair", "mechanical keyboard", "running shoes", "espresso machine"]

export function Shopping() {
  const [q, setQ] = useState("")
  const [products, setProducts] = useState<Product[] | null>(null)
  const [status, setStatus] = useState<string>()
  const [loading, setLoading] = useState(false)

  async function run(e?: FormEvent, preset?: string) {
    e?.preventDefault()
    const query = preset ?? q
    if (!query.trim()) return
    if (preset) setQ(preset)
    setLoading(true)
    setStatus(undefined)
    try {
      const r = await api.searchProducts(query, 24)
      setProducts(r.products || [])
      if (r.status !== "ok") setStatus(r.status)
    } catch {
      setStatus("error")
      setProducts([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-36">
      <Reveal>
        <span className="label text-plum">03 · Buy</span>
        <h1 className="mt-3 font-display text-[clamp(2.1rem,6vw,4.6rem)] font-medium leading-[0.98]">
          The best buy, <span className="italic text-plum">found fast.</span>
        </h1>
        <p className="mt-4 max-w-xl text-lg text-ink-soft text-pretty">
          Search products across merchants — real prices, ratings, and links. Kensho surfaces options; you decide where
          to buy.
        </p>
      </Reveal>

      <Reveal delay={0.1} className="mt-8">
        <form onSubmit={run} className="card flex items-center gap-2 p-2 pl-5">
          <Search className="h-5 w-5 text-plum" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="what are you looking for?" className="flex-1 bg-transparent py-3 outline-none placeholder:text-ink-faint" />
          <Button loading={loading} className="bg-plum hover:bg-plum-deep">Search</Button>
        </form>
        <div className="mt-3 flex flex-wrap gap-2">
          {IDEAS.map((s) => (
            <button key={s} onClick={() => run(undefined, s)} className="rounded-full border border-ink-line bg-paper-card/60 px-3 py-1.5 text-xs text-ink-soft transition hover:border-plum hover:text-plum">
              {s}
            </button>
          ))}
        </div>
      </Reveal>

      <div className="mt-10">
        {loading && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => <div key={i} className="skeleton h-72" />)}
          </div>
        )}
        {!loading && status && <StatusNote status={status} />}
        {!loading && products && products.length > 0 && (
          <>
            <p className="label mb-4">{products.length} results</p>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {products.map((p, i) => <ProductCard key={i} p={p} i={i} />)}
            </div>
          </>
        )}
        {!loading && products && products.length === 0 && !status && <p className="py-12 text-center text-ink-faint">Nothing found — try different words.</p>}
      </div>
    </section>
  )
}

function ProductCard({ p, i }: { p: Product; i: number }) {
  return (
    <motion.a
      href={p.link}
      target="_blank"
      rel="noreferrer"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(i * 0.04, 0.4) }}
      whileHover={{ y: -6 }}
      className="card group flex flex-col overflow-hidden"
    >
      <div className="relative flex h-44 items-center justify-center overflow-hidden bg-paper p-4">
        {p.thumbnail ? (
          <img src={p.thumbnail} alt="" className="h-full w-full object-contain transition-transform duration-500 group-hover:scale-105" loading="lazy" />
        ) : (
          <ShoppingBag className="h-10 w-10 text-plum/30" />
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <p className="line-clamp-2 text-sm font-medium leading-snug text-ink">{p.title}</p>
        <div className="mt-2 flex items-center gap-2 text-xs text-ink-faint">
          {p.source && <span className="truncate">{p.source}</span>}
          {p.rating != null && (
            <span className="flex items-center gap-0.5"><Star className="h-3 w-3 fill-saffron-glow text-saffron-glow" />{p.rating}</span>
          )}
        </div>
        <div className="mt-auto flex items-end justify-between pt-3">
          <span className="font-display text-2xl text-plum">{p.price_label || money(p.price)}</span>
          <span className="flex items-center gap-1 text-xs font-semibold text-ink opacity-100 transition sm:opacity-0 sm:group-hover:opacity-100">
            View <ExternalLink className="h-3 w-3" />
          </span>
        </div>
      </div>
    </motion.a>
  )
}
