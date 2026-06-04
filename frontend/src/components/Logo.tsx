import { motion } from "framer-motion"
import { cn } from "../lib/cn"

/** The Kensho mark — a brushy enso (見性, "seeing true nature") with a spice dot. */
export function Mark({ className, animate = true }: { className?: string; animate?: boolean }) {
  return (
    <svg viewBox="0 0 48 48" className={cn("h-8 w-8", className)} fill="none" aria-hidden>
      <motion.path
        d="M24 5.5C13.5 4 5.5 12 5.5 23.5 5.5 35 13.5 43 24 43c8.7 0 16-5.6 18-14"
        stroke="currentColor"
        strokeWidth="3.4"
        strokeLinecap="round"
        initial={animate ? { pathLength: 0, opacity: 0 } : false}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1] }}
      />
      <motion.circle
        cx="36.5"
        cy="13"
        r="4.2"
        fill="#E0531F"
        initial={animate ? { scale: 0 } : false}
        animate={{ scale: 1 }}
        transition={{ delay: 0.9, type: "spring", stiffness: 320, damping: 14 }}
      />
    </svg>
  )
}

export function Logo({ className, mono }: { className?: string; mono?: boolean }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <Mark className={mono ? "text-ink" : "text-ink"} />
      <span className="font-display text-2xl font-semibold leading-none tracking-tight text-ink">
        Kensho
      </span>
    </div>
  )
}
