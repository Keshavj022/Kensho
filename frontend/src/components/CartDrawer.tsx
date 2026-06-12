import { AnimatePresence, motion } from "framer-motion"
import { ExternalLink, Minus, Plus, ShoppingBag, Trash2, X } from "lucide-react"
import { api } from "../lib/api"
import { INR } from "../lib/cn"
import { useCart } from "../state/cart"

/** Always give the diner a path to order — the Google deep link when we have it,
 * otherwise a Google search for the restaurant's online ordering. */
function handoffLink(orderUrl?: string | null, restaurantName?: string): string {
  if (orderUrl) return orderUrl
  if (restaurantName) return `https://www.google.com/search?q=${encodeURIComponent(`order ${restaurantName} online`)}`
  return "https://www.google.com/search?q=order+food+online"
}

export function CartDrawer() {
  const { open, setOpen, lines, restaurantId, restaurantName, orderUrl, total, count, setQty, remove, clear } = useCart()
  const href = handoffLink(orderUrl, restaurantName)

  function handoff() {
    api.track({
      kind: "order",
      restaurant_id: restaurantId,
      restaurant_name: restaurantName,
      payload: { total, items: lines.length, item_names: lines.map((l) => l.name).slice(0, 12) },
    })
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="fixed inset-0 z-[60] bg-ink/40 backdrop-blur-sm"
          />
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-y-0 right-0 z-[61] flex w-[min(92vw,27rem)] flex-col bg-paper shadow-lift"
          >
            <div className="flex items-center justify-between border-b border-ink-line px-6 py-5">
              <div className="min-w-0">
                <p className="label">Your cart</p>
                <h2 className="truncate font-display text-2xl">{restaurantName || "Empty"}</h2>
              </div>
              <button onClick={() => setOpen(false)} className="rounded-full p-2 text-ink-faint hover:bg-ink/5 hover:text-ink" aria-label="Close cart">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4">
              {lines.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-ink-faint">
                  <ShoppingBag className="h-10 w-10" />
                  <p className="max-w-[16rem] text-pretty">
                    Add dishes from a restaurant menu — or use voice ordering — and they'll gather here.
                  </p>
                </div>
              ) : (
                <ul className="space-y-3">
                  {lines.map((l) => (
                    <li key={l.item_id} className="flex items-center gap-3 rounded-2xl border border-ink-line bg-paper-card p-3">
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium text-ink">{l.name}</p>
                        <p className="font-mono text-sm text-ink-faint">
                          {INR(l.price)}
                          {l.price != null && l.qty > 1 && <span className="text-ink-faint/70"> · {INR((l.price || 0) * l.qty)}</span>}
                        </p>
                      </div>
                      <div className="flex items-center gap-1 rounded-full border border-ink-line">
                        <button onClick={() => setQty(l.item_id, l.qty - 1)} className="p-1.5 text-ink-soft hover:text-ink" aria-label="Decrease">
                          <Minus className="h-3.5 w-3.5" />
                        </button>
                        <span className="w-6 text-center font-mono text-sm">{l.qty}</span>
                        <button onClick={() => setQty(l.item_id, l.qty + 1)} className="p-1.5 text-ink-soft hover:text-ink" aria-label="Increase">
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <button onClick={() => remove(l.item_id)} className="p-1.5 text-ink-faint hover:text-saffron" aria-label="Remove">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {lines.length > 0 && (
              <div className="border-t border-ink-line px-6 py-5">
                <div className="mb-4 flex items-end justify-between">
                  <span className="label">{count} items · subtotal</span>
                  <span className="font-display text-3xl">{INR(total)}</span>
                </div>
                <a
                  href={href}
                  target="_blank"
                  rel="noreferrer"
                  onClick={handoff}
                  className="flex w-full items-center justify-center gap-2 rounded-full bg-saffron px-5 py-3.5 font-semibold text-paper-card transition hover:bg-saffron-deep"
                >
                  {orderUrl ? "Hand off to order online" : "Find ordering for this place"} <ExternalLink className="h-4 w-4" />
                </a>
                <div className="mt-3 flex items-center justify-between text-xs text-ink-faint">
                  <button onClick={clear} className="hover:text-saffron">
                    Clear cart
                  </button>
                  <span>Kensho hands off — it never charges you.</span>
                </div>
              </div>
            )}
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
