
export type Status = "ok" | "not_configured" | "error" | "no_menu" | "no_data_id" | string

export interface Restaurant {
  id: string // place_id
  data_id?: string
  name: string
  rating?: number | null
  rating_count?: number | null
  price_level?: number | null
  price_level_label?: string | null
  price_range?: string | null
  location?: { lat?: number | null; lng?: number | null }
  address?: string | null
  types?: string[]
  primary_type?: string | null
  open_now?: boolean | null
  phone?: string | null
  website?: string | null
  summary?: string | null
  thumbnail?: string | null
  photo_urls?: string[]
  reason?: string // why it was recommended
}
export interface RestaurantSearch {
  status: Status
  count?: number
  restaurants: Restaurant[]
  message?: string
}

export interface MenuItem {
  id: string
  name: string
  description?: string | null
  price?: number | null
  currency: string
  section?: string | null
  dietary_flags: string[]
  spice_level?: string | null
  image_url?: string | null
  source: "structured" | "ocr" | "web"
  confidence: number
}
export interface MenuSection {
  name: string
  items: MenuItem[]
}
export interface Menu {
  status: Status
  cached?: boolean
  restaurant_id: string
  restaurant_name: string
  currency: string
  sections: MenuSection[]
  source: "structured" | "ocr" | "web"
  order_online_url?: string | null
  raw_photo_urls?: string[]
  note?: string
}

export interface Dish {
  id: string
  name: string
  restaurant_id: string
  restaurant_name: string
  price?: number | null
  currency?: string
  section?: string
  dietary_flags: string[]
  score?: number | null
  reason?: string
}
export interface DishSearch {
  status: Status
  count: number
  dishes: Dish[]
  indexed_items?: number
  message?: string
}

export interface FlightLeg {
  airline?: string
  flight_number?: string
  from?: string
  to?: string
  depart?: string
  arrive?: string
  duration_minutes?: number
}
export interface Flight {
  price?: number
  total_duration_minutes?: number
  stops?: number
  airlines?: string[]
  departure?: Record<string, any>
  arrival?: Record<string, any>
  carbon_emissions?: number | null
  booking_token?: string
  legs?: FlightLeg[]
}
export interface FlightSearch {
  status: Status
  currency?: string
  cheapest?: Flight | null
  flights?: Flight[]
  best_flights?: Flight[]
  other_flights?: Flight[]
  price_insights?: {
    lowest_price?: number | null
    price_level?: string | null
    typical_price_range?: [number, number] | null
  }
  note?: string
  message?: string
}

export interface HotelProvider {
  source?: string
  price_per_night?: number | null
  link?: string | null
  official?: boolean
}
export interface Hotel {
  name?: string
  rating?: number | null
  hotel_class?: string | null
  price_per_night?: number | null
  total_rate?: number | null
  cheapest_provider?: HotelProvider | null
  gps?: { latitude?: number; longitude?: number } | null
  link?: string | null
}
export interface HotelSearch {
  status: Status
  currency?: string
  count?: number
  cheapest?: Hotel | null
  hotels: Hotel[]
  message?: string
}

export interface DayPlan {
  day: number
  date: string
  location: string
  activities: { name?: string; info?: string; summary?: string; time?: string | null }[]
  meals: { type: string; time: string; suggestion: string }[]
}
export interface TripPlan {
  status: Status
  id?: string
  trip_name?: string
  origin?: string | null
  destination: string
  start_date: string
  end_date: string
  nights: number
  travelers: number
  pace: string
  flights?: FlightSearch | { status: string }
  hotel?: Hotel | null
  hotels_searched?: number
  daily: DayPlan[]
  estimated_cost?: number | null
  currency?: string
  note?: string
}

export interface Product {
  title?: string
  price?: number | null
  price_label?: string | null
  source?: string
  link?: string
  rating?: number | null
  reviews?: number | null
  thumbnail?: string | null
}
export interface ProductSearch {
  status: Status
  count: number
  products: Product[]
  message?: string
}

export interface ChatReference {
  type: "restaurant" | "dish" | "product" | "hotel" | string
  title: string
  subtitle?: string
  link: string
  external?: boolean
  image?: string | null
}
export interface ChatResponse {
  message: string
  thread_id: string
  references?: ChatReference[] | null
  recommendations?: any[] | null
  follow_up_questions?: string[] | null
}

export interface CartItem {
  item_id: string
  name: string
  price?: number | null
  qty: number
}
export interface Cart {
  status: Status
  restaurant_id?: string
  restaurant_name?: string
  items: CartItem[]
  order_online_url?: string | null
  total: number
}
export interface VoiceOrder {
  status: Status
  transcript: string
  stt_provider?: string | null
  matched: { item_id: string; name: string; qty: number }[]
  cart: Cart
  order_online_url?: string | null
  confirmation_text: string
  message?: string
}

export interface UserInfo {
  user_id: string
  username: string
  email: string
  role: string
  is_active: boolean
}
export interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
}

export interface Health {
  status: string
  app: string
  version: string
  subsystems: Record<string, string>
}

export interface ProfilePayload {
  name?: string
  dob?: string | null
  gender?: string | null
  age?: number | null
  location?: string
  lat?: number | null
  lng?: number | null
  dietary_type?: string
  spice_tolerance?: string | null
  allergies?: string[]
  goals?: string[]
  likes?: string[]
  dislikes?: string[]
  cuisines?: string[]
}
export interface Profile extends ProfilePayload {
  user_id: string
  age?: number | null
  allergies: string[]
  goals: string[]
  likes: string[]
  dislikes: string[]
  cuisines: string[]
  onboarded: boolean
}

export interface Activity {
  id: number
  kind: "search" | "view" | "dish_view" | "order"
  query?: string | null
  restaurant_id?: string | null
  restaurant_name?: string | null
  cuisine?: string | null
  domain: string
  payload: Record<string, any>
  created_at?: string | null
}
export interface Dashboard {
  status: Status
  counts: { searches: number; views: number; orders: number }
  recent_searches: Activity[]
  recent_views: Activity[]
  recent_orders: Activity[]
}
export interface Recommendations {
  status: Status
  restaurants: RestaurantSearch
  dishes: DishSearch
}
export interface TasteNode {
  id: string
  label: string
  group: "user" | "diet" | "cuisine" | "food" | "allergy" | "goal"
  weight?: number
}
export interface TasteEdge {
  source: string
  target: string
  kind: string
}
export interface TasteGraph {
  status: Status
  onboarded: boolean
  center: TasteNode
  nodes: TasteNode[]
  edges: TasteEdge[]
  insights: Record<string, any>
}
export interface TrackBody {
  kind: "search" | "view" | "dish_view" | "order"
  query?: string
  restaurant_id?: string
  restaurant_name?: string
  cuisine?: string
  domain?: string
  payload?: Record<string, any>
}
export interface Photos {
  status: Status
  count?: number
  photos: string[]
}
