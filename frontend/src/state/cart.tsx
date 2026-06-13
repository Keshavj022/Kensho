import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"

export interface CartLine {
  item_id: string
  name: string
  price?: number | null
  qty: number
}
export interface CartState {
  restaurantId?: string
  restaurantName?: string
  orderUrl?: string | null
  lines: CartLine[]
}

interface CartCtx extends CartState {
  open: boolean
  setOpen: (o: boolean) => void
  count: number
  total: number
  setRestaurant: (id: string, name: string, orderUrl?: string | null) => void
  add: (line: Omit<CartLine, "qty">, qty?: number) => void
  setQty: (item_id: string, qty: number) => void
  remove: (item_id: string) => void
  clear: () => void
  replaceLines: (lines: CartLine[]) => void
}

const Ctx = createContext<CartCtx>(null as unknown as CartCtx)
const KEY = "kensho.cart"

function loadCart(): CartState {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) || "null")
    if (raw && typeof raw === "object" && Array.isArray(raw.lines)) {
      const lines: CartLine[] = (raw.lines as Partial<CartLine>[])
        .filter((l) => l && typeof l.item_id === "string" && typeof l.name === "string")
        .map((l) => ({ item_id: l.item_id as string, name: l.name as string, price: l.price ?? null, qty: Math.max(1, Number(l.qty) || 1) }))
      return { ...(raw as CartState), lines }
    }
  } catch {}
  return { lines: [] }
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<CartState>(loadCart)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(state))
  }, [state])

  const setRestaurant = (id: string, name: string, orderUrl?: string | null) =>
    setState((s) =>
      s.restaurantId === id ? { ...s, restaurantName: name, orderUrl } : { restaurantId: id, restaurantName: name, orderUrl, lines: [] },
    )

  const add: CartCtx["add"] = (line, qty = 1) =>
    setState((s) => {
      const existing = s.lines.find((l) => l.item_id === line.item_id)
      const lines = existing
        ? s.lines.map((l) => (l.item_id === line.item_id ? { ...l, qty: l.qty + qty } : l))
        : [...s.lines, { ...line, qty }]
      return { ...s, lines }
    })

  // An empty cart drops the restaurant context too, so the drawer reads "Empty".
  const withLines = (s: CartState, lines: CartLine[]): CartState => (lines.length ? { ...s, lines } : { lines: [] })

  const setQty: CartCtx["setQty"] = (item_id, qty) =>
    setState((s) =>
      withLines(s, qty <= 0 ? s.lines.filter((l) => l.item_id !== item_id) : s.lines.map((l) => (l.item_id === item_id ? { ...l, qty } : l))),
    )

  const remove: CartCtx["remove"] = (item_id) => setState((s) => withLines(s, s.lines.filter((l) => l.item_id !== item_id)))
  const clear = () => setState({ lines: [] })
  const replaceLines: CartCtx["replaceLines"] = (lines) => setState((s) => withLines(s, lines))

  const count = useMemo(() => state.lines.reduce((a, l) => a + l.qty, 0), [state.lines])
  const total = useMemo(() => state.lines.reduce((a, l) => a + (l.price || 0) * l.qty, 0), [state.lines])

  return (
    <Ctx.Provider
      value={{ ...state, open, setOpen, count, total, setRestaurant, add, setQty, remove, clear, replaceLines }}
    >
      {children}
    </Ctx.Provider>
  )
}

export const useCart = () => useContext(Ctx)
