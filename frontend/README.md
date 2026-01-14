# Frontend - Kensho

> **Note**: For complete project documentation, see the [main README](../README.md)

A beautiful, modern, and animated frontend for an AI-powered e-commerce platform with multiple agent services.

## Features

- 🎨 **Modern UI/UX**: Beautiful, aesthetic design with smooth animations
- 🚀 **Fast Performance**: Built with Vite and React for optimal performance
- 🎭 **Animations**: Framer Motion for smooth, eye-catching animations
- 📱 **Responsive**: Fully responsive design that works on all devices
- 🎯 **Three Main Services**:
  - **Food Recommendations**: AI-powered restaurant discovery
  - **Travel Agent**: Intelligent itinerary planning and bookings
  - **E-Commerce**: Smart shopping with personalized recommendations

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **React Router** - Navigation
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

3. Start the development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

4. Open your browser and visit `http://localhost:5173`

### Build for Production

```bash
npm run build
# or
yarn build
# or
pnpm build
```

The built files will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable components
│   │   └── Layout.tsx  # Main layout with navigation
│   ├── pages/          # Page components
│   │   ├── Home.tsx              # Landing page
│   │   ├── FoodRecommendations.tsx
│   │   ├── TravelAgent.tsx
│   │   └── ECommerce.tsx
│   ├── utils/          # Utility functions
│   ├── App.tsx         # Main app component with routing
│   ├── main.tsx        # Entry point
│   └── index.css       # Global styles
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

## Features Overview

### Landing Page
- Animated hero section with gradient backgrounds
- Feature showcase cards
- Statistics section
- Smooth scroll animations

### Food Recommendations
- Search functionality with voice input UI
- Filter by dietary preferences and cuisine
- Restaurant cards with ratings and details
- Image upload UI for multimodal support

### Travel Agent
- Flight and hotel search
- Interactive itinerary planning
- Booking management
- Tab-based navigation

### E-Commerce
- Product search and filtering
- Shopping cart functionality
- Favorites/wishlist
- AI recommendations banner
- Category-based browsing

## Design Philosophy

The frontend is designed to be:
- **Beautiful**: Modern, aesthetic design with gradients and glassmorphism
- **Animated**: Smooth animations throughout for better UX
- **Independent**: Completely standalone, no backend connections
- **Accessible**: Clean, readable code with proper semantic HTML

## Future Enhancements

When connecting to the backend:
- API integration for real data
- Authentication and user profiles
- Real-time chat interfaces
- Voice input/output functionality
- Image analysis features

## License

This project is part of the Kensho platform.
