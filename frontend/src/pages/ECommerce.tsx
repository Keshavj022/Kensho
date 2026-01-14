import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ShoppingBag, Search, Heart, ShoppingCart, Filter, Star, Sparkles, TrendingUp, Zap } from 'lucide-react'

interface Product {
  id: string
  name: string
  category: string
  price: number
  originalPrice?: number
  rating: number
  reviews: number
  image?: string
  description: string
  tags: string[]
  inStock: boolean
}

const ECommerce = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [cart, setCart] = useState<string[]>([])
  const [favorites, setFavorites] = useState<string[]>([])

  const categories = ['All', 'Electronics', 'Fashion', 'Home', 'Sports', 'Books', 'Beauty']

  const mockProducts: Product[] = [
    {
      id: '1',
      name: 'Wireless Noise-Canceling Headphones',
      category: 'Electronics',
      price: 299.99,
      originalPrice: 399.99,
      rating: 4.8,
      reviews: 1234,
      description: 'Premium wireless headphones with active noise cancellation and 30-hour battery life.',
      tags: ['Wireless', 'Noise Canceling', 'Premium'],
      inStock: true,
    },
    {
      id: '2',
      name: 'Smart Fitness Watch',
      category: 'Electronics',
      price: 249.99,
      rating: 4.6,
      reviews: 856,
      description: 'Track your fitness goals with advanced health monitoring and GPS tracking.',
      tags: ['Fitness', 'Smart Watch', 'GPS'],
      inStock: true,
    },
    {
      id: '3',
      name: 'Designer Leather Jacket',
      category: 'Fashion',
      price: 449.99,
      originalPrice: 599.99,
      rating: 4.9,
      reviews: 342,
      description: 'Premium genuine leather jacket with modern design and perfect fit.',
      tags: ['Leather', 'Designer', 'Premium'],
      inStock: true,
    },
    {
      id: '4',
      name: 'Minimalist Home Decor Set',
      category: 'Home',
      price: 129.99,
      rating: 4.7,
      reviews: 567,
      description: 'Complete home decoration set with modern minimalist design aesthetic.',
      tags: ['Home Decor', 'Minimalist', 'Set'],
      inStock: true,
    },
    {
      id: '5',
      name: 'Professional Camera Lens',
      category: 'Electronics',
      price: 899.99,
      rating: 4.9,
      reviews: 234,
      description: 'High-quality professional camera lens for stunning photography.',
      tags: ['Camera', 'Professional', 'Lens'],
      inStock: true,
    },
    {
      id: '6',
      name: 'Yoga Mat Premium',
      category: 'Sports',
      price: 49.99,
      originalPrice: 69.99,
      rating: 4.5,
      reviews: 789,
      description: 'Eco-friendly premium yoga mat with superior grip and cushioning.',
      tags: ['Yoga', 'Eco-Friendly', 'Premium'],
      inStock: true,
    },
  ]

  const filteredProducts = mockProducts.filter((product) => {
    const matchesSearch = product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      product.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || product.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const toggleFavorite = (productId: string) => {
    setFavorites((prev) =>
      prev.includes(productId)
        ? prev.filter((id) => id !== productId)
        : [...prev, productId]
    )
  }

  const addToCart = (productId: string) => {
    setCart((prev) => [...prev, productId])
  }

  const getDiscount = (price: number, originalPrice?: number) => {
    if (!originalPrice) return 0
    return Math.round(((originalPrice - price) / originalPrice) * 100)
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
            <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
              <ShoppingBag className="w-10 h-10 text-white" />
            </div>
          </motion.div>
          <h1 className="text-4xl sm:text-5xl font-display font-bold text-slate-800 mb-4">
            AI-Powered <span className="text-gradient">Shopping</span>
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Discover products tailored to your preferences with intelligent recommendations
          </p>
        </motion.div>

        {/* AI Features Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-2xl p-6 mb-8 bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200"
        >
          <div className="flex flex-wrap items-center justify-center gap-6">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <span className="font-semibold text-slate-700">AI Recommendations</span>
            </div>
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-purple-600" />
              <span className="font-semibold text-slate-700">Personalized Shopping</span>
            </div>
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-purple-600" />
              <span className="font-semibold text-slate-700">Trending Products</span>
            </div>
          </div>
        </motion.div>

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-8 space-y-4"
        >
          {/* Search Bar */}
          <div className="glass rounded-2xl p-4 flex items-center space-x-4 shadow-lg">
            <Search className="w-6 h-6 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search products, brands, or categories..."
              className="flex-1 bg-transparent border-none outline-none text-slate-700 placeholder-slate-400 text-lg"
            />
            <div className="flex items-center space-x-2">
              <div className="relative">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-3 bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 relative"
                >
                  <ShoppingCart className="w-5 h-5" />
                  {cart.length > 0 && (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold"
                    >
                      {cart.length}
                    </motion.span>
                  )}
                </motion.button>
              </div>
            </div>
          </div>

          {/* Category Filters */}
          <div className="flex items-center space-x-2 overflow-x-auto pb-2">
            <Filter className="w-5 h-5 text-slate-600 flex-shrink-0" />
            {categories.map((category) => (
              <motion.button
                key={category}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedCategory(category.toLowerCase())}
                className={`px-4 py-2 rounded-full font-medium whitespace-nowrap transition-all ${
                  selectedCategory === category.toLowerCase()
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                    : 'glass text-slate-700 hover:bg-white/80'
                }`}
              >
                {category}
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Products Grid */}
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedCategory + searchQuery}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
          >
            {filteredProducts.map((product, index) => {
              const isFavorite = favorites.includes(product.id)
              const isInCart = cart.includes(product.id)
              const discount = getDiscount(product.price, product.originalPrice)

              return (
                <motion.div
                  key={product.id}
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  whileHover={{ y: -10 }}
                  className="glass rounded-2xl overflow-hidden shadow-lg border-2 border-transparent hover:border-purple-200 transition-all group"
                >
                  {/* Product Image */}
                  <div className="relative h-64 bg-gradient-to-br from-purple-400 to-pink-500 overflow-hidden">
                    {discount > 0 && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute top-4 left-4 px-3 py-1 bg-red-500 text-white rounded-full text-sm font-bold z-10"
                      >
                        -{discount}%
                      </motion.div>
                    )}
                    <motion.button
                      whileHover={{ scale: 1.2 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => toggleFavorite(product.id)}
                      className={`absolute top-4 right-4 p-2 rounded-full shadow-lg z-10 ${
                        isFavorite
                          ? 'bg-red-500 text-white'
                          : 'bg-white/90 text-slate-600 hover:bg-white'
                      }`}
                    >
                      <Heart className={`w-5 h-5 ${isFavorite ? 'fill-current' : ''}`} />
                    </motion.button>
                    <div className="absolute inset-0 bg-black/10 group-hover:bg-black/20 transition-colors" />
                  </div>

                  {/* Product Info */}
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-slate-800 group-hover:text-gradient transition-colors mb-1">
                          {product.name}
                        </h3>
                        <p className="text-xs text-slate-500 mb-2">{product.category}</p>
                      </div>
                    </div>

                    <p className="text-sm text-slate-600 mb-4 line-clamp-2">{product.description}</p>

                    {/* Rating */}
                    <div className="flex items-center space-x-2 mb-4">
                      <div className="flex items-center">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            className={`w-4 h-4 ${
                              i < Math.floor(product.rating)
                                ? 'text-yellow-500 fill-yellow-500'
                                : 'text-slate-300'
                            }`}
                          />
                        ))}
                      </div>
                      <span className="text-sm text-slate-600">
                        {product.rating} ({product.reviews})
                      </span>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {product.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-xs font-medium"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>

                    {/* Price and Actions */}
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-2xl font-bold text-gradient">${product.price}</span>
                          {product.originalPrice && (
                            <span className="text-sm text-slate-400 line-through">
                              ${product.originalPrice}
                            </span>
                          )}
                        </div>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => addToCart(product.id)}
                        disabled={isInCart}
                        className={`px-4 py-2 rounded-xl font-semibold transition-all ${
                          isInCart
                            ? 'bg-green-500 text-white'
                            : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg'
                        }`}
                      >
                        {isInCart ? 'In Cart' : 'Add to Cart'}
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </motion.div>
        </AnimatePresence>

        {filteredProducts.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <ShoppingBag className="w-16 h-16 text-slate-400 mx-auto mb-4" />
            <p className="text-xl text-slate-600">No products found. Try different search terms.</p>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default ECommerce
