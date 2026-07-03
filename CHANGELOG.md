# Changelog

All notable changes to the RoomNest application will be documented in this file.

## [1.1.0] - 2026-07-03

### Added
- **Multi-Environment Setup**: Introduced `DJANGO_ENV` configuration handling in `roomnest/settings.py` supporting `development`, `staging`, and `production` environments cleanly. Enforced secure SSL redirects, cookies, and Strict Transport Security (HSTS) headers dynamically for production/staging environments.
- **Destructive Migration Safeguards**: Added pre-deploy scanning in `production_safety_check.py` to intercept unapplied migrations containing potentially destructive database schema operations (e.g. `RemoveField`, `RenameField`, `DeleteModel`, `RenameModel`, or destructive raw `RunSQL` alterations) to prevent data loss.
- **Automated Post-Deployment Verification Check**: Created a read-only Django management command (`python manage.py verify_deployment`) that checks 10 critical service paths: user/owner records, listings, image reachability, maps/proximity API, search query handling, auth login page, dashboards rendering, rewards status, and subscriptions table state.
- **Postgres Railway Backup Check**: Integrated explicit user confirmation checkpoints in the deployment pipeline to ensure manual/cloud PostgreSQL backups are completed and verified before modifications are made.

### Fixed
- **WhatsApp Direct Interaction & Tracking**: Patched the "WhatsApp Chat" buttons to call backend AJAX click-tracking endpoints to log seeker leads and views appropriately. Fixed browser popup blocking caused by asynchronous `.then()` promises in the click handlers.

### Database Migrations Applied
- None (All added elements are read-only commands, template adjustments, and configuration handlers).

### Rollback Procedure
If a deployment fails validation checks or introduces database instability:
1. **Restore Git State**: Run `git checkout <commit_sha>` or `git revert <commit_sha>` to roll back code modifications.
2. **Reverse Schema Changes (if applicable)**: If database schema alterations were applied, identify the last known stable migration index and rollback using:
   ```bash
   python manage.py migrate <app_name> <stable_migration_number>
   ```
3. **Database Restore**: If database data corruption is detected, log into the Railway console, retrieve the verified backup/snapshot created during the pre-deploy phase, and restore it to overwrite the corrupted table states.
