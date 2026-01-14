import { useState, useEffect } from 'react'

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

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser')
      return
    }

    setLoading(true)
    setError(null)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        
        // Try to get location name from backend
        try {
          const response = await fetch(
            `http://localhost:8000/api/v1/location/reverse-geocode?latitude=${latitude}&longitude=${longitude}`
          )
          if (response.ok) {
            const data = await response.json()
            setLocation({
              latitude,
              longitude,
              city: data.address?.city || data.display_name?.split(',')[0],
              region: data.address?.state || data.display_name?.split(',')[1],
              country: data.address?.country || data.display_name?.split(',').pop(),
            })
          } else {
            // Fallback to just coordinates
            setLocation({ latitude, longitude })
          }
        } catch (err) {
          // Fallback to just coordinates
          setLocation({ latitude, longitude })
        }
        
        setLoading(false)
      },
      (err) => {
        setError(err.message || 'Failed to get location')
        setLoading(false)
        
        // Fallback: Try to get location from IP
        fetch('http://localhost:8000/api/v1/location/ip')
          .then(res => res.json())
          .then(data => {
            if (data.latitude && data.longitude) {
              setLocation({
                latitude: data.latitude,
                longitude: data.longitude,
                city: data.city,
                region: data.region,
                country: data.country,
              })
              setError(null)
            }
          })
          .catch(() => {
            // Ignore IP fallback errors
          })
      }
    )
  }

  useEffect(() => {
    // Auto-request location on mount
    requestLocation()
  }, [])

  return { location, loading, error, requestLocation }
}
