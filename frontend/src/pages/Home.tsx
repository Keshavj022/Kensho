import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, ArrowUpRight, Compass, ScanLine, ShoppingBag, Soup, Sparkles } from "lucide-react"
import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Mark } from "../components/Logo"
import { NearYou } from "../components/NearYou"
import { Magnetic, Marquee, Reveal, Stagger, StaggerItem } from "../components/fx"
import { cn } from "../lib/cn"

const ROTATE = ["eat", "wander", "savour", "buy", "explore"]

const DOMAINS = [
  {
    to: "/restaurants",
    label: "Eat",
    n: "01",
    title: "Restaurants & menus",
    body: "Search places, then read a structured menu Kensho extracts from photos — and order by voice.",
    accent: "bg-saffron text-paper-card",
    tag: "text-saffron",
    icon: Soup,
  },
  {
    to: "/travel",
    label: "Go",
    n: "02",
    title: "Travel metasearch",
    body: "Cheapest flights & stays with the provider, a deep link, and price context — plus day-by-day plans.",
    accent: "bg-pine text-paper-card",
    tag: "text-pine",
    icon: Compass,
  },
  {
    to: "/shopping",
    label: "Buy",
    n: "03",
    title: "Smart shopping",
    body: "Products across merchants with real prices, ratings, and links — find the best buy, fast.",
    accent: "bg-plum text-paper-card",
    tag: "text-plum",
    icon: ShoppingBag,
  },
]

export function Home() {
  return (
    <div className="overflow-hidden">
      <Hero />
      <CuisineStrip />
      <NearYou />
      <Domains />
      <HowItWorks />
      <Keystone />
      <FinalCTA />
    </div>
  )
}

function Hero() {
  const [i, setI] = useState(0)
  const [q, setQ] = useState("")
  const nav = useNavigate()
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x + 1) % ROTATE.length), 2200)
    return () => clearInterval(t)
  }, [])

  return (
    <section className="relative mx-auto max-w-7xl px-5 pb-16 pt-32 sm:px-8 sm:pt-40">
      <div className="pointer-events-none absolute right-[6%] top-28 hidden lg:block">
        <Mark className="h-44 w-44 text-ink/10 animate-floaty" animate={false} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="flex items-center gap-3"
      >
        <span className="pill">見性 · kenshō</span>
        <span className="hidden font-mono text-xs text-ink-faint sm:inline">22.57°N 88.36°E · an atlas for taste</span>
      </motion.div>

      <h1 className="mt-6 max-w-5xl font-display text-[clamp(3rem,9vw,7.5rem)] font-medium leading-[0.92] tracking-[-0.02em] text-balance">
        <Word delay={0.05}>See what to</Word>{" "}
        <span className="relative inline-block">
          <AnimatePresence mode="wait">
            <motion.span
              key={ROTATE[i]}
              initial={{ y: "0.5em", opacity: 0, filter: "blur(8px)" }}
              animate={{ y: 0, opacity: 1, filter: "blur(0px)" }}
              exit={{ y: "-0.5em", opacity: 0, filter: "blur(8px)" }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="inline-block italic text-saffron"
            >
              {ROTATE[i]}
            </motion.span>
          </AnimatePresence>
        </span>
        <br />
        <Word delay={0.12}>before you decide.</Word>
      </h1>

      <Reveal delay={0.2} className="mt-8 max-w-xl text-lg text-ink-soft text-pretty">
        One assistant routes you to three specialists — restaurants &amp; menus, travel metasearch, and shopping. Ask in
        plain words; Kensho figures out the rest.
      </Reveal>

      <Reveal delay={0.3} className="mt-9 max-w-2xl">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            nav("/assistant", { state: { q } })
          }}
          className="group flex items-center gap-2 rounded-full border border-ink-line bg-paper-card/80 p-2 pl-6 shadow-card backdrop-blur transition focus-within:border-saffron"
        >
          <Sparkles className="h-5 w-5 text-saffron" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Best biryani in Kolkata · flights CCU→DEL · headphones under ₹10k"
            className="flex-1 bg-transparent py-2.5 text-ink outline-none placeholder:text-ink-faint"
          />
          <button className="flex items-center gap-2 rounded-full bg-ink px-5 py-3 text-sm font-semibold text-paper-card transition-colors group-focus-within:bg-saffron">
            Ask <ArrowRight className="h-4 w-4" />
          </button>
        </form>
      </Reveal>

      <Stagger className="mt-14 grid max-w-3xl grid-cols-3 gap-6 border-t border-ink-line pt-8" gap={0.12}>
        {[
          ["3", "specialist agents"],
          ["187+", "menu items read"],
          ["0", "bookings · search only"],
        ].map(([v, k]) => (
          <StaggerItem key={k}>
            <div className="font-display text-4xl text-ink sm:text-5xl">{v}</div>
            <div className="label mt-1">{k}</div>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  )
}

function Word({ children, delay }: { children: React.ReactNode; delay: number }) {
  return (
    <motion.span
      className="inline-block"
      initial={{ y: "0.6em", opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay }}
    >
      {children}
    </motion.span>
  )
}

function CuisineStrip() {
  const items = ["Biryani", "Tonkotsu", "Rooftop bars", "Goa", "Tokyo", "Filter coffee", "Thali", "Espresso", "Dim sum", "Kolkata", "Street food"]
  return (
    <div className="border-y border-ink-line bg-paper-deep/60 py-5">
      <Marquee
        items={items.map((t) => (
          <span key={t} className="font-display text-2xl italic text-ink-soft">
            {t}
          </span>
        ))}
      />
    </div>
  )
}

function Domains() {
  return (
    <section className="mx-auto max-w-7xl px-5 py-24 sm:px-8">
      <Reveal className="flex items-end justify-between gap-6">
        <div>
          <span className="label text-saffron">Three appetites</span>
          <h2 className="mt-3 max-w-xl font-display text-4xl leading-tight sm:text-5xl">One question, the right expert.</h2>
        </div>
        <Link to="/assistant" className="hidden shrink-0 items-center gap-2 text-ink-soft link-grow hover:text-ink sm:flex">
          Ask the supervisor <ArrowUpRight className="h-4 w-4" />
        </Link>
      </Reveal>

      <Stagger className="mt-12 grid gap-5 md:grid-cols-3" gap={0.1}>
        {DOMAINS.map((d) => (
          <StaggerItem key={d.to}>
            <Link to={d.to} className="group block h-full">
              <motion.div
                whileHover={{ y: -8 }}
                transition={{ type: "spring", stiffness: 260, damping: 22 }}
                className="card relative flex h-full flex-col overflow-hidden p-7"
              >
                <div className="flex items-center justify-between">
                  <span className={cn("flex h-12 w-12 items-center justify-center rounded-full", d.accent)}>
                    <d.icon className="h-5 w-5" />
                  </span>
                  <span className="font-mono text-xs text-ink-faint">{d.n}</span>
                </div>
                <h3 className="mt-8 font-display text-2xl">
                  <span className={d.tag}>{d.label}.</span> {d.title}
                </h3>
                <p className="mt-3 flex-1 text-ink-soft text-pretty">{d.body}</p>
                <div className="mt-6 flex items-center gap-2 text-sm font-semibold text-ink">
                  Open
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </div>
              </motion.div>
            </Link>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  )
}

function HowItWorks() {
  const steps = [
    ["You ask", "“Vegan dinner near Park Street, then a flight home.”"],
    ["Supervisor routes", "A Gemini router classifies intent and hands off to one specialist."],
    ["Specialist answers", "It calls the right tools — Places, SerpApi, menus — and replies."],
  ]
  return (
    <section className="bg-ink py-24 text-paper">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <Reveal>
          <span className="label text-saffron-glow">How it works</span>
          <h2 className="mt-3 max-w-2xl font-display text-4xl leading-tight sm:text-5xl">
            A calm <span className="italic text-saffron-glow">supervisor</span>, three sharp specialists.
          </h2>
        </Reveal>
        <Stagger className="mt-14 grid gap-px overflow-hidden rounded-xl2 border border-white/10 md:grid-cols-3" gap={0.12}>
          {steps.map(([t, b], i) => (
            <StaggerItem key={t as string} className="bg-pine-ink p-8">
              <span className="font-mono text-sm text-saffron-glow">0{i + 1}</span>
              <h3 className="mt-5 font-display text-2xl">{t}</h3>
              <p className="mt-2 text-pretty text-pine-wash/70">{b}</p>
            </StaggerItem>
          ))}
        </Stagger>
      </div>
    </section>
  )
}

function Keystone() {
  return (
    <section className="mx-auto max-w-7xl px-5 py-24 sm:px-8">
      <div className="grid items-center gap-12 lg:grid-cols-2">
        <Reveal>
          <span className="label text-saffron">The keystone</span>
          <h2 className="mt-3 font-display text-4xl leading-tight sm:text-5xl">
            Menus, read from <span className="italic">photographs.</span>
          </h2>
          <p className="mt-5 max-w-md text-lg text-ink-soft text-pretty">
            For each restaurant, Kensho gathers user-posted photos, decides which ones are menus, and uses Gemini vision
            to extract a structured, multilingual menu — cached, searchable across restaurants, and ready for voice
            ordering.
          </p>
          <div className="mt-7 flex flex-wrap gap-2">
            {["classify", "extract", "cache", "embed", "search dishes"].map((s, i) => (
              <span key={s} className="pill">
                <span className="text-saffron">{i + 1}</span> {s}
              </span>
            ))}
          </div>
          <Link to="/restaurants" className="mt-8 inline-flex items-center gap-2 font-semibold text-ink link-grow">
            Try menu extraction <ArrowRight className="h-4 w-4" />
          </Link>
        </Reveal>

        <Reveal delay={0.15}>
          <div className="card relative overflow-hidden p-6">
            <div className="flex items-center gap-3 border-b border-ink-line pb-4">
              <ScanLine className="h-5 w-5 text-saffron" />
              <span className="label">karim hotel · old delhi</span>
              <span className="ml-auto pill !text-saffron">ocr</span>
            </div>
            <div className="mt-4 space-y-3">
              {[
                ["Mutton Burra", "₹540", ["non-veg"]],
                ["Chicken Jahangiri", "₹420", ["non-veg"]],
                ["Mutton Korma", "₹380", ["spicy"]],
                ["Sheermal", "₹60", ["veg"]],
              ].map(([name, price, flags], i) => (
                <motion.div
                  key={name as string}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.1 + i * 0.08 }}
                  className="flex items-center gap-3 rounded-xl border border-ink-line bg-paper px-4 py-3"
                >
                  <span className="flex-1 font-medium">{name}</span>
                  {(flags as string[]).map((f) => (
                    <span key={f} className="rounded-full bg-saffron-wash px-2 py-0.5 font-mono text-[0.6rem] uppercase text-saffron-deep">
                      {f}
                    </span>
                  ))}
                  <span className="font-mono text-pine">{price}</span>
                </motion.div>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between text-xs text-ink-faint">
              <span className="font-mono">70 items · 7 sections</span>
              <span>cached 30 days</span>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}

function FinalCTA() {
  return (
    <section className="mx-auto max-w-7xl px-5 pb-12 sm:px-8">
      <Reveal>
        <div className="relative overflow-hidden rounded-[2.5rem] bg-saffron px-8 py-20 text-center text-paper-card sm:px-16">
          <div className="pointer-events-none absolute inset-0 opacity-20 [background:radial-gradient(circle_at_20%_20%,#fff,transparent_40%),radial-gradient(circle_at_80%_70%,#fff,transparent_35%)]" />
          <h2 className="relative mx-auto max-w-3xl font-display text-[clamp(2.4rem,6vw,4.5rem)] font-medium leading-[0.95] text-balance">
            Tell Kensho what you're hungry for.
          </h2>
          <Magnetic className="relative mt-10 inline-block">
            <Link
              to="/assistant"
              className="inline-flex items-center gap-2 rounded-full bg-ink px-8 py-4 text-lg font-semibold text-paper-card"
            >
              <Sparkles className="h-5 w-5" /> Start a conversation
            </Link>
          </Magnetic>
        </div>
      </Reveal>
    </section>
  )
}
