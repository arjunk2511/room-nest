# RoomNest Production Deployment & Backup Guide

This document outlines the deployment process, database schema migrations, and backup configurations for the RoomNest application in a live production environment.

---

## 1. Production Architecture Overview

The application utilizes a **fail-closed, provider-agnostic Django settings architecture**:
1. **No SQLite Fallback:** At runtime, the production container blocks startup if `DATABASE_URL` is missing or if the active database is configured to SQLite.
2. **Build-Time Bypassing:** Static assets compilation (`collectstatic`) runs cleanly at build-time using a dummy SQLite layout to compile without requiring an active database socket.
3. **Cross-Service Variable Referencing:** The web app container references the PostgreSQL service variables using Railway’s dynamic variables mapping, eliminating hardcoded credentials in the repository.

---

## 2. Production Deployment Steps

Every deployment or code push to GitHub follows this automated execution sequence on the startup dyno:
1. **`python manage.py migrate --no-input`:** Applies all database schema changes against PostgreSQL first.
2. **`python verify_production_db.py`:** Runs structural assertions, logs startup environment variables (masked), outputs the active database connections parameters, and checks migration status.
3. **`python create_superuser.py`:** Restores or initializes the administrative superuser account securely.
4. **`python verify_deployment.py`:** Executes post-deployment diagnostic checks (verifies users/owners counts, images metadata, tests login post form flow, and dashboard HTTP page rendering).
5. **`gunicorn roomnest.wsgi:application`:** Starts Gunicorn to serve the web application.

---

## 3. Database Backup & Recovery Strategy

To ensure zero data loss in production, implement the following backup policy:

### Automatic PostgreSQL Backups on Railway
1. Log into your **Railway Dashboard**.
2. Select your project and click on the **PostgreSQL service** node.
3. Select the **Backups** tab.
4. Enable **Automatic Backups** (Railway provides daily automatic snapshots).

### Manual PostgreSQL Backups
Before deploying major schema modifications or database refactoring, execute a manual backup using standard database dumping utilities:
```bash
# Export schema and data from the database
pg_dump -H <host> -U <user> -d <database> -F c -b -v -f roomnest_prod_backup.dump
```

### Restoring a Database Backup
To restore a snapshot in the event of an outage or data discrepancy:
- **On Railway:** Go to `Postgres` -> `Backups` -> Click `Restore` on the latest successful snapshot.
- **Via CLI:**
  ```bash
  pg_restore -H <host> -U <user> -d <database> -v roomnest_prod_backup.dump
  ```
