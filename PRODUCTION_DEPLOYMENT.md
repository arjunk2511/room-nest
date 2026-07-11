# Production Deployment Guide

## Safe Deployment Process
1. Ensure PostgreSQL is configured via DATABASE_URL or PGHOST/PGUSER/PGPASSWORD/PGDATABASE.
2. Run `python manage.py migrate --no-input`.
3. Run `python manage.py verify_production_readiness`.
4. Run `python deployment_test.py`.
5. Deploy only if all checks pass.

## Backup Procedure
- Enable daily PostgreSQL backups in Railway.
- Keep local backups in a secure storage location.
- Never run destructive commands during deployment.

## Database Verification Process
- Confirm the active engine is PostgreSQL.
- Confirm required tables exist.
- Confirm migrations are applied.
- Confirm the application can read user, listing, and image data.

## Recovery Steps
1. Restore the latest PostgreSQL backup.
2. Re-run migrations if required.
3. Re-run `python manage.py verify_production_readiness`.
4. Re-run deployment tests.

## Deployment Checklist
- [ ] PostgreSQL is reachable.
- [ ] No SQLite fallback is active.
- [ ] Migrations are applied safely.
- [ ] Static files exist.
- [ ] Cloudinary credentials are configured.
- [ ] System health endpoint is accessible.

## Rollback Checklist
- [ ] Keep the previous release tag.
- [ ] Restore the previous container or deployment.
- [ ] Verify data integrity and app health.
- [ ] Re-run deployment verification.
