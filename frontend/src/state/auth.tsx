import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react"
import { api } from "../lib/api"
import { getStoredUser, getToken, setStoredUser, setToken } from "../lib/session"
import type { Profile, ProfilePayload, UserInfo } from "../lib/types"

interface AuthCtx {
  user: UserInfo | null
  profile: Profile | null
  onboarded: boolean
  ready: boolean
  isDemoMode: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  startDemo: () => Promise<void>
  saveProfile: (p: ProfilePayload) => Promise<Profile>
  refreshProfile: () => Promise<void>
  logout: () => void
}

const Ctx = createContext<AuthCtx>(null as unknown as AuthCtx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(getStoredUser())
  const [profile, setProfile] = useState<Profile | null>(null)
  const [ready, setReady] = useState(false)

  const loadProfile = useCallback(async () => {
    try {
      setProfile(await api.getProfile())
    } catch {
      setProfile(null)
    }
  }, [])

  // Fetch the profile, then set user + profile together so `onboarded` is correct on
  // the first render — no window where the user is signed in but profile is still null.
  const setSession = useCallback(async (u: UserInfo) => {
    let p: Profile | null = null
    try {
      p = await api.getProfile()
    } catch {
      p = null
    }
    setStoredUser(u)
    setProfile(p)
    setUser(u)
  }, [])

  useEffect(() => {
    if (!getToken()) {
      setReady(true)
      return
    }
    api
      .me()
      .then(setSession)
      .catch(() => {
        setToken(null)
        setStoredUser(null)
        setUser(null)
      })
      .finally(() => setReady(true))
  }, [setSession])

  const finishLogin = useCallback(
    async (email: string, password: string) => {
      const tok = await api.login(email, password)
      setToken(tok.access_token)
      await setSession(await api.me())
    },
    [setSession],
  )

  const login = finishLogin

  const register = useCallback(
    async (email: string, password: string) => {
      await api.register(email, password)
      await finishLogin(email, password)
    },
    [finishLogin],
  )

  const startDemo = useCallback(async () => {
    const tok = await api.demoLogin()
    setToken(tok.access_token)
    await setSession(await api.me())
  }, [setSession])

  const saveProfile = useCallback(async (p: ProfilePayload) => {
    const saved = await api.saveProfile(p)
    setProfile(saved)
    return saved
  }, [])

  const logout = useCallback(() => {
    api.logout().catch(() => {})
    setToken(null)
    setStoredUser(null)
    setUser(null)
    setProfile(null)
  }, [])

  return (
    <Ctx.Provider
      value={{
        user,
        profile,
        onboarded: !!profile?.onboarded,
        ready,
        isDemoMode: user?.email === "demo@kensho.app",
        login,
        register,
        startDemo,
        saveProfile,
        refreshProfile: loadProfile,
        logout,
      }}
    >
      {children}
    </Ctx.Provider>
  )
}

export const useAuth = () => useContext(Ctx)
