import { Link } from "react-router-dom"
import { Mark } from "./Logo"
import { Marquee } from "./fx"

export function Footer() {
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
            An atlas for taste. Restaurants &amp; menus, travel metasearch, and shopping — guided by one calm assistant
            that learns what you love.
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
          title="Your space"
          links={[
            ["Dashboard", "/dashboard"],
            ["Profile", "/profile"],
            ["Sign in", "/auth"],
          ]}
        />
        <div>
          <p className="label text-pine-wash/50">The promise</p>
          <ul className="mt-4 space-y-2.5 text-sm text-pine-wash/70">
            <li>Menus read from real photos</li>
            <li>Cheapest option, the seller, a link</li>
            <li>Search &amp; metasearch — never a booking or charge</li>
            <li>Your taste profile stays yours</li>
          </ul>
        </div>
      </div>

      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 border-t border-white/10 px-5 py-6 text-xs text-pine-wash/50 sm:flex-row sm:px-8">
        <span>© {new Date().getFullYear()} Kensho · search-only, no bookings or payments</span>
        <span className="font-display italic text-pine-wash/60">See what to eat, before you decide.</span>
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
