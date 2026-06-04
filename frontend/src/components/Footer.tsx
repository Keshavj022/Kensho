import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api } from "../lib/api"
import type { Health } from "../lib/types"
import { Mark } from "./Logo"
import { Marquee } from "./fx"

export function Footer() {
  const [health, setHealth] = useState<Health | null>(null)
  useEffect(() => {
    api.health().then(setHealth).catch(() => {})
  }, [])

  return (
    <footer className="relative mt-32 overflow-hidden bg-pine-ink text-paper">
      <div className="border-b border-white/10 py-6">
        <Marquee
          className="text-pine-wash/60"
          items={["見性 · seeing true nature", "eat well", "wander far", "buy wisely", "one assistant, three appetites"].map(
            (t, i) => (
              <span key={i} className="font-display text-2xl italic">
                {t}
              </span>
            ),
          )}
        />
      </div>

      <div className="mx-auto grid max-w-7xl gap-12 px-5 py-16 sm:px-8 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-2.5">
            <Mark className="text-paper" animate={false} />
            <span className="font-display text-3xl font-semibold">Kensho</span>
          </div>
          <p className="mt-4 max-w-xs text-pretty text-pine-wash/70">
            An atlas for taste. Restaurants & menus, travel metasearch, and shopping — guided by one calm assistant.
          </p>
        </div>

        <FooterCol
          title="Explore"
          links={[
            ["Eat", "/restaurants"],
            ["Go", "/travel"],
            ["Buy", "/shopping"],
            ["Ask Kensho", "/assistant"],
          ]}
        />
        <FooterCol
          title="Account"
          links={[
            ["Sign in", "/auth"],
            ["Register", "/auth"],
          ]}
        />
        <div>
          <p className="label text-pine-wash/50">System</p>
          <div className="mt-4 space-y-2 font-mono text-xs text-pine-wash/70">
            {health ? (
              <>
                <div>
                  v{health.version} · <span className="text-saffron-glow">{health.status}</span>
                </div>
                {Object.entries(health.subsystems).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-2">
                    <span className={v === "ok" ? "text-saffron-glow" : "text-pine-wash/40"}>●</span>
                    {k}: {v}
                  </div>
                ))}
              </>
            ) : (
              <div className="text-pine-wash/40">backend offline</div>
            )}
          </div>
        </div>
      </div>

      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 border-t border-white/10 px-5 py-6 text-xs text-pine-wash/50 sm:flex-row sm:px-8">
        <span>© {new Date().getFullYear()} Kensho · search-only, no bookings or payments</span>
        <span className="font-mono">LangChain · LangGraph · Gemini · SerpApi</span>
      </div>
    </footer>
  )
}

function FooterCol({ title, links }: { title: string; links: [string, string][] }) {
  return (
    <div>
      <p className="label text-pine-wash/50">{title}</p>
      <ul className="mt-4 space-y-2.5">
        {links.map(([label, to]) => (
          <li key={label + to}>
            <Link to={to} className="link-grow text-pine-wash/80 hover:text-paper">
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
