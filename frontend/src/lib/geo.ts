import { api } from "./api"

export interface Detected {
  lat?: number
  lng?: number
  location?: string
  source?: "gps" | "ip"
}

export async function detectLocation(): Promise<Detected> {
  const pos = await new Promise<GeolocationPosition | null>((resolve) => {
    if (!navigator.geolocation) return resolve(null)
    navigator.geolocation.getCurrentPosition(
      (p) => resolve(p),
      () => resolve(null),
      { timeout: 8000, maximumAge: 60000, enableHighAccuracy: false },
    )
  })

  if (pos) {
    const { latitude: lat, longitude: lng } = pos.coords
    try {
      const r = await api.reverseGeocode(lat, lng)
      return { lat, lng, location: r.status === "ok" ? r.location : undefined, source: "gps" }
    } catch {
      return { lat, lng, source: "gps" }
    }
  }

  try {
    const r = await api.ipLocation()
    if (r.status === "ok") return { lat: r.lat, lng: r.lng, location: r.location, source: "ip" }
  } catch {}
  return {}
}
