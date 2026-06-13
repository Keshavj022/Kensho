import { getToken } from "./session"
import type {
  Cart,
  ChatResponse,
  Dashboard,
  DishSearch,
  FlightSearch,
  Health,
  HotelSearch,
  Menu,
  Photos,
  ProductSearch,
  Profile,
  ProfilePayload,
  Recommendations,
  RestaurantSearch,
  TasteGraph,
  TokenResponse,
  TrackBody,
  TripPlan,
  UserInfo,
  VoiceOrder,
} from "./types"
import type { Activity } from "./types"

const BASE = (import.meta.env.VITE_API_BASE_URL ?? "") + "/api/v1"

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers = new Headers(opts.headers)
  const token = getToken()
  if (token) headers.set("Authorization", `Bearer ${token}`)
  if (opts.body && !(opts.body instanceof FormData) && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json")

  const res = await fetch(BASE + path, { ...opts, headers })
  const ct = res.headers.get("content-type") || ""
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = ct.includes("json") ? (await res.json()).detail ?? detail : await res.text()
    } catch {}
    throw new ApiError(typeof detail === "string" ? detail : JSON.stringify(detail), res.status)
  }
  if (res.status === 204) return undefined as T
  return ct.includes("json") ? res.json() : (res as unknown as T)
}

const post = <T>(p: string, body?: unknown) =>
  req<T>(p, { method: "POST", body: body == null ? undefined : JSON.stringify(body) })
const get = <T>(p: string) => req<T>(p)

const ROOT = import.meta.env.VITE_API_BASE_URL ?? ""

export const api = {
  health: () => fetch(ROOT + "/health").then((r) => r.json() as Promise<Health>),

  chat: (message: string, thread_id?: string, user_id?: string) =>
    post<ChatResponse>("/chat", { message, thread_id, user_id }),

  searchRestaurants: (body: Record<string, unknown>) => post<RestaurantSearch>("/restaurants/search", body),
  featuredRestaurants: (p: { lat?: number | null; lng?: number | null; location?: string; dietary?: string; limit?: number }) => {
    const q = new URLSearchParams()
    if (p.lat != null) q.set("lat", String(p.lat))
    if (p.lng != null) q.set("lng", String(p.lng))
    if (p.location) q.set("location", p.location)
    if (p.dietary) q.set("dietary", p.dietary)
    if (p.limit) q.set("limit", String(p.limit))
    return get<RestaurantSearch>(`/restaurants/featured?${q.toString()}`)
  },
  restaurant: (placeId: string) => get<any>(`/restaurants/${encodeURIComponent(placeId)}`),
  restaurantPhotos: (placeId: string, limit = 12) =>
    get<Photos>(`/restaurants/${encodeURIComponent(placeId)}/photos?limit=${limit}`),
  menu: (placeId: string, restaurantName = "", refresh = false) =>
    get<Menu>(
      `/restaurants/${encodeURIComponent(placeId)}/menu?restaurant_name=${encodeURIComponent(
        restaurantName,
      )}&refresh=${refresh}`,
    ),
  searchDishes: (query: string, max_results = 12, restaurant_id?: string, dietary?: string) =>
    post<DishSearch>("/restaurants/dishes/search", { query, max_results, restaurant_id, dietary }),
  featuredDishes: (limit = 12, dietary?: string) =>
    get<DishSearch>(`/restaurants/dishes/featured?limit=${limit}${dietary ? `&dietary=${encodeURIComponent(dietary)}` : ""}`),
  prefetchMenus: (items: { place_id: string; name?: string }[], cap = 8) =>
    post<{ status: string; queued: number }>("/restaurants/menu/prefetch", { items, cap }),

  searchFlights: (body: Record<string, unknown>) => post<FlightSearch>("/travel/flights/search", body),
  searchHotels: (body: Record<string, unknown>) => post<HotelSearch>("/travel/hotels/search", body),
  planTrip: (body: Record<string, unknown>) => post<TripPlan>("/travel/itinerary", body),

  searchProducts: (query: string, max_results = 24) => post<ProductSearch>("/shopping/search", { query, max_results }),

  voiceOrder: (form: FormData) => req<VoiceOrder>("/voice/order", { method: "POST", body: form }),
  cart: (placeId: string, sessionId: string) =>
    get<Cart>(`/voice/cart?place_id=${encodeURIComponent(placeId)}&session_id=${encodeURIComponent(sessionId)}`),
  voices: () => get<{ status: string; voices: { voice_id: string; name: string }[] }>("/voice/voices"),
  stt: (form: FormData) => req<{ status: string; text: string; provider?: string; message?: string }>("/voice/stt", { method: "POST", body: form }),
  tts: async (text: string, voice_id?: string): Promise<Blob | null> => {
    const headers = new Headers({ "Content-Type": "application/json" })
    const token = getToken()
    if (token) headers.set("Authorization", `Bearer ${token}`)
    try {
      const res = await fetch(BASE + "/voice/tts", { method: "POST", headers, body: JSON.stringify({ text, voice_id }) })
      const ct = res.headers.get("content-type") || ""
      if (res.ok && ct.includes("audio")) return await res.blob()
      return null
    } catch {
      return null
    }
  },

  register: (email: string, password: string) => post<UserInfo>("/auth/register", { email, password }),
  login: (email: string, password: string) => post<TokenResponse>("/auth/login", { email, password }),
  demoLogin: () => post<TokenResponse>("/auth/demo"),
  checkEmail: (email: string) =>
    get<{ email: string; available: boolean }>(`/auth/check-email?email=${encodeURIComponent(email)}`),
  me: () => get<UserInfo>("/auth/me"),
  logout: () => post<{ message: string }>("/auth/logout"),
  getProfile: () => get<Profile>("/auth/profile"),
  saveProfile: (p: ProfilePayload) => req<Profile>("/auth/profile", { method: "PUT", body: JSON.stringify(p) }),

  dashboard: () => get<Dashboard>("/me/dashboard"),
  myActivity: (limit = 30) => get<{ status: string; count: number; items: Activity[] }>(`/me/activity?limit=${limit}`),
  recommendations: (p?: { lat?: number | null; lng?: number | null; location?: string; limit?: number }) => {
    const q = new URLSearchParams()
    if (p?.lat != null) q.set("lat", String(p.lat))
    if (p?.lng != null) q.set("lng", String(p.lng))
    if (p?.location) q.set("location", p.location)
    if (p?.limit) q.set("limit", String(p.limit))
    return get<Recommendations>(`/me/recommendations?${q.toString()}`)
  },
  tasteGraph: () => get<TasteGraph>("/me/taste-graph"),
  track: (body: TrackBody) => post<{ status: string }>("/me/track", body).catch(() => ({ status: "skipped" })),

  reverseGeocode: (lat: number, lng: number) =>
    get<{ status: string; location?: string; city?: string; lat?: number; lng?: number }>(
      `/location/reverse?lat=${lat}&lng=${lng}`,
    ),
  ipLocation: () => get<{ status: string; location?: string; lat?: number; lng?: number }>("/location/ip"),
  nearestAirport: (lat?: number | null, lng?: number | null, city?: string) => {
    const p = new URLSearchParams()
    if (lat != null) p.set("lat", String(lat))
    if (lng != null) p.set("lng", String(lng))
    if (city) p.set("city", city)
    return get<{ iata?: string; city?: string; name?: string; distance_km?: number; status?: string }>(
      `/location/nearest-airport?${p.toString()}`,
    )
  },
}
