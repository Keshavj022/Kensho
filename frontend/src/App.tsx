import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import FoodRecommendations from './pages/FoodRecommendations'
import TravelAgent from './pages/TravelAgent'
import ECommerce from './pages/ECommerce'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/food" element={<FoodRecommendations />} />
          <Route path="/travel" element={<TravelAgent />} />
          <Route path="/shop" element={<ECommerce />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
