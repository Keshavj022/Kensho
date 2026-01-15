/**
 * Restaurant Service - API calls for restaurant features
 */
import { apiService } from './api'
import { API_ENDPOINTS } from '../config/api'

export interface Restaurant {
  id: string
  name: string
  cuisine?: string
  location?: {
    latitude: number
    longitude: number
  }
  address?: string
  vicinity?: string
  rating?: number
  user_ratings_total?: number
  review_count?: number
  price?: string
  price_level?: number
  priceRange?: string
  dietaryOptions?: string[]
  types?: string[]
  categories?: string[]
  distance_km?: number
  image_url?: string
  photos?: any[]
  description?: string
}

export interface RestaurantSearchParams {
  query?: string
  location?: string
  latitude?: number
  longitude?: number
  cuisine?: string
  dietary_type?: string
  max_results?: number
}

export interface RestaurantSearchResponse {
  results: Restaurant[]
  count: number
}

export interface ChatRequest {
  message: string
  user_id?: string
  thread_id?: string
}

export interface ChatResponse {
  message: string
  thread_id: string
  follow_up_questions?: string[]
  recommendations?: Restaurant[]
}

export interface RecommendationRequest {
  user_query: string
  user_id?: string
}

export interface RecommendationResponse {
  response?: string
  thread_id?: string
  recommendations: Restaurant[]
  kg_recommendations?: Restaurant[]
  explanation?: string
  confidence_score?: number
  follow_up_questions?: string[]
}

class RestaurantService {
  /**
   * Search restaurants
   */
  async searchRestaurants(params: RestaurantSearchParams): Promise<RestaurantSearchResponse> {
    return apiService.post<RestaurantSearchResponse>(API_ENDPOINTS.RESTAURANT_SEARCH, params)
  }

  /**
   * Get restaurant recommendations
   */
  async getRecommendations(request: RecommendationRequest): Promise<RecommendationResponse> {
    return apiService.post<RecommendationResponse>(API_ENDPOINTS.RESTAURANT_RECOMMENDATIONS, request)
  }

  /**
   * Chat with restaurant agent
   */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    return apiService.post<ChatResponse>(API_ENDPOINTS.RESTAURANT_CHAT, request)
  }

  /**
   * Get available cuisines
   */
  async getCuisines(): Promise<{ cuisines: string[] }> {
    return apiService.get<{ cuisines: string[] }>(API_ENDPOINTS.RESTAURANT_CUISINES)
  }

  /**
   * Get available locations
   */
  async getLocations(): Promise<{ locations: string[] }> {
    return apiService.get<{ locations: string[] }>(API_ENDPOINTS.RESTAURANT_LOCATIONS)
  }
}

export const restaurantService = new RestaurantService()
