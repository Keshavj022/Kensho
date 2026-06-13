import { motion } from "framer-motion"
import { Loader2, Star } from "lucide-react"
import {
  forwardRef,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react"
import { cn } from "../lib/cn"

type Variant = "ink" | "spice" | "outline" | "ghost"
const variants: Record<Variant, string> = {
  ink: "bg-ink text-paper-card hover:bg-ink/90",
  spice: "bg-saffron text-paper-card hover:bg-saffron-deep",
  outline: "border border-ink/25 text-ink hover:border-ink hover:bg-ink/5",
  ghost: "text-ink hover:bg-ink/5",
}

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; loading?: boolean; icon?: ReactNode }
>(({ className, variant = "ink", loading, icon, children, disabled, ...props }, ref) => (
  <motion.button
    ref={ref}
    whileTap={{ scale: 0.97 }}
    disabled={disabled || loading}
    className={cn(
      "inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold tracking-tight",
      "transition-colors duration-300 disabled:cursor-not-allowed disabled:opacity-50",
      variants[variant],
      className,
    )}
    {...(props as any)}
  >
    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
    {children}
  </motion.button>
))
Button.displayName = "Button"

export const Spinner = ({ className }: { className?: string }) => (
  <Loader2 className={cn("h-5 w-5 animate-spin text-saffron", className)} />
)

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "w-full rounded-xl border border-ink-line bg-paper-card/80 px-4 py-3 text-ink placeholder:text-ink-faint",
        "outline-none transition focus:border-saffron focus:bg-paper-card",
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = "Input"

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "w-full resize-none rounded-xl border border-ink-line bg-paper-card/80 px-4 py-3 text-ink placeholder:text-ink-faint",
        "outline-none transition focus:border-saffron focus:bg-paper-card",
        className,
      )}
      {...props}
    />
  ),
)
Textarea.displayName = "Textarea"

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "w-full appearance-none rounded-xl border border-ink-line bg-paper-card/80 px-4 py-3 text-ink",
        "outline-none transition focus:border-saffron focus:bg-paper-card",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  ),
)
Select.displayName = "Select"

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="block">
      <span className="label mb-1.5 block">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-ink-faint">{hint}</span>}
    </label>
  )
}

export function Stars({ value, count }: { value?: number | null; count?: number | null }) {
  if (value == null) return null
  return (
    <span className="inline-flex items-center gap-1 font-mono text-sm text-ink-soft">
      <Star className="h-3.5 w-3.5 fill-saffron-glow text-saffron-glow" />
      {value.toFixed(1)}
      {count != null && <span className="text-ink-faint">({count.toLocaleString("en-IN")})</span>}
    </span>
  )
}

export function PriceTag({ level, range }: { level?: number | null; range?: string | null }) {
  if (range && /\d/.test(range)) return <span className="whitespace-nowrap font-mono text-sm text-pine">{range}</span>
  if (level == null) return null
  return (
    <span className="font-mono text-sm">
      <span className="text-pine">{"₹".repeat(Math.max(1, level))}</span>
      <span className="text-ink-line">{"₹".repeat(Math.max(0, 4 - level))}</span>
    </span>
  )
}

export function Chip({
  children,
  active,
  onClick,
  tone = "ink",
}: {
  children: ReactNode
  active?: boolean
  onClick?: () => void
  tone?: "ink" | "saffron" | "pine" | "plum"
}) {
  const tones = {
    ink: "data-[on=true]:bg-ink data-[on=true]:text-paper-card",
    saffron: "data-[on=true]:bg-saffron data-[on=true]:text-paper-card",
    pine: "data-[on=true]:bg-pine data-[on=true]:text-paper-card",
    plum: "data-[on=true]:bg-plum data-[on=true]:text-paper-card",
  }[tone]
  return (
    <button
      type="button"
      data-on={!!active}
      onClick={onClick}
      className={cn(
        "rounded-full border border-ink-line bg-paper-card/60 px-3.5 py-1.5 text-xs font-medium text-ink-soft",
        "transition hover:border-ink/40",
        tones,
      )}
    >
      {children}
    </button>
  )
}

export function StatusNote({ status, message }: { status?: string; message?: string }) {
  const text =
    message ||
    (status === "not_configured"
      ? "This service isn't configured yet — add the relevant API key to the backend .env."
      : status === "request_failed"
        ? "The upstream provider couldn't be reached (check the key/plan)."
        : "Nothing came back for that.")
  return (
    <div className="card flex items-start gap-3 p-5 text-sm text-ink-soft">
      <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-saffron" />
      <p className="text-pretty">{text}</p>
    </div>
  )
}

export function Stat({ k, v }: { k: string; v: ReactNode }) {
  return (
    <div>
      <div className="font-display text-3xl text-ink">{v}</div>
      <div className="label mt-1">{k}</div>
    </div>
  )
}
