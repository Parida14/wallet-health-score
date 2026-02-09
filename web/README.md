# Wallet Health Score Dashboard

A Next.js 15 web dashboard for visualizing on-chain wallet health scores.

## Features

- **Wallet Search**: Look up any Ethereum wallet address
- **Score Visualization**: Circular gauge showing overall health score (0-100)
- **Component Breakdown**: Radar chart and bar charts for 5 score components
  - Activity
  - Diversification
  - Risk
  - Profitability
  - Stability
- **Historical Trends**: Line/area charts showing score history over time
- **Wallet Comparison**: Compare multiple wallets side by side

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui + Radix UI
- **Charts**: Recharts
- **State Management**: nuqs (URL search params)

## Getting Started

### Prerequisites

- Node.js 20+
- npm
- Backend API running on `http://localhost:8000`

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

Create a `.env.local` file:

```env
# API URL (defaults to http://localhost:8000)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Docker

The app can be run in Docker as part of the full stack:

```bash
# From the infra directory
docker-compose up -d web
```

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Home page with search
│   ├── wallet/[address]/  # Wallet detail page
│   └── compare/           # Multi-wallet comparison
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── score-gauge.tsx   # Circular score gauge
│   ├── component-radar.tsx # Radar chart
│   ├── component-bars.tsx # Bar chart breakdown
│   ├── history-chart.tsx # Historical line chart
│   ├── score-card.tsx    # Complete score card
│   └── wallet-search.tsx # Search input
├── lib/                   # Utilities
│   ├── api.ts            # API client
│   └── utils.ts          # Helper functions
└── types/                 # TypeScript types
    └── wallet.ts         # Wallet data models
```

## Sample Wallets

The app includes sample wallet addresses for testing:

| Label | Address |
|-------|---------|
| vitalik.eth | `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` |
| Ethereum Foundation | `0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe` |
| Uniswap Treasury | `0x1a9C8182C09F50C8318d769245beA52c32BE35BC` |
| Binance Hot Wallet | `0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503` |
| Binance Cold Wallet | `0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8` |

## API Endpoints Used

- `GET /score/{address}` - Get wallet health score
- `GET /history/{address}?days=30` - Get score history
- `POST /compare` - Compare multiple wallets
- `GET /health` - API health check

## License

MIT
