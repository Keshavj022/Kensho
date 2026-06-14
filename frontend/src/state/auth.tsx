import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react"
import { api } from "../lib/api"
import { DEMO_USER, endDemoSession, getDemoProfile, isDemo, setDemoProfile, startDemoSession } from "../lib/demo"
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
  startDemo: () => void
  saveProfile: (p: ProfilePayload) => Promise<Profile>
  refreshProfile: () => Promise<void>
  logout: () => void
}

const Ctx = createContext<AuthCtx>(null as unknown as AuthCtx)

export function AuthProvider({ children }: { children: ReactNode }) {
  // An ephemeral demo session is only honored when there's no real token (real auth always wins).
  const demoActive = isDemo() && !getToken()
  const [user, setUser] = useState<UserInfo | null>(() => (demoActive ? DEMO_USER : getStoredUser()))
  const [profile, setProfile] = useState<Profile | null>(() => (demoActive ? getDemoProfile() : null))
  const [demo, setDemo] = useState(demoActive)
  const [ready, setReady] = useState(false)

  const loadProfile = useCallback(async () => {
    if (isDemo()) {
      setProfile(getDemoProfile())
      return
    }
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
    if (getToken()) {
      endDemoSession() // a real token supersedes any stale demo flag
      api
        .me()
        .then(setSession)
        .catch(() => {
          setToken(null)
          setStoredUser(null)
          setUser(null)
        })
        .finally(() => setReady(true))
      return
    }
    if (isDemo()) {
      // Restore the ephemeral guest after a refresh (sessionStorage survives reloads, not tab close).
      setUser(DEMO_USER)
      setProfile(getDemoProfile())
      setDemo(true)
    }
    setReady(true)
  }, [setSession])

  const finishLogin = useCallback(
    async (email: string, password: string) => {
      endDemoSession() // leaving the demo for a real account
      setDemo(false)
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

  // Enter the live demo: a client-only guest. No backend account, no token, nothing persisted.
  const startDemo = useCallback(() => {
    setToken(null)
    setStoredUser(null)
    const p = startDemoSession()
    setUser(DEMO_USER)
    setProfile(p)
    setDemo(true)
    setReady(true)
  }, [])

  const saveProfile = useCallback(async (p: ProfilePayload) => {
    if (isDemo()) {
      const saved = setDemoProfile(p as Partial<Profile>)
      setProfile(saved)
      return saved
    }
    const saved = await api.saveProfile(p)
    setProfile(saved)
    return saved
  }, [])

  const logout = useCallback(() => {
    if (isDemo()) {
      endDemoSession()
      setDemo(false)
      setUser(null)
      setProfile(null)
      return
    }
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
        isDemoMode: demo,
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
