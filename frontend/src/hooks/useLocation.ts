import { useState, useEffect } from 'react'
import { locationService } from '../services/locationService'

interface Location {
  latitude: number
  longitude: number
  city?: string
  region?: string
  country?: string
}

interface UseLocationReturn {
  location: Location | null
  loading: boolean
  error: string | null
  requestLocation: () => void
}

export const useLocation = (): UseLocationReturn => {
  const [location, setLocation] = useState<Location | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const requestLocation = async () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser')
      // Fallback to IP-based location
      try {
        const ipLocation = await locationService.getLocationFromIP()
        if (ipLocation.latitude && ipLocation.longitude) {
          setLocation({
            latitude: ipLocation.latitude,
            longitude: ipLocation.longitude,
            city: ipLocation.city,
            region: ipLocation.region,
            country: ipLocation.country,
          })
        }
      } catch (err) {
        setError('Could not determine location')
      }
      return
    }

    setLoading(true)
    setError(null)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        
        // Try to get location name from backend
        try {
          const data = await locationService.reverseGeocode(latitude, longitude)
          setLocation({
            latitude,
            longitude,
            city: data.address?.city || data.display_name?.split(',')[0],
            region: data.address?.state || data.display_name?.split(',')[1],
            country: data.address?.country || data.display_name?.split(',').pop(),
          })
        } catch (err) {
          // Fallback to just coordinates
          setLocation({ latitude, longitude })
        }
        
        setLoading(false)
      },
      async (err) => {
        setError(err.message || 'Failed to get location')
        setLoading(false)
        
        // Fallback: Try to get location from IP
        try {
          const ipLocation = await locationService.getLocationFromIP()
          if (ipLocation.latitude && ipLocation.longitude) {
            setLocation({
              latitude: ipLocation.latitude,
              longitude: ipLocation.longitude,
              city: ipLocation.city,
              region: ipLocation.region,
              country: ipLocation.country,
            })
            setError(null)
          }
        } catch (ipErr) {
          // Ignore IP fallback errors
          console.error('IP location fallback failed:', ipErr)
        }
      }
    )
  }

  useEffect(() => {
    // Auto-request location on mount
    requestLocation()
  }, [])

  return { location, loading, error, requestLocation }
}
