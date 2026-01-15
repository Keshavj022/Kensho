import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, UtensilsCrossed, Star, MapPin, Clock, Heart, Filter, Mic, Image as ImageIcon, Loader2, AlertCircle } from 'lucide-react'
import { restaurantService, Restaurant } from '../services/restaurantService'
import { useLocation } from '../hooks/useLocation'

const FoodRecommendations = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cuisines, setCuisines] = useState<string[]>([])
  
  const { location, loading: locationLoading } = useLocation()

  const filters = ['All', 'Vegetarian', 'Vegan', 'Gluten-Free', ...cuisines.slice(0, 5)]

  // Load cuisines on mount
  useEffect(() => {
    const loadCuisines = async () => {
      try {
        const response = await restaurantService.getCuisines()
        setCuisines(response.cuisines)
      } catch (err) {
        console.error('Failed to load cuisines:', err)
      }
    }
    loadCuisines()
  }, [])

  // Search restaurants
  const searchRestaurants = useCallback(async () => {
    if (!location?.latitude || !location?.longitude) {
      if (!locationLoading) {
        setError('Location is required. Please allow location access or enter a location.')
      }
      return
    }

    setLoading(true)
    setError(null)

    try {
      const params: any = {
        latitude: location.latitude,
        longitude: location.longitude,
        max_results: 20,
      }

      if (searchQuery) {
        params.query = searchQuery
      }

      // Map filter to dietary type or cuisine
      if (selectedFilter && selectedFilter !== 'All') {
        const dietaryTypes = ['Vegetarian', 'Vegan', 'Gluten-Free']
        if (dietaryTypes.includes(selectedFilter)) {
          params.dietary_type = selectedFilter.toLowerCase()
        } else {
          params.cuisine = selectedFilter
        }
      }

      const response = await restaurantService.searchRestaurants(params)
      setRestaurants(response.results || [])
    } catch (err: any) {
      console.error('Search error:', err)
      setError(err.message || 'Failed to search restaurants. Please try again.')
      setRestaurants([])
    } finally {
      setLoading(false)
    }
  }, [location, searchQuery, selectedFilter, locationLoading])

  // Auto-search when location is available or filters change
  useEffect(() => {
    if (location && !locationLoading) {
      searchRestaurants()
    }
  }, [location, locationLoading, searchQuery, selectedFilter, searchRestaurants])

  const handleVoiceSearch = () => {
    setIsListening(!isListening)
    // In real app, this would integrate with speech-to-text
    setTimeout(() => {
      setIsListening(false)
      setSearchQuery('Italian restaurants near me')
    }, 2000)
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    searchRestaurants()
  }

  // Format price level to price range
  const formatPriceRange = (priceLevel?: number, price?: string): string => {
    if (price) return price
    if (priceLevel === undefined || priceLevel === null) return '$$'
    return '$'.repeat(Math.min(priceLevel + 1, 4))
  }

  // Get cuisine from types or categories
  const getCuisine = (restaurant: Restaurant): string => {
    if (restaurant.cuisine) return restaurant.cuisine
    const types = restaurant.types || restaurant.categories || []
    const cuisineTypes = types.filter((t: string) => 
      !['restaurant', 'food', 'establishment', 'point_of_interest'].includes(t.toLowerCase())
    )
    return cuisineTypes[0] || 'Restaurant'
  }

  // Get location string
  const getLocationString = (restaurant: Restaurant): string => {
    if (restaurant.vicinity) return restaurant.vicinity
    if (restaurant.address) return restaurant.address
    if (restaurant.location?.latitude && restaurant.distance_km) {
      return `${restaurant.distance_km.toFixed(1)} km away`
    }
    return 'Location not available'
  }

  const filteredRestaurants = restaurants.filter((restaurant) => {
    if (!searchQuery && !selectedFilter) return true
    
    const matchesSearch = !searchQuery || 
      restaurant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      getCuisine(restaurant).toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesFilter = !selectedFilter || selectedFilter === 'All' ||
      getCuisine(restaurant) === selectedFilter ||
      (selectedFilter === 'Vegetarian' && restaurant.types?.some(t => t.toLowerCase().includes('vegetarian'))) ||
      (selectedFilter === 'Vegan' && restaurant.types?.some(t => t.toLowerCase().includes('vegan')))
    
    return matchesSearch && matchesFilter
  })

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', duration: 0.6 }}
            className="inline-block mb-4"
          >
            <div className="w-20 h-20 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
              <UtensilsCrossed className="w-10 h-10 text-white" />
            </div>
          </motion.div>
          <h1 className="text-4xl sm:text-5xl font-display font-bold text-slate-800 mb-4">
            Food <span className="text-gradient">Recommendations</span>
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Discover personalized restaurant recommendations powered by AI
            {location?.city && (
              <span className="block mt-2 text-sm text-slate-500">
                Near {location.city}{location.region ? `, ${location.region}` : ''}
              </span>
            )}
          </p>
        </motion.div>

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8 space-y-4"
        >
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="relative">
            <div className="glass rounded-2xl p-4 flex items-center space-x-4 shadow-lg">
              <Search className="w-6 h-6 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search restaurants, cuisines, or dishes..."
                className="flex-1 bg-transparent border-none outline-none text-slate-700 placeholder-slate-400 text-lg"
              />
              <div className="flex items-center space-x-2">
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={handleVoiceSearch}
                  className={`p-3 rounded-xl transition-colors ${
                    isListening
                      ? 'bg-red-500 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  <Mic className="w-5 h-5" />
                </motion.button>
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-3 bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200"
                >
                  <ImageIcon className="w-5 h-5" />
                </motion.button>
              </div>
            </div>
            {isListening && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="absolute top-full mt-2 left-0 right-0 glass rounded-xl p-4 text-center"
              >
                <div className="flex items-center justify-center space-x-2 text-red-500">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                  <span className="font-medium">Listening...</span>
                </div>
              </motion.div>
            )}
          </form>

          {/* Filters */}
          <div className="flex items-center space-x-2 overflow-x-auto pb-2">
            <Filter className="w-5 h-5 text-slate-600 flex-shrink-0" />
            {filters.map((filter) => (
              <motion.button
                key={filter}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedFilter(filter)}
                className={`px-4 py-2 rounded-full font-medium whitespace-nowrap transition-all ${
                  selectedFilter === filter
                    ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg'
                    : 'glass text-slate-700 hover:bg-white/80'
                }`}
              >
                {filter}
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Loading State */}
        {(loading || locationLoading) && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
            <span className="ml-3 text-slate-600">
              {locationLoading ? 'Getting your location...' : 'Searching restaurants...'}
            </span>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 glass rounded-2xl p-6 border-2 border-red-200"
          >
            <div className="flex items-center space-x-3 text-red-600">
              <AlertCircle className="w-6 h-6" />
              <div>
                <p className="font-semibold">Error</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Restaurant Grid */}
        {!loading && !locationLoading && (
          <AnimatePresence mode="wait">
            <motion.div
              key={selectedFilter + searchQuery}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {filteredRestaurants.map((restaurant, index) => (
                <motion.div
                  key={restaurant.id}
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  whileHover={{ y: -10 }}
                  className="glass rounded-2xl overflow-hidden shadow-lg border-2 border-transparent hover:border-orange-200 transition-all cursor-pointer group"
                >
                  {/* Image placeholder */}
                  <div className="h-48 bg-gradient-to-br from-orange-400 to-red-500 relative overflow-hidden">
                    {restaurant.image_url && (
                      <img
                        src={restaurant.image_url}
                        alt={restaurant.name}
                        className="w-full h-full object-cover"
                      />
                    )}
                    <div className="absolute inset-0 bg-black/20" />
                    <motion.button
                      whileHover={{ scale: 1.2 }}
                      whileTap={{ scale: 0.9 }}
                      className="absolute top-4 right-4 p-2 bg-white/90 rounded-full shadow-lg"
                    >
                      <Heart className="w-5 h-5 text-red-500" />
                    </motion.button>
                    <div className="absolute bottom-4 left-4 right-4">
                      <div className="flex items-center justify-between">
                        <span className="px-3 py-1 bg-white/90 rounded-full text-sm font-semibold text-slate-800">
                          {getCuisine(restaurant)}
                        </span>
                        {restaurant.rating && (
                          <div className="flex items-center space-x-1 px-3 py-1 bg-white/90 rounded-full">
                            <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                            <span className="text-sm font-semibold text-slate-800">
                              {restaurant.rating.toFixed(1)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-2xl font-bold text-slate-800 group-hover:text-gradient transition-colors">
                        {restaurant.name}
                      </h3>
                      <span className="text-lg font-semibold text-slate-600">
                        {formatPriceRange(restaurant.price_level, restaurant.price)}
                      </span>
                    </div>

                    <div className="flex items-center text-slate-600 mb-4">
                      <MapPin className="w-4 h-4 mr-1" />
                      <span className="text-sm">{getLocationString(restaurant)}</span>
                    </div>

                    {restaurant.description && (
                      <p className="text-slate-600 mb-4 line-clamp-2">{restaurant.description}</p>
                    )}

                    {/* Types/Categories */}
                    {(restaurant.types || restaurant.categories) && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {(restaurant.types || restaurant.categories || []).slice(0, 3).map((type: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs font-medium"
                          >
                            {type}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Action Button */}
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full mt-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-semibold shadow-lg"
                    >
                      View Details
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </AnimatePresence>
        )}

        {/* Empty State */}
        {!loading && !locationLoading && !error && filteredRestaurants.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <UtensilsCrossed className="w-16 h-16 text-slate-400 mx-auto mb-4" />
            <p className="text-xl text-slate-600 mb-2">No restaurants found.</p>
            <p className="text-slate-500">
              {location ? 'Try different search terms or filters.' : 'Please allow location access to see nearby restaurants.'}
            </p>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default FoodRecommendations
