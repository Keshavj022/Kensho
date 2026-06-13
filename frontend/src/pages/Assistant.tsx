import { Compass, ShoppingBag, Soup } from "lucide-react"
import { useLocation } from "react-router-dom"
import { Chat } from "../components/Chat"
import { Reveal } from "../components/fx"

const CAPS = [
  { icon: Soup, tone: "text-saffron", t: "Eat", d: "find places, read menus, search dishes" },
  { icon: Compass, tone: "text-pine", t: "Go", d: "cheapest flights, hotels, day-by-day plans" },
  { icon: ShoppingBag, tone: "text-plum", t: "Buy", d: "products, prices, merchants, ratings" },
]

export function Assistant() {
  const loc = useLocation()
  const initial = (loc.state as { q?: string } | null)?.q

  return (
    <section className="mx-auto max-w-7xl px-5 pb-24 pt-28 sm:px-8 sm:pt-36">
      <div className="grid items-start gap-12 lg:grid-cols-[0.85fr_1.15fr]">
        <Reveal className="lg:sticky lg:top-28">
          <span className="label text-saffron">The assistant</span>
          <h1 className="mt-3 font-display text-[clamp(2.1rem,6vw,4.5rem)] font-medium leading-[0.95]">
            Ask Kensho <span className="italic text-saffron">anything.</span>
          </h1>
          <p className="mt-5 max-w-md text-lg text-ink-soft text-pretty">
            One conversation, three specialists. The supervisor reads your intent and hands off to the right expert —
            then replies in plain language.
          </p>
          <div className="mt-8 space-y-3">
            {CAPS.map((c) => (
              <div key={c.t} className="flex items-center gap-4 rounded-2xl border border-ink-line bg-paper-card/60 px-4 py-3">
                <c.icon className={`h-5 w-5 ${c.tone}`} />
                <div>
                  <span className="font-semibold">{c.t}</span>
                  <span className="ml-2 text-sm text-ink-faint">{c.d}</span>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-6 font-mono text-xs text-ink-faint">
            Conversations persist by thread · ↺ starts a fresh one.
          </p>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="card p-4 sm:p-6">
            <Chat variant="page" initial={initial} />
          </div>
        </Reveal>
      </div>
    </section>
  )
}
