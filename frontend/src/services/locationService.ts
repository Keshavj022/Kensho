/**
 * Location Service - API calls for location features
 */
import { apiService } from './api'
import { API_ENDPOINTS } from '../config/api'

export interface LocationFromIP {
  latitude: number
  longitude: number
  city?: string
  region?: string
  country?: string
  country_code?: string
  timezone?: string
  ip?: string
}

export interface GeocodeResult {
  latitude: number
  longitude: number
  display_name?: string
  address?: {
    city?: string
    state?: string
    country?: string
    postcode?: string
  }
}

export interface DistanceResult {
  distance_km: number
  distance_miles: number
  point1: { latitude: number; longitude: number }
  point2: { latitude: number; longitude: number }
}

class LocationService {
  /**
   * Get location from IP address
   */
  async getLocationFromIP(): Promise<LocationFromIP> {
    return apiService.get<LocationFromIP>(API_ENDPOINTS.LOCATION_IP)
  }

  /**
   * Geocode an address to coordinates
   */
  async geocodeAddress(address: string): Promise<GeocodeResult> {
    return apiService.get<GeocodeResult>(API_ENDPOINTS.LOCATION_GEOCODE, { address })
  }

  /**
   * Reverse geocode coordinates to address
   */
  async reverseGeocode(latitude: number, longitude: number): Promise<GeocodeResult> {
    return apiService.get<GeocodeResult>(API_ENDPOINTS.LOCATION_REVERSE_GEOCODE, {
      latitude,
      longitude,
    })
  }

  /**
   * Calculate distance between two coordinates
   */
  async calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ): Promise<DistanceResult> {
    return apiService.get<DistanceResult>(API_ENDPOINTS.LOCATION_DISTANCE, {
      lat1,
      lon1,
      lat2,
      lon2,
    })
  }
}

export const locationService = new LocationService()
