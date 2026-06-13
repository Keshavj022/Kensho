import React from "react"
import ReactDOM from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import App from "./App.tsx"
import { ErrorBoundary } from "./components/ErrorBoundary.tsx"
import { VoiceProvider } from "./components/VoiceAssistant.tsx"
import { AuthProvider } from "./state/auth.tsx"
import { CartProvider } from "./state/cart.tsx"
import { ChatProvider } from "./state/chat.tsx"
import "./index.css"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ErrorBoundary>
        <AuthProvider>
          <CartProvider>
            <ChatProvider>
              <VoiceProvider>
                <App />
              </VoiceProvider>
            </ChatProvider>
          </CartProvider>
        </AuthProvider>
      </ErrorBoundary>
    </BrowserRouter>
  </React.StrictMode>,
)
