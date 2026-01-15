/**
 * API Configuration
 */
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  API_PREFIX: '/api/v1',
  TIMEOUT: 30000, // 30 seconds
}

export const API_ENDPOINTS = {
  // Location
  LOCATION_IP: '/location/ip',
  LOCATION_GEOCODE: '/location/geocode',
  LOCATION_REVERSE_GEOCODE: '/location/reverse-geocode',
  LOCATION_DISTANCE: '/location/distance',
  
  // Restaurant
  RESTAURANT_SEARCH: '/search',
  RESTAURANT_RECOMMENDATIONS: '/recommendations',
  RESTAURANT_CHAT: '/chat',
  RESTAURANT_CUISINES: '/cuisines',
  RESTAURANT_LOCATIONS: '/locations',
  
  // Travel
  TRAVEL_FLIGHTS_SEARCH: '/travel/flights/search',
  TRAVEL_HOTELS_SEARCH: '/travel/hotels/search',
  TRAVEL_ITINERARY_CREATE: '/travel/itinerary/create',
  TRAVEL_ITINERARY_GET: '/travel/itinerary',
  TRAVEL_CHAT: '/travel/chat',
  TRAVEL_DESTINATIONS: '/travel/destinations',
  TRAVEL_DESTINATION_INFO: '/travel/destinations',
  TRAVEL_ACTIVITIES: '/travel/activities',
  
  // Auth
  AUTH_REGISTER: '/auth/register',
  AUTH_LOGIN: '/auth/login',
  AUTH_REFRESH: '/auth/refresh',
  AUTH_LOGOUT: '/auth/logout',
  AUTH_ME: '/auth/me',
  AUTH_CHANGE_PASSWORD: '/auth/change-password',
  
  // Health
  HEALTH: '/health',
}

/**
 * Get full API URL
 */
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${API_CONFIG.API_PREFIX}${endpoint}`
}
