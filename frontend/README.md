# ForecastReview — Frontend

Next.js 16 (App Router) frontend for the ForecastReview investment system.

## Setup

**1. Install dependencies**

```bash
npm install
```

**2. Configure environment**

```bash
cp .env.example .env
```

Then open `.env` and set `BACKEND_URL` to point at your running backend instance (default is `http://localhost:8000` which works for local development).

**3. Start the dev server**

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The app redirects to `/dashboard` on load.

> The backend must be running before the frontend starts, as server-side data fetching hits the backend directly at startup.

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `BACKEND_URL` | URL of the backend — server-side only, never sent to the browser | `http://localhost:8000` |

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
