import { motion, useInView, type Variants } from "framer-motion"
import { useRef, type ReactNode } from "react"
import { cn } from "../lib/cn"

export function Grain() {
  return <div className="grain" aria-hidden />
}

export const easeExpo = [0.16, 1, 0.3, 1] as const

const revealVariants: Variants = {
  hidden: { opacity: 0, y: 26, filter: "blur(6px)" },
  show: { opacity: 1, y: 0, filter: "blur(0px)" },
}

export function Reveal({
  children,
  delay = 0,
  className,
  as = "div",
  y,
}: {
  children: ReactNode
  delay?: number
  className?: string
  as?: keyof typeof motion
  y?: number
}) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: "-12% 0px" })
  const M = (motion as any)[as]
  return (
    <M
      ref={ref}
      className={className}
      initial="hidden"
      animate={inView ? "show" : "hidden"}
      variants={{
        hidden: { opacity: 0, y: y ?? 26, filter: "blur(6px)" },
        show: { opacity: 1, y: 0, filter: "blur(0px)" },
      }}
      transition={{ duration: 0.85, ease: easeExpo, delay }}
    >
      {children}
    </M>
  )
}

export function Stagger({ children, className, gap = 0.08 }: { children: ReactNode; className?: string; gap?: number }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: "-10% 0px" })
  return (
    <motion.div
      ref={ref}
      className={className}
      initial="hidden"
      animate={inView ? "show" : "hidden"}
      variants={{ show: { transition: { staggerChildren: gap } } }}
    >
      {children}
    </motion.div>
  )
}
export function StaggerItem({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div className={className} variants={revealVariants} transition={{ duration: 0.7, ease: easeExpo }}>
      {children}
    </motion.div>
  )
}

export function Marquee({ items, className, reverse }: { items: ReactNode[]; className?: string; reverse?: boolean }) {
  const row = [...items, ...items]
  return (
    <div className={cn("mask-fade-x overflow-hidden", className)}>
      <div
        className="flex w-max animate-marquee gap-10"
        style={reverse ? { animationDirection: "reverse" } : undefined}
      >
        {row.map((it, i) => (
          <div key={i} className="flex shrink-0 items-center gap-10">
            {it}
            <span className="text-saffron">✦</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function Magnetic({ children, className, strength = 0.4 }: { children: ReactNode; className?: string; strength?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  return (
    <motion.div
      ref={ref}
      className={cn("inline-block", className)}
      onMouseMove={(e) => {
        const el = ref.current
        if (!el) return
        const r = el.getBoundingClientRect()
        const x = (e.clientX - r.left - r.width / 2) * strength
        const y = (e.clientY - r.top - r.height / 2) * strength
        el.style.transform = `translate(${x}px, ${y}px)`
      }}
      onMouseLeave={() => {
        if (ref.current) ref.current.style.transform = "translate(0,0)"
      }}
      style={{ transition: "transform 0.4s cubic-bezier(0.16,1,0.3,1)" }}
    >
      {children}
    </motion.div>
  )
}
