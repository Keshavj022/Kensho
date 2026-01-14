import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, UtensilsCrossed, Star, MapPin, Clock, Heart, Filter, Mic, Image as ImageIcon } from 'lucide-react'

interface Restaurant {
  id: string
  name: string
  cuisine: string
  location: string
  rating: number
  priceRange: string
  dietaryOptions: string[]
  popularDishes: string[]
  description: string
  image?: string
}

const FoodRecommendations = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)

  // Mock data - in real app, this would come from API
  const mockRestaurants: Restaurant[] = [
    {
      id: '1',
      name: 'The Gourmet Kitchen',
      cuisine: 'Italian',
      location: 'Downtown',
      rating: 4.8,
      priceRange: '$$$',
      dietaryOptions: ['Vegetarian', 'Vegan', 'Gluten-Free'],
      popularDishes: ['Margherita Pizza', 'Truffle Pasta', 'Tiramisu'],
      description: 'Authentic Italian cuisine with a modern twist, featuring fresh ingredients and traditional recipes.',
    },
    {
      id: '2',
      name: 'Sakura Sushi',
      cuisine: 'Japanese',
      location: 'Waterfront',
      rating: 4.9,
      priceRange: '$$$$',
      dietaryOptions: ['Pescatarian', 'Gluten-Free'],
      popularDishes: ['Dragon Roll', 'Sashimi Platter', 'Miso Soup'],
      description: 'Premium sushi experience with the freshest fish and traditional Japanese techniques.',
    },
    {
      id: '3',
      name: 'Green Leaf Cafe',
      cuisine: 'Vegetarian',
      location: 'Park District',
      rating: 4.7,
      priceRange: '$$',
      dietaryOptions: ['Vegetarian', 'Vegan', 'Organic'],
      popularDishes: ['Quinoa Bowl', 'Avocado Toast', 'Smoothie Bowl'],
      description: 'Healthy and delicious plant-based meals made with organic, locally-sourced ingredients.',
    },
    {
      id: '4',
      name: 'Spice Route',
      cuisine: 'Indian',
      location: 'Cultural Quarter',
      rating: 4.6,
      priceRange: '$$',
      dietaryOptions: ['Vegetarian', 'Vegan', 'Halal'],
      popularDishes: ['Butter Chicken', 'Biryani', 'Naan Bread'],
      description: 'Aromatic Indian dishes with authentic spices and flavors from different regions.',
    },
  ]

  const filters = ['All', 'Vegetarian', 'Vegan', 'Gluten-Free', 'Italian', 'Japanese', 'Indian']

  const filteredRestaurants = mockRestaurants.filter((restaurant) => {
    const matchesSearch = restaurant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      restaurant.cuisine.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = !selectedFilter || selectedFilter === 'All' ||
      restaurant.dietaryOptions.includes(selectedFilter) ||
      restaurant.cuisine === selectedFilter
    return matchesSearch && matchesFilter
  })

  const handleVoiceSearch = () => {
    setIsListening(!isListening)
    // In real app, this would integrate with speech-to-text
    setTimeout(() => {
      setIsListening(false)
      setSearchQuery('Italian restaurants near me')
    }, 2000)
  }

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
          <div className="relative">
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
          </div>

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

        {/* Restaurant Grid */}
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
                        {restaurant.cuisine}
                      </span>
                      <div className="flex items-center space-x-1 px-3 py-1 bg-white/90 rounded-full">
                        <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                        <span className="text-sm font-semibold text-slate-800">{restaurant.rating}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-6">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-2xl font-bold text-slate-800 group-hover:text-gradient transition-colors">
                      {restaurant.name}
                    </h3>
                    <span className="text-lg font-semibold text-slate-600">{restaurant.priceRange}</span>
                  </div>

                  <div className="flex items-center text-slate-600 mb-4">
                    <MapPin className="w-4 h-4 mr-1" />
                    <span className="text-sm">{restaurant.location}</span>
                  </div>

                  <p className="text-slate-600 mb-4 line-clamp-2">{restaurant.description}</p>

                  {/* Dietary Options */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {restaurant.dietaryOptions.slice(0, 3).map((option) => (
                      <span
                        key={option}
                        className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs font-medium"
                      >
                        {option}
                      </span>
                    ))}
                  </div>

                  {/* Popular Dishes */}
                  <div>
                    <p className="text-sm font-semibold text-slate-700 mb-2">Popular Dishes:</p>
                    <div className="flex flex-wrap gap-2">
                      {restaurant.popularDishes.map((dish) => (
                        <span
                          key={dish}
                          className="px-2 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs"
                        >
                          {dish}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Action Button */}
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full mt-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-semibold shadow-lg"
                  >
                    View Menu & Order
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </AnimatePresence>

        {filteredRestaurants.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <UtensilsCrossed className="w-16 h-16 text-slate-400 mx-auto mb-4" />
            <p className="text-xl text-slate-600">No restaurants found. Try different search terms.</p>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default FoodRecommendations
