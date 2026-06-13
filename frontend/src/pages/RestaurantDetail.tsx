import { AnimatePresence, motion } from "framer-motion"
import { ArrowLeft, ExternalLink, Globe, Mic, Phone, Plus, RefreshCw, ScanLine, Send, Square } from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"
import { Link, useLocation, useParams } from "react-router-dom"
import { PriceTag, Spinner, Stars, StatusNote } from "../components/ui"
import { api } from "../lib/api"
import { INR, cn } from "../lib/cn"
import { getSessionId } from "../lib/session"
import { useCart } from "../state/cart"
import type { Menu, MenuItem, Restaurant, VoiceOrder } from "../lib/types"

export function RestaurantDetail() {
  const { placeId = "" } = useParams()
  const loc = useLocation()
  const seed = (loc.state as { restaurant?: Restaurant } | null)?.restaurant
  const [r, setR] = useState<Restaurant | undefined>(seed)
  const [menu, setMenu] = useState<Menu | null>(null)
  const [photos, setPhotos] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [rescanning, setRescanning] = useState(false)
  const cart = useCart()

  const fetchMenu = useCallback(
    (refresh: boolean) => {
      setLoading(true)
      setRescanning(refresh)
      api
        .menu(placeId, seed?.name || "", refresh)
        .then((m) => {
          setMenu(m)
          if (m.order_online_url) cart.setRestaurant(placeId, m.restaurant_name, m.order_online_url)
        })
        .catch(() => setMenu({ status: "error" } as Menu))
        .finally(() => {
          setLoading(false)
          setRescanning(false)
        })
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [placeId],
  )

  useEffect(() => {
    if (!seed) api.restaurant(placeId).then((d) => d?.status === "ok" && setR(d)).catch(() => {})
    setMenu(null)
    setPhotos([])
    fetchMenu(false)
    api.restaurantPhotos(placeId, 12).then((p) => setPhotos(p.photos || [])).catch(() => {})
    api.track({
      kind: "view",
      restaurant_id: placeId,
      restaurant_name: seed?.name,
      cuisine: seed?.primary_type || seed?.types?.[0],
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [placeId])

  const name = r?.name || menu?.restaurant_name || "Restaurant"

  return (
    <section className="mx-auto max-w-6xl px-5 pb-28 pt-24 sm:px-8 sm:pt-32">
      <Link to="/restaurants" className="inline-flex items-center gap-2 text-sm text-ink-soft link-grow hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> All restaurants
      </Link>

      {/* header */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mt-6 grid gap-8 lg:grid-cols-[1.4fr_1fr]">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <Stars value={r?.rating} count={r?.rating_count} />
            <PriceTag level={r?.price_level} range={r?.price_range} />
            {r?.open_now != null && (
              <span className={cn("rounded-full px-2.5 py-0.5 font-mono text-[0.6rem] uppercase", r.open_now ? "bg-pine text-paper-card" : "bg-ink/70 text-paper-card")}>
                {r.open_now ? "open now" : "closed"}
              </span>
            )}
          </div>
          <h1 className="mt-3 font-display text-[clamp(2rem,5.5vw,4rem)] font-medium leading-[0.95]">{name}</h1>
          {r?.address && <p className="mt-3 text-ink-soft">{r.address}</p>}
          <div className="mt-4 flex flex-wrap gap-2">
            {r?.types?.slice(0, 4).map((t) => (
              <span key={t} className="pill">{t}</span>
            ))}
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            {r?.phone && (
              <a href={`tel:${r.phone}`} className="inline-flex items-center gap-2 rounded-full border border-ink-line px-4 py-2 text-sm hover:border-ink/40">
                <Phone className="h-4 w-4" /> Call
              </a>
            )}
            {r?.website && (
              <a href={r.website} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full border border-ink-line px-4 py-2 text-sm hover:border-ink/40">
                <Globe className="h-4 w-4" /> Website
              </a>
            )}
            {menu?.order_online_url && (
              <a href={menu.order_online_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-paper-card hover:bg-saffron">
                Order online <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
        </div>

        <div className="relative h-56 overflow-hidden rounded-xl2 border border-ink-line bg-paper-deep">
          {r?.thumbnail ? (
            <img src={r.thumbnail} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center bg-gradient-to-br from-saffron-wash to-pine-wash">
              <ScanLine className="h-10 w-10 text-saffron/50" />
            </div>
          )}
        </div>
      </motion.div>

      <Gallery photos={photos} />

      <VoiceOrderBar placeId={placeId} restaurantName={name} orderUrl={menu?.order_online_url} />

      {/* menu */}
      <div className="mt-12">
        {loading && <MenuLoading rescan={rescanning} />}
        {!loading && menu && !menu.sections?.length && (menu.source === "web" || menu.status === "not_configured" || menu.status === "error") && (
          <div className="space-y-3">
            <StatusNote
              status={menu.status === "not_configured" ? "not_configured" : undefined}
              message={
                menu.status === "not_configured"
                  ? undefined
                  : menu.note ||
                    "No readable menu was found for this place — the order-online link above is your fastest path."
              }
            />
            <button
              onClick={() => fetchMenu(true)}
              className="inline-flex items-center gap-2 rounded-full border border-ink-line px-4 py-2 text-sm font-medium text-ink-soft transition hover:border-saffron hover:text-saffron"
            >
              <RefreshCw className="h-3.5 w-3.5" /> Re-scan menu
            </button>
          </div>
        )}
        {!loading && menu && menu.sections?.length > 0 && <MenuView menu={menu} placeId={placeId} />}
      </div>
    </section>
  )
}

function Gallery({ photos }: { photos: string[] }) {
  if (!photos.length) return null
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8">
      <div className="-mx-5 flex snap-x gap-3 overflow-x-auto px-5 pb-2 sm:-mx-2 sm:px-2 [&::-webkit-scrollbar]:hidden" style={{ scrollbarWidth: "none" }}>
        {photos.map((src, i) => (
          <motion.div
            key={src + i}
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: Math.min(i * 0.05, 0.4) }}
            className="h-40 w-56 shrink-0 snap-start overflow-hidden rounded-xl2 border border-ink-line bg-paper-deep sm:h-48 sm:w-64"
          >
            <img src={src} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-700 hover:scale-105" />
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

function MenuView({ menu, placeId }: { menu: Menu; placeId: string }) {
  const cart = useCart()
  const [active, setActive] = useState(menu.sections[0]?.name)

  return (
    <div className="grid gap-8 lg:grid-cols-[200px_1fr]">
      <aside className="hidden lg:block">
        <div className="sticky top-28">
          <div className="mb-4 flex items-center gap-2">
            <span className="pill !text-saffron">{menu.source}</span>
            <span className="font-mono text-xs text-ink-faint">{menu.sections.reduce((a, s) => a + s.items.length, 0)} items</span>
          </div>
          <nav className="space-y-1">
            {menu.sections.map((s) => (
              <a
                key={s.name}
                href={`#sec-${s.name}`}
                onClick={() => setActive(s.name)}
                className={cn("block rounded-lg px-3 py-1.5 text-sm transition", active === s.name ? "bg-ink text-paper-card" : "text-ink-soft hover:bg-ink/5")}
              >
                {s.name}
              </a>
            ))}
          </nav>
        </div>
      </aside>

      <div className="space-y-12">
        {menu.sections.map((s) => (
          <div key={s.name} id={`sec-${s.name}`} className="scroll-mt-28">
            <div className="mb-5 flex items-baseline gap-3 border-b border-ink-line pb-2">
              <h2 className="font-display text-2xl">{s.name}</h2>
              <span className="font-mono text-xs text-ink-faint">{s.items.length}</span>
            </div>
            <div className="space-y-2">
              {s.items.map((it) => (
                <ItemRow key={it.id} it={it} onAdd={() => { cart.setRestaurant(placeId, menu.restaurant_name, menu.order_online_url); cart.add({ item_id: it.id, name: it.name, price: it.price }); cart.setOpen(true) }} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ItemRow({ it, onAdd }: { it: MenuItem; onAdd: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: "-5%" }}
      className="group flex items-start gap-4 rounded-xl px-3 py-3 transition hover:bg-paper-card"
    >
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-ink">{it.name}</span>
          {it.dietary_flags?.map((f) => (
            <span key={f} className="rounded-full bg-pine-wash px-2 py-0.5 font-mono text-[0.58rem] uppercase text-pine">{f}</span>
          ))}
          {it.spice_level && <span className="rounded-full bg-saffron-wash px-2 py-0.5 font-mono text-[0.58rem] uppercase text-saffron-deep">{it.spice_level}</span>}
        </div>
        {it.description && <p className="mt-1 max-w-prose text-sm text-ink-faint text-pretty">{it.description}</p>}
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <span className="font-mono text-pine">{INR(it.price)}</span>
        <button onClick={onAdd} className="flex h-8 w-8 items-center justify-center rounded-full border border-ink-line text-ink transition hover:border-saffron hover:bg-saffron hover:text-paper-card" aria-label={`Add ${it.name}`}>
          <Plus className="h-4 w-4" />
        </button>
      </div>
    </motion.div>
  )
}

function VoiceOrderBar({ placeId, restaurantName, orderUrl }: { placeId: string; restaurantName: string; orderUrl?: string | null }) {
  const cart = useCart()
  const [recording, setRecording] = useState(false)
  const [busy, setBusy] = useState(false)
  const [text, setText] = useState("")
  const [result, setResult] = useState<VoiceOrder | null>(null)
  const [err, setErr] = useState<string>()
  const mr = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])

  async function submit(form: FormData) {
    setBusy(true)
    setErr(undefined)
    try {
      const res = await api.voiceOrder(form)
      setResult(res)
      if (res.status === "ok" && res.cart?.items) {
        cart.setRestaurant(placeId, restaurantName, res.order_online_url ?? orderUrl)
        cart.replaceLines(res.cart.items.map((l) => ({ item_id: l.item_id, name: l.name, price: l.price, qty: l.qty })))
      } else if (res.status !== "ok") {
        setErr(res.message || "That didn't resolve to anything on the menu.")
      }
    } catch {
      setErr("Voice ordering is unavailable right now.")
    } finally {
      setBusy(false)
    }
  }

  function base(extra: (f: FormData) => void) {
    const f = new FormData()
    f.append("place_id", placeId)
    f.append("session_id", getSessionId())
    extra(f)
    return f
  }

  async function startRec() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const rec = new MediaRecorder(stream)
      chunks.current = []
      rec.ondataavailable = (e) => chunks.current.push(e.data)
      rec.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunks.current, { type: "audio/webm" })
        submit(base((f) => f.append("file", blob, "order.webm")))
      }
      rec.start()
      mr.current = rec
      setRecording(true)
    } catch {
      setErr("Microphone access was blocked — type your order instead.")
    }
  }
  function stopRec() {
    mr.current?.stop()
    setRecording(false)
  }

  return (
    <div className="mt-10 card overflow-hidden">
      <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-saffron-wash text-saffron-deep">
            <Mic className="h-5 w-5" />
          </span>
          <div>
            <p className="font-semibold">Order by voice</p>
            <p className="text-sm text-ink-faint">Speak or type — matched only to real menu items.</p>
          </div>
        </div>
        <div className="flex flex-1 items-center gap-2 sm:justify-end">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              if (text.trim()) submit(base((f) => f.append("text", text)))
            }}
            className="flex flex-1 items-center gap-2 rounded-full border border-ink-line bg-paper px-3 sm:max-w-sm"
          >
            <input value={text} onChange={(e) => setText(e.target.value)} placeholder="“two chicken biryani, one paneer tikka”" className="w-full bg-transparent py-2.5 text-sm outline-none placeholder:text-ink-faint" />
            <button type="submit" disabled={busy} className="text-ink-faint hover:text-saffron disabled:opacity-40">
              {busy ? <Spinner className="h-4 w-4" /> : <Send className="h-4 w-4" />}
            </button>
          </form>
          <button
            onClick={recording ? stopRec : startRec}
            className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition", recording ? "animate-pulse bg-saffron text-paper-card" : "bg-ink text-paper-card hover:bg-saffron")}
            aria-label={recording ? "Stop recording" : "Record order"}
          >
            {recording ? <Square className="h-4 w-4" /> : <Mic className="h-5 w-5" />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {(result || err) && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden border-t border-ink-line bg-paper px-5">
            <div className="py-4 text-sm">
              {err && <p className="text-saffron-deep">{err}</p>}
              {result?.transcript && (
                <p className="text-ink-faint">
                  heard: <span className="italic text-ink">“{result.transcript}”</span>
                </p>
              )}
              {result?.confirmation_text && <p className="mt-1 font-medium text-ink">{result.confirmation_text}</p>}
              {result?.matched && result.matched.length > 0 && (
                <button onClick={() => cart.setOpen(true)} className="mt-2 inline-flex items-center gap-1 font-semibold text-saffron link-grow">
                  Review cart →
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function MenuLoading({ rescan }: { rescan?: boolean }) {
  return (
    <div className="card flex flex-col items-center gap-4 px-6 py-16 text-center">
      <Spinner className="h-7 w-7" />
      <div>
        <p className="font-display text-xl">{rescan ? "Re-scanning the menu…" : "Reading the menu…"}</p>
        <p className="mt-1 max-w-sm text-pretty text-sm text-ink-faint">
          Kensho gathers photos, decides which are menus, and extracts items with vision AI. The first read can take a
          moment — after that it's cached, so opening this place again is instant.
        </p>
      </div>
      <div className="mt-2 flex gap-2">
        {["fetch", "classify", "extract", "cache"].map((s, i) => (
          <motion.span
            key={s}
            className="pill"
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.3 }}
          >
            {s}
          </motion.span>
        ))}
      </div>
    </div>
  )
}
