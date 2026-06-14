/**
 * Ephemeral guest demo — for recruiters to explore the whole product with no sign-up.
 *
 * Design rules (see also the demo banner copy):
 *  - NOTHING is stored server-side. There is no demo account, no token, no DB row.
 *  - NO seeded/stub data. The guest starts as a blank-slate omnivore; whatever they do
 *    in-session (searches, opened places, profile edits) lives only in `sessionStorage`
 *    and vanishes when the tab closes.
 *  - Everything works for real: Eat/Go/Buy/chat/voice/menus hit the same public backend
 *    a signed-in user does. Only the five auth-gated personal surfaces (profile, dashboard,
 *    activity, recommendations, taste-graph) are served from this session instead of `/me`.
 */
import type {
  Activity,
  Dashboard,
  Profile,
  TasteEdge,
  TasteGraph,
  TasteNode,
  UserInfo,
} from "./types"

const FLAG = "kensho.demo"
const PROFILE = "kensho.demo.profile"
const ACTIVITY = "kensho.demo.activity"

/** The synthetic guest — never written to the backend. */
export const DEMO_USER: UserInfo = {
  user_id: "demo-guest",
  username: "guest",
  email: "",
  role: "guest",
  is_active: true,
}

/** A neutral, blank-slate profile — `non-vegetarian` means nothing is filtered out yet. */
export function defaultDemoProfile(): Profile {
  return {
    user_id: "demo-guest",
    name: "Guest",
    dob: null,
    gender: null,
    age: null,
    location: "",
    lat: null,
    lng: null,
    dietary_type: "non-vegetarian",
    spice_tolerance: null,
    allergies: [],
    goals: [],
    likes: [],
    dislikes: [],
    cuisines: [],
    onboarded: true,
  }
}

export function isDemo(): boolean {
  try {
    return sessionStorage.getItem(FLAG) === "1"
  } catch {
    return false
  }
}

/** Begin a fresh ephemeral session and return the starting profile. */
export function startDemoSession(): Profile {
  const p = defaultDemoProfile()
  try {
    sessionStorage.setItem(FLAG, "1")
    sessionStorage.setItem(PROFILE, JSON.stringify(p))
    sessionStorage.removeItem(ACTIVITY)
  } catch {}
  return p
}

export function endDemoSession(): void {
  try {
    sessionStorage.removeItem(FLAG)
    sessionStorage.removeItem(PROFILE)
    sessionStorage.removeItem(ACTIVITY)
  } catch {}
}

export function getDemoProfile(): Profile {
  try {
    const raw = sessionStorage.getItem(PROFILE)
    if (raw) return { ...defaultDemoProfile(), ...JSON.parse(raw) }
  } catch {}
  return defaultDemoProfile()
}

export function setDemoProfile(patch: Partial<Profile>): Profile {
  const next: Profile = { ...getDemoProfile(), ...patch, user_id: "demo-guest", onboarded: true }
  try {
    sessionStorage.setItem(PROFILE, JSON.stringify(next))
  } catch {}
  return next
}

export function getDemoActivity(): Activity[] {
  try {
    const raw = sessionStorage.getItem(ACTIVITY)
    if (raw) return JSON.parse(raw) as Activity[]
  } catch {}
  return []
}

/** Record an in-session interaction so the demo dashboard fills in as the guest explores. */
export function pushDemoActivity(a: Omit<Activity, "id" | "created_at">): void {
  const list = getDemoActivity()
  const item: Activity = { ...a, id: Date.now() + list.length, created_at: new Date().toISOString() }
  list.unshift(item)
  try {
    sessionStorage.setItem(ACTIVITY, JSON.stringify(list.slice(0, 60)))
  } catch {}
}

/** Build the dashboard payload from in-session activity (same shape as `/me/dashboard`). */
export function demoDashboard(): Dashboard {
  const acts = getDemoActivity()
  const of = (kind: Activity["kind"]) => acts.filter((a) => a.kind === kind)
  const searches = of("search")
  const views = of("view")
  const orders = of("order")
  return {
    status: "ok",
    counts: { searches: searches.length, views: views.length, orders: orders.length },
    recent_searches: searches.slice(0, 8),
    recent_views: views.slice(0, 8),
    recent_orders: orders.slice(0, 8),
  }
}

/** Synthesize the taste graph from the session profile (same shape as `/me/taste-graph`). */
export function demoTasteGraph(): TasteGraph {
  const p = getDemoProfile()
  const center: TasteNode = { id: "me", label: p.name || "You", group: "user", weight: 8 }
  const nodes: TasteNode[] = [center]
  const edges: TasteEdge[] = []
  const add = (id: string, label: string, group: TasteNode["group"], weight: number) => {
    nodes.push({ id, label, group, weight })
    edges.push({ source: "me", target: id, kind: group })
  }
  if (p.dietary_type) add(`diet:${p.dietary_type}`, p.dietary_type.replace(/-/g, " "), "diet", 6)
  ;(p.cuisines ?? []).forEach((c) => add(`cui:${c}`, c, "cuisine", 4))
  ;(p.likes ?? []).forEach((l) => add(`food:${l}`, l, "food", 3))
  ;(p.allergies ?? []).forEach((a) => add(`alg:${a}`, a, "allergy", 4))
  ;(p.goals ?? []).forEach((g) => add(`goal:${g}`, g, "goal", 3))
  return {
    status: "ok",
    onboarded: true,
    center,
    nodes,
    edges,
    insights: {
      favorite_cuisines: p.cuisines ?? [],
      total_interactions: getDemoActivity().length,
    },
  }
}
