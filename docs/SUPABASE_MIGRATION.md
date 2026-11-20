# CYNERA — Supabase PostgreSQL Migration Guide

CYNERA is architected with complete database portability. The SQLAlchemy models and `database/schema.sql` file natively support both persistent local SQLite and enterprise cloud **Supabase PostgreSQL** without code refactoring.

---

## 1. Prerequisites

1. A [Supabase](https://supabase.com/) account and project.
2. Your Supabase PostgreSQL database connection URI, found in:
   `Project Settings -> Database -> Connection string -> URI`
   Format:
   ```
   postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```

---

## 2. Step 1: Provision the Supabase Schema

Open the Supabase **SQL Editor** in your browser and execute the complete DDL schema located at:
```
database/schema.sql
```
*(All foreign key relationships, cascade rules, JSON fields, and indexes are pre-configured.)*

---

## 3. Step 2: Configure Environment Variables

Update `backend/.env` with your Supabase connection string:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Or via PgBouncer Connection Pooler (Recommended for Serverless)
# DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?pgbouncer=true
```

CYNERA's `backend/app/database.py` automatically detects `postgresql://` and adjusts connection pooling (`pool_size=10, max_overflow=20`) instead of SQLite file locks.

---

## 4. Step 3: Data Migration Script (SQLite → Supabase)

To migrate your existing organizations, users, and monitoring targets from `backend/cynera.db` into Supabase:

Run the included migration utility:
```powershell
python backend/scripts/migrate_sqlite_to_postgres.py --sqlite backend/cynera.db --target "$env:DATABASE_URL"
```

The script copies records in dependency order:
1. `organizations`
2. `tenants`
3. `profiles`
4. `monitored_websites` & `website_endpoints`
5. `network_devices`
6. `application_services`
7. `database_integrations`
8. `alerts` & `webhooks`

---

## 5. Step 4: Verification

Restart the backend server:
```powershell
python backend/run.py
```

Test database connectivity:
```powershell
pytest backend/tests/test_saas_products.py -v
```

All 21 backend tests will execute against your live Supabase PostgreSQL instance.

