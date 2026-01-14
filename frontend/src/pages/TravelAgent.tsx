import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plane, MapPin, Calendar, Users, Search, Hotel, Route, Clock, DollarSign, Star, ChevronRight, UtensilsCrossed } from 'lucide-react'

interface Flight {
  id: string
  airline: string
  departure: string
  arrival: string
  departureTime: string
  arrivalTime: string
  duration: string
  price: number
  stops: number
}

interface Hotel {
  id: string
  name: string
  location: string
  rating: number
  pricePerNight: number
  amenities: string[]
  image?: string
}

interface ItineraryDay {
  day: number
  date: string
  activities: string[]
  meals: string[]
}

const TravelAgent = () => {
  const [activeTab, setActiveTab] = useState<'search' | 'itinerary' | 'bookings'>('search')
  const [searchForm, setSearchForm] = useState({
    origin: '',
    destination: '',
    departureDate: '',
    returnDate: '',
    passengers: 1,
    tripType: 'round_trip',
  })

  // Mock data
  const mockFlights: Flight[] = [
    {
      id: '1',
      airline: 'Sky Airlines',
      departure: 'NYC',
      arrival: 'LON',
      departureTime: '08:00',
      arrivalTime: '20:30',
      duration: '7h 30m',
      price: 650,
      stops: 0,
    },
    {
      id: '2',
      airline: 'Global Airways',
      departure: 'NYC',
      arrival: 'LON',
      departureTime: '14:00',
      arrivalTime: '06:00+1',
      duration: '8h 0m',
      price: 580,
      stops: 1,
    },
  ]

  const mockHotels: Hotel[] = [
    {
      id: '1',
      name: 'Grand Plaza Hotel',
      location: 'London, UK',
      rating: 4.8,
      pricePerNight: 150,
      amenities: ['WiFi', 'Pool', 'Spa', 'Restaurant'],
    },
    {
      id: '2',
      name: 'Riverside Boutique',
      location: 'London, UK',
      rating: 4.6,
      pricePerNight: 120,
      amenities: ['WiFi', 'Breakfast', 'Parking'],
    },
  ]

  const mockItinerary: ItineraryDay[] = [
    {
      day: 1,
      date: '2024-03-15',
      activities: ['Arrival at Heathrow', 'Check-in at hotel', 'Westminster Abbey tour', 'Evening Thames cruise'],
      meals: ['Dinner at The Shard'],
    },
    {
      day: 2,
      date: '2024-03-16',
      activities: ['British Museum', 'Covent Garden', 'Tower of London', 'Tower Bridge'],
      meals: ['Breakfast at hotel', 'Lunch at Borough Market', 'Dinner at Gordon Ramsay'],
    },
  ]

  const handleSearch = () => {
    // In real app, this would call the API
    console.log('Searching...', searchForm)
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
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
              <Plane className="w-10 h-10 text-white" />
            </div>
          </motion.div>
          <h1 className="text-4xl sm:text-5xl font-display font-bold text-slate-800 mb-4">
            AI Travel <span className="text-gradient">Agent</span>
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Plan your perfect trip with AI-powered itinerary planning and bookings
          </p>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex justify-center mb-8"
        >
          <div className="glass rounded-2xl p-2 inline-flex space-x-2">
            {[
              { id: 'search', label: 'Search', icon: Search },
              { id: 'itinerary', label: 'Itinerary', icon: Route },
              { id: 'bookings', label: 'Bookings', icon: Hotel },
            ].map((tab) => {
              const Icon = tab.icon
              return (
                <motion.button
                  key={tab.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                    activeTab === tab.id
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg'
                      : 'text-slate-700 hover:bg-white/50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </motion.button>
              )
            })}
          </div>
        </motion.div>

        {/* Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'search' && (
            <motion.div
              key="search"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-8"
            >
              {/* Search Form */}
              <div className="glass rounded-2xl p-8 shadow-lg">
                <div className="grid md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      <MapPin className="w-4 h-4 inline mr-1" />
                      From
                    </label>
                    <input
                      type="text"
                      value={searchForm.origin}
                      onChange={(e) => setSearchForm({ ...searchForm, origin: e.target.value })}
                      placeholder="City or Airport"
                      className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:outline-none transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      <MapPin className="w-4 h-4 inline mr-1" />
                      To
                    </label>
                    <input
                      type="text"
                      value={searchForm.destination}
                      onChange={(e) => setSearchForm({ ...searchForm, destination: e.target.value })}
                      placeholder="City or Airport"
                      className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:outline-none transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      <Calendar className="w-4 h-4 inline mr-1" />
                      Departure
                    </label>
                    <input
                      type="date"
                      value={searchForm.departureDate}
                      onChange={(e) => setSearchForm({ ...searchForm, departureDate: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:outline-none transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      <Calendar className="w-4 h-4 inline mr-1" />
                      Return
                    </label>
                    <input
                      type="date"
                      value={searchForm.returnDate}
                      onChange={(e) => setSearchForm({ ...searchForm, returnDate: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:outline-none transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      <Users className="w-4 h-4 inline mr-1" />
                      Passengers
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={searchForm.passengers}
                      onChange={(e) => setSearchForm({ ...searchForm, passengers: parseInt(e.target.value) })}
                      className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:outline-none transition-colors"
                    />
                  </div>
                </div>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleSearch}
                  className="w-full py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl font-semibold text-lg shadow-lg"
                >
                  Search Flights & Hotels
                </motion.button>
              </div>

              {/* Flights */}
              <div>
                <h2 className="text-2xl font-bold text-slate-800 mb-4">Available Flights</h2>
                <div className="space-y-4">
                  {mockFlights.map((flight, index) => (
                    <motion.div
                      key={flight.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ scale: 1.02 }}
                      className="glass rounded-2xl p-6 border-2 border-transparent hover:border-blue-200 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-6">
                          <div className="text-center">
                            <div className="text-2xl font-bold text-slate-800">{flight.departureTime}</div>
                            <div className="text-sm text-slate-600">{flight.departure}</div>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <Clock className="w-4 h-4 text-slate-600" />
                              <span className="text-sm text-slate-600">{flight.duration}</span>
                              {flight.stops > 0 && (
                                <span className="text-sm text-orange-600">{flight.stops} stop(s)</span>
                              )}
                            </div>
                            <div className="h-1 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full" />
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-slate-800">{flight.arrivalTime}</div>
                            <div className="text-sm text-slate-600">{flight.arrival}</div>
                          </div>
                        </div>
                        <div className="text-right ml-6">
                          <div className="text-3xl font-bold text-gradient mb-1">${flight.price}</div>
                          <div className="text-sm text-slate-600 mb-3">{flight.airline}</div>
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold"
                          >
                            Select
                          </motion.button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Hotels */}
              <div>
                <h2 className="text-2xl font-bold text-slate-800 mb-4">Recommended Hotels</h2>
                <div className="grid md:grid-cols-2 gap-6">
                  {mockHotels.map((hotel, index) => (
                    <motion.div
                      key={hotel.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ y: -5 }}
                      className="glass rounded-2xl overflow-hidden border-2 border-transparent hover:border-blue-200 transition-all"
                    >
                      <div className="h-48 bg-gradient-to-br from-blue-400 to-cyan-500 relative">
                        <div className="absolute top-4 right-4 flex items-center space-x-1 px-3 py-1 bg-white/90 rounded-full">
                          <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                          <span className="text-sm font-semibold">{hotel.rating}</span>
                        </div>
                      </div>
                      <div className="p-6">
                        <h3 className="text-xl font-bold text-slate-800 mb-2">{hotel.name}</h3>
                        <div className="flex items-center text-slate-600 mb-4">
                          <MapPin className="w-4 h-4 mr-1" />
                          <span className="text-sm">{hotel.location}</span>
                        </div>
                        <div className="flex flex-wrap gap-2 mb-4">
                          {hotel.amenities.map((amenity) => (
                            <span
                              key={amenity}
                              className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs"
                            >
                              {amenity}
                            </span>
                          ))}
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-2xl font-bold text-gradient">${hotel.pricePerNight}</div>
                            <div className="text-sm text-slate-600">per night</div>
                          </div>
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold"
                          >
                            Book Now
                          </motion.button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'itinerary' && (
            <motion.div
              key="itinerary"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div className="glass rounded-2xl p-8 shadow-lg">
                <h2 className="text-3xl font-bold text-slate-800 mb-6">Your Itinerary</h2>
                <div className="space-y-6">
                  {mockItinerary.map((day, index) => (
                    <motion.div
                      key={day.day}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="border-l-4 border-blue-500 pl-6 relative"
                    >
                      <div className="absolute -left-3 w-6 h-6 bg-blue-500 rounded-full border-4 border-white" />
                      <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-2xl font-bold text-slate-800">Day {day.day}</h3>
                          <span className="text-slate-600">{day.date}</span>
                        </div>
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-semibold text-slate-700 mb-2 flex items-center">
                              <Route className="w-4 h-4 mr-2" />
                              Activities
                            </h4>
                            <ul className="space-y-2">
                              {day.activities.map((activity, i) => (
                                <li key={i} className="flex items-center text-slate-600">
                                  <ChevronRight className="w-4 h-4 mr-2 text-blue-500" />
                                  {activity}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <h4 className="font-semibold text-slate-700 mb-2 flex items-center">
                              <UtensilsCrossed className="w-4 h-4 mr-2" />
                              Meals
                            </h4>
                            <ul className="space-y-2">
                              {day.meals.map((meal, i) => (
                                <li key={i} className="flex items-center text-slate-600">
                                  <ChevronRight className="w-4 h-4 mr-2 text-orange-500" />
                                  {meal}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'bookings' && (
            <motion.div
              key="bookings"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="text-center py-20"
            >
              <Hotel className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <p className="text-xl text-slate-600">Your bookings will appear here</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default TravelAgent
