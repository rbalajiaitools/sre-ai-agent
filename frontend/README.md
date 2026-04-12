# SRE AI Agent - Frontend

Enterprise-grade multi-tenant SaaS platform for AI-powered incident investigation.

## Tech Stack

- **React 18** + **TypeScript** (strict mode)
- **Vite** for build tooling
- **React Router v6** for navigation
- **TanStack Query v5** for server state management
- **Zustand** for client state (auth, UI)
- **Tailwind CSS** for styling
- **shadcn/ui** for component primitives
- **React Hook Form** + **Zod** for forms
- **Axios** for API client

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Environment Variables

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=SRE AI Agent
```

## Project Structure

```
src/
├── api/              # Axios client + API functions
├── components/
│   ├── ui/          # shadcn primitives (auto-generated)
│   └── shared/      # Shared components
├── features/        # Feature modules (future)
├── hooks/           # Custom hooks
├── lib/             # Utilities
├── pages/           # Page components
├── router/          # Route definitions
├── stores/          # Zustand stores
└── types/           # TypeScript types
```

## Module 1 - Complete ✓

### Implemented Features

- ✓ Project scaffold with Vite + React + TypeScript
- ✓ Tailwind CSS with custom design tokens
- ✓ shadcn/ui components (Button, Input, Label, Avatar, DropdownMenu)
- ✓ React Router v6 with protected routes
- ✓ TanStack Query provider
- ✓ Zustand stores (auth, app state)
- ✓ Axios client with interceptors
- ✓ AppLayout with collapsible sidebar
- ✓ Login page with form validation
- ✓ Placeholder pages for all routes

### Routes

- `/` → Redirects to `/chat`
- `/login` → Login page (public)
- `/onboarding` → Onboarding (auth required)
- `/chat` → Chat interface
- `/incidents` → Incidents list
- `/investigations` → Investigations list
- `/topology` → Service topology
- `/dashboard` → Analytics dashboard
- `/settings` → Settings

### API Client

The Axios client (`src/api/client.ts`) includes:
- Automatic Bearer token attachment
- 401 handling (logout + redirect)
- 5xx error transformation
- Typed API wrappers

### State Management

**Auth Store** (`src/stores/authStore.ts`):
- Persisted to localStorage
- Stores: user, token, tenant, isAuthenticated
- Actions: login(), logout(), setTenant()

**App Store** (`src/stores/appStore.ts`):
- UI state: activeChatId, sidebarCollapsed
- Actions: setActiveChatId(), toggleSidebar()

## Development

```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Next Modules

- **Module 2**: Chat interface with streaming
- **Module 3**: Incidents list with filters
- **Module 4**: Investigations detail view
- **Module 5**: Service topology graph (React Flow)
- **Module 6**: Analytics dashboard (Recharts)
- **Module 7**: Settings and configuration

## Design Principles

- Clean, minimal enterprise SaaS aesthetic
- Dark mode support (CSS variables)
- Mobile-responsive (desktop-first)
- Loading, error, and empty states for all data
- No hardcoded colors (Tailwind semantic tokens only)
- TypeScript strict mode (no `any` types)
- Accessibility (ARIA labels, keyboard navigation)
