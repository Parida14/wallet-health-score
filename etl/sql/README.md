# Database Schema

Phase 1 introduces the core relational schema used by the scoring pipeline. Apply `001_init_schema.sql` to Postgres before running ETL jobs:

```bash
psql "$DATABASE_URL" -f etl/sql/001_init_schema.sql
```

Tables included:

- `wallets` — wallet metadata and lifecycle timestamps.
- `transactions` — on-chain transactions enriched with costs and touched contracts.
- `positions` — token/protocol holdings with USD valuations.
- `features_daily` — precalculated component/total scores per wallet/date.

Future migrations should be appended as `002_*.sql` files to preserve ordering.
