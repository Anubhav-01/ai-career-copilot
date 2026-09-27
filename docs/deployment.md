# Deployment

## Recommended topology

```
Frontend (Next.js)   → Vercel (or any Node/Docker host)
Backend (FastAPI)    → Fly.io / Render / Railway / ECS (Docker image provided)
PostgreSQL + pgvector→ Managed Postgres with pgvector (Neon, Supabase, RDS + extension)
Redis                → Managed Redis (Upstash, Elasticache) — optional
```

## Backend

1. Build the image (with real embeddings):

   ```bash
   docker build apps/api --build-arg INSTALL_ML=true -t career-copilot-api
   ```

2. Provision managed Postgres, enable the extension (most providers:
   `CREATE EXTENSION vector;` — the migration also attempts this).

3. Set environment variables (never commit them):

   ```
   DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db
   JWT_SECRET=<64+ random chars>
   LLM_PROVIDER=openai
   LLM_API_KEY=<key>
   EMBEDDING_PROVIDER=sentence-transformer
   REDIS_URL=rediss://...
   CORS_ORIGINS=https://your-frontend-domain
   ENVIRONMENT=production
   ```

4. The container entrypoint runs `alembic upgrade head` before starting
   uvicorn. For multi-replica deployments, run migrations as a separate release
   step instead and change the CMD to plain uvicorn.

5. Uploads are written to `/app/uploads` — mount a volume, or (recommended for
   real production) swap the storage path logic in `ResumeService.upload` for
   S3-compatible object storage.

## Frontend (Vercel)

- Root directory: `apps/web`
- Build command: `npm run build` · Output: default Next.js
- Env var: `NEXT_PUBLIC_API_URL=https://api.your-domain.com`
  (build-time — it is baked into the client bundle)

Or use the provided `apps/web/Dockerfile` (standalone output, ~120MB image).

## Production checklist

- [ ] Strong unique `JWT_SECRET`; HTTPS everywhere
- [ ] `CORS_ORIGINS` restricted to the real frontend origin
- [ ] `ENVIRONMENT=production` (no debug)
- [ ] Managed Postgres backups enabled; pgvector extension active
- [ ] Rate limiting backed by Redis if running >1 API replica
- [ ] Log drain / aggregation for the JSON logs (they are one-object-per-line)
- [ ] `GET /health` wired to the platform health check
- [ ] LLM budget alarms on the provider account
