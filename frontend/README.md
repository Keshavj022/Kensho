# Kensho — frontend

The web client for Kensho — an AI atlas for taste. A React single-page app that talks
to the FastAPI backend and renders the four experiences: **Eat**, **Go**, **Buy**, and
the conversational **assistant**.

> For the product overview and architecture, see the [main README](../README.md).

## Stack

- **React 18** + **TypeScript**
- **Vite** — dev server and build
- **Tailwind CSS** — styling
- **Framer Motion** — animation
- **React Router** — routing
- **Lucide** — icons

## Getting started

```bash
npm install
npm run dev        # → http://localhost:5173
```

The dev server proxies `/api` and `/health` to the backend on `http://localhost:8000`,
so run the backend (see the main README) alongside it.

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Start the Vite dev server |
| `npm run build` | Type-check (`tsc`) and build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint |

## Configuration

The API base URL is resolved from `VITE_API_BASE_URL`:

- **Local dev** — leave it unset; requests go to `/api/v1` and Vite proxies to `:8000`.
- **Split hosting** — set `VITE_API_BASE_URL` to the backend's origin at build time
  (when the frontend is served from a different host than the API).

In the default deployment the backend serves this app from the same origin, so no base
URL is needed.

## Structure

```
src/
├── pages/        # Home, Auth, Dashboard, Profile, Restaurants, RestaurantDetail,
│                 #   Travel, Shopping, Assistant
├── components/   # Nav, Chat, CartDrawer, VoiceAssistant, Onboarding, UI kit, fx…
├── state/        # auth, cart, chat context providers
├── lib/          # API client, types, helpers
└── index.css     # Tailwind layers + design tokens
```
