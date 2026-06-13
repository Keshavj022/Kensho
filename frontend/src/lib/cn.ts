import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const INR = (n?: number | null) =>
  n == null ? "—" : "₹" + Math.round(n).toLocaleString("en-IN")

export const money = (n?: number | null, cur = "INR") => {
  if (n == null) return "—"
  if (cur === "INR") return INR(n)
  try {
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: cur, maximumFractionDigits: 0 }).format(n)
  } catch {
    return `${cur} ${Math.round(n)}`
  }
}
