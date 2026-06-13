import { Component, type ErrorInfo, type ReactNode } from "react"
import { Mark } from "./Logo"

interface Props {
  children: ReactNode
}
interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error("Kensho caught a render error:", error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-5 px-6 text-center">
          <Mark className="h-12 w-12 text-ink" animate={false} />
          <div>
            <h1 className="font-display text-3xl">Something slipped.</h1>
            <p className="mt-2 max-w-sm text-pretty text-ink-soft">
              A part of Kensho hit an unexpected error. Reload to get back to your atlas of taste.
            </p>
          </div>
          <button
            onClick={() => {
              this.setState({ error: null })
              window.location.assign("/")
            }}
            className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-paper-card transition hover:bg-saffron"
          >
            Back to safety
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
