import { AnimatePresence, motion } from "framer-motion"
import { useEffect } from "react"
import { Navigate, Route, Routes, useLocation } from "react-router-dom"
import { AssistantDock } from "./components/AssistantDock"
import { CartDrawer } from "./components/CartDrawer"
import { Footer } from "./components/Footer"
import { Nav } from "./components/Nav"
import { RequireAuth } from "./components/RequireAuth"
import { Grain } from "./components/fx"
import { Assistant } from "./pages/Assistant"
import { Auth } from "./pages/Auth"
import { Dashboard } from "./pages/Dashboard"
import { Home } from "./pages/Home"
import { Profile } from "./pages/Profile"
import { RestaurantDetail } from "./pages/RestaurantDetail"
import { Restaurants } from "./pages/Restaurants"
import { Shopping } from "./pages/Shopping"
import { Travel } from "./pages/Travel"
import { useAuth } from "./state/auth"

function ScrollTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior })
  }, [pathname])
  return null
}

/** The landing page is for guests. Signed-in, onboarded diners get their dashboard.
 *  Render nothing until auth resolves so the landing never flashes before redirect. */
function HomeGate() {
  const { user, onboarded, ready } = useAuth()
  if (!ready) return null
  if (user && onboarded) return <Navigate to="/dashboard" replace />
  return <Home />
}

export default function App() {
  const location = useLocation()
  const isAuth = location.pathname.startsWith("/auth")

  return (
    <>
      <Grain />
      <Nav />
      <ScrollTop />
      <CartDrawer />
      <AssistantDock />

      <main className="min-h-screen">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname.split("/")[1] || "home"}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
          >
            <Routes location={location}>
              <Route path="/" element={<HomeGate />} />
              <Route path="/auth" element={<Auth />} />
              <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
              <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
              <Route path="/restaurants" element={<RequireAuth><Restaurants /></RequireAuth>} />
              <Route path="/restaurants/:placeId" element={<RequireAuth><RestaurantDetail /></RequireAuth>} />
              <Route path="/travel" element={<RequireAuth><Travel /></RequireAuth>} />
              <Route path="/shopping" element={<RequireAuth><Shopping /></RequireAuth>} />
              <Route path="/assistant" element={<RequireAuth><Assistant /></RequireAuth>} />
              <Route path="*" element={<HomeGate />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>

      {!isAuth && <Footer />}
    </>
  )
}
