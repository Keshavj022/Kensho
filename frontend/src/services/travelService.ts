/**
 * Travel Service - API calls for travel features
 */
import { apiService } from './api'
import { API_ENDPOINTS } from '../config/api'

export interface Flight {
  id: string
  price?: number
  currency?: string
  itineraries?: any[]
  numberOfBookableSeats?: number
  airline?: string
  departure?: string
  arrival?: string
  departureTime?: string
  arrivalTime?: string
  duration?: string
  stops?: number
}

export interface Hotel {
  id: string
  name?: string
  location?: string
  address?: string
  rating?: number
  price_per_night?: number
  price?: number | { total?: number }
  currency?: string
  amenities?: string[]
  room_type?: string
  check_in?: string
  check_out?: string
  total_nights?: number
  total_price?: number
  images?: string[]
  description?: string
  distance_km?: number
}

export interface FlightSearchRequest {
  origin: string
  destination: string
  departure_date?: string
  return_date?: string
  passengers?: number
  travel_class?: string
  max_price?: number
}

export interface HotelSearchRequest {
  location: string
  latitude?: number
  longitude?: number
  check_in?: string
  check_out?: string
  guests?: number
  min_rating?: number
  max_price_per_night?: number
}

export interface ItineraryRequest {
  destination: string
  start_date: string
  end_date: string
  travelers?: number
  budget?: number
  preferences?: string[]
  origin?: string
  user_id?: string
}

export interface TravelChatRequest {
  message: string
  user_id?: string
  thread_id?: string
}

export interface TravelChatResponse {
  message: string
  thread_id: string
  suggestions?: string[]
  itinerary?: any
  flights?: Flight[]
  hotels?: Hotel[]
}

class TravelService {
  /**
   * Search flights
   */
  async searchFlights(request: FlightSearchRequest): Promise<{ flights: Flight[]; count: number }> {
    return apiService.post<{ flights: Flight[]; count: number }>(API_ENDPOINTS.TRAVEL_FLIGHTS_SEARCH, request)
  }

  /**
   * Search hotels
   */
  async searchHotels(request: HotelSearchRequest): Promise<{ hotels: Hotel[]; count: number }> {
    return apiService.post<{ hotels: Hotel[]; count: number }>(API_ENDPOINTS.TRAVEL_HOTELS_SEARCH, request)
  }

  /**
   * Create itinerary
   */
  async createItinerary(request: ItineraryRequest): Promise<any> {
    return apiService.post(API_ENDPOINTS.TRAVEL_ITINERARY_CREATE, request)
  }

  /**
   * Get itinerary by ID
   */
  async getItinerary(itineraryId: string): Promise<any> {
    return apiService.get(`${API_ENDPOINTS.TRAVEL_ITINERARY_GET}/${itineraryId}`)
  }

  /**
   * Chat with travel agent
   */
  async chat(request: TravelChatRequest): Promise<TravelChatResponse> {
    return apiService.post<TravelChatResponse>(API_ENDPOINTS.TRAVEL_CHAT, request)
  }

  /**
   * Get destinations
   */
  async getDestinations(): Promise<{ destinations: string[]; count: number }> {
    return apiService.get<{ destinations: string[]; count: number }>(API_ENDPOINTS.TRAVEL_DESTINATIONS)
  }

  /**
   * Get destination info
   */
  async getDestinationInfo(destinationName: string): Promise<any> {
    return apiService.get(`${API_ENDPOINTS.TRAVEL_DESTINATION_INFO}/${encodeURIComponent(destinationName)}`)
  }

  /**
   * Get activities for a location
   */
  async getActivities(
    location: string,
    activityType?: string,
    latitude?: number,
    longitude?: number
  ): Promise<{ activities: any[]; count: number }> {
    const params: any = { location }
    if (activityType) params.activity_type = activityType
    if (latitude) params.latitude = latitude
    if (longitude) params.longitude = longitude

    const queryString = new URLSearchParams(params).toString()
    return apiService.get<{ activities: any[]; count: number }>(
      `${API_ENDPOINTS.TRAVEL_ACTIVITIES}/${encodeURIComponent(location)}?${queryString}`
    )
  }
}

export const travelService = new TravelService()
