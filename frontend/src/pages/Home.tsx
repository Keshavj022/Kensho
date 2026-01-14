import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowRight, Sparkles, UtensilsCrossed, Plane, ShoppingBag, Zap, Brain, Globe } from 'lucide-react'

const Home = () => {
  const features = [
    {
      icon: UtensilsCrossed,
      title: 'Food Recommendations',
      description: 'AI-powered restaurant discovery with personalized menu suggestions',
      color: 'from-orange-500 to-red-500',
      link: '/food',
    },
    {
      icon: Plane,
      title: 'Travel Agent',
      description: 'Intelligent itinerary planning with flight and hotel bookings',
      color: 'from-blue-500 to-cyan-500',
      link: '/travel',
    },
    {
      icon: ShoppingBag,
      title: 'E-Commerce',
      description: 'Smart shopping experience with AI-powered product recommendations',
      color: 'from-purple-500 to-pink-500',
      link: '/shop',
    },
  ]

  const capabilities = [
    { icon: Brain, text: 'AI-Powered Agents' },
    { icon: Zap, text: 'Real-time Recommendations' },
    { icon: Globe, text: 'Multimodal Support' },
    { icon: Sparkles, text: 'Voice Interface' },
  ]

  return (
    <div className="relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: 'linear',
          }}
          className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/30 to-purple-600/30 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1.2, 1, 1.2],
            rotate: [90, 0, 90],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: 'linear',
          }}
          className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-br from-pink-400/30 to-orange-600/30 rounded-full blur-3xl"
        />
      </div>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 pt-20">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-8"
          >
            {/* Main heading */}
            <motion.h1
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-display font-bold"
            >
              <span className="text-gradient">Kensho</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="text-xl sm:text-2xl text-slate-600 max-w-3xl mx-auto"
            >
              Experience the future of shopping with AI agents that understand your needs,
              <br className="hidden sm:block" />
              recommend personalized options, and make every interaction seamless.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center"
            >
              <Link to="/food">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="group px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full font-semibold text-lg shadow-lg shadow-purple-500/50 flex items-center space-x-2"
                >
                  <span>Get Started</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </motion.button>
              </Link>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-8 py-4 glass text-slate-700 rounded-full font-semibold text-lg border-2 border-slate-200"
              >
                Learn More
              </motion.button>
            </motion.div>

            {/* Capabilities */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.8 }}
              className="flex flex-wrap justify-center gap-6 pt-8"
            >
              {capabilities.map((cap, index) => {
                const Icon = cap.icon
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.9 + index * 0.1 }}
                    whileHover={{ scale: 1.1, y: -5 }}
                    className="flex items-center space-x-2 glass px-4 py-2 rounded-full"
                  >
                    <Icon className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium text-slate-700">{cap.text}</span>
                  </motion.div>
                )
              })}
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl sm:text-5xl font-display font-bold text-slate-800 mb-4">
              Three Powerful <span className="text-gradient">Services</span>
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Choose from our AI-powered services designed to enhance your lifestyle
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 50 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                  whileHover={{ y: -10 }}
                  className="group"
                >
                  <Link to={feature.link}>
                    <div className="glass rounded-2xl p-8 h-full border-2 border-transparent hover:border-blue-200 transition-all cursor-pointer">
                      <motion.div
                        whileHover={{ rotate: [0, -10, 10, -10, 0] }}
                        transition={{ duration: 0.5 }}
                        className={`w-16 h-16 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center mb-6 shadow-lg`}
                      >
                        <Icon className="w-8 h-8 text-white" />
                      </motion.div>
                      <h3 className="text-2xl font-bold text-slate-800 mb-3 group-hover:text-gradient transition-colors">
                        {feature.title}
                      </h3>
                      <p className="text-slate-600 mb-4">{feature.description}</p>
                      <div className="flex items-center text-blue-600 font-semibold group-hover:translate-x-2 transition-transform">
                        Explore <ArrowRight className="w-4 h-4 ml-2" />
                      </div>
                    </div>
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: '10K+', label: 'Active Users' },
              { value: '50K+', label: 'Recommendations' },
              { value: '99%', label: 'Satisfaction' },
              { value: '24/7', label: 'AI Support' },
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="text-center"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  whileInView={{ scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 + 0.2, type: 'spring' }}
                  className="text-4xl md:text-5xl font-bold text-gradient mb-2"
                >
                  {stat.value}
                </motion.div>
                <div className="text-slate-600 font-medium">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home
