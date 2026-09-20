# LeadPulse Nexus on Railway

The production deployment uses one repository/image and five Railway resources:

1. PostgreSQL
2. Redis
3. `leadpulse-web`
4. `leadpulse-worker`
5. `leadpulse-beat` (exactly one replica)

## Shared variables

Configure these on all three LeadPulse services:

```text
ENVIRONMENT=production
AUTO_CREATE_SCHEMA=false
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CORS_ORIGINS=https://YOUR_WEB_DOMAIN
```

Configure and seal these on the web and worker services:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SENDER_NAME=...
SENDER_EMAIL=...
```

Optional: set both `ADMIN_USERNAME` and `ADMIN_PASSWORD` on the web service to
enable HTTP Basic authentication. They are deliberately not required or enabled
by default; decide on the operator-access policy before assigning a public domain.

Add Twilio values only if live carrier calls are enabled. Prefer a restricted API
key (`TWILIO_API_KEY` and `TWILIO_API_SECRET`) over the master Auth Token.

## Migration command

Configure this as the web service's Railway pre-deploy command so migrations
run once before a new release becomes active:

```text
alembic upgrade head
```

Do not put the migration in every replica's start command; concurrent schema
migrations can race during a scale-up.

## Service start commands

Web:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Worker:

```text
celery -A app.workers.celery_app:celery_app worker --loglevel=INFO --concurrency=2 --queues=outreach,maintenance,enrichment
```

Scheduler (one replica only):

```text
celery -A app.workers.celery_app:celery_app beat --loglevel=INFO
```

The worker and scheduler do not need public domains. Generate a public domain only
for the web service.

## Import legacy data

Run the schema migration first. From a local shell with `DATABASE_URL` set to a
Railway PostgreSQL TCP Proxy URL (the private URL is only reachable inside the
Railway project):

```text
python -m scripts.migrate_sqlite_to_postgres --source leads.db --dry-run
python -m scripts.migrate_sqlite_to_postgres --source leads.db
```

The importer copies only `leads` and `company_contacts`; it never copies `.env`
or provider credentials. The Docker image intentionally excludes `leads.db`,
so keep the import local unless you explicitly upload a database copy. Take a
PostgreSQL backup after validating counts.

## Health check

Configure Railway's health-check path as `/health`. It verifies that the web
process can query the database.
