#!/usr/bin/env python
import os
import sys
import shutil
import sqlite3
import datetime
import subprocess

def run_cmd(args):
    print(f"Running: {' '.join(args)}")
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr
    return True, result.stdout

def scan_migration_for_destructive_ops(app_name, mig_name):
    # Construct paths
    filepath = os.path.join(app_name, 'migrations', f"{mig_name}.py")
    if not os.path.exists(filepath):
        # Fallback search under workspace
        filepath = os.path.join(os.path.dirname(__file__), app_name, 'migrations', f"{mig_name}.py")
        if not os.path.exists(filepath):
            return []

    with open(filepath, 'r') as f:
        content = f.read()

    destructive_keywords = {
        'RemoveField': 'Removing a model database column (RemoveField)',
        'RenameField': 'Renaming a database column (RenameField)',
        'DeleteModel': 'Deleting a database table/model (DeleteModel)',
        'RenameModel': 'Renaming a database table/model (RenameModel)',
    }

    found_ops = []
    for kw, description in destructive_keywords.items():
        if kw in content:
            found_ops.append(description)

    if 'RunSQL' in content:
        content_lower = content.lower()
        if 'drop ' in content_lower or 'alter ' in content_lower:
            found_ops.append('Raw RunSQL operation containing ALTER or DROP statements')

    return found_ops

def main():
    print("====================================================")
    print("🔒 RoomNest Production Safety & Pre-Deploy Checks")
    print("====================================================\n")

    # 1. Backup Checks
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        print("ℹ️ Detected Remote Database (DATABASE_URL is set).")
        print("🚨 CRITICAL: TREAT THE PRODUCTION DATABASE AS PERMANENT.")
        print("To protect production data, you must manually confirm backup status.")
        print("Please log into Railway and create a PostgreSQL database backup/snapshot now.")
        
        confirm = input("\nHave you created and verified a PostgreSQL backup on Railway? (type 'yes' to confirm): ").strip().lower()
        if confirm != 'yes':
            print("❌ Pre-deploy check failed: A verified backup is required before proceeding.")
            sys.exit(1)
        print("✅ Backup confirmation received.\n")
    else:
        print("📦 Detected Local SQLite Database.")
        db_path = "db.sqlite3"
        if os.path.exists(db_path):
            os.makedirs("backups", exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/db_backup_{timestamp}.sqlite3"
            
            print(f"🔄 Backing up {db_path} to {backup_path}...")
            try:
                shutil.copy2(db_path, backup_path)
                print("✅ Backup file created successfully.")
            except Exception as e:
                print(f"❌ Backup failed: {e}")
                sys.exit(1)
                
            print("🔍 Verifying backup database integrity check...")
            try:
                conn = sqlite3.connect(backup_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                row = cursor.fetchone()
                if row and row[0] == "ok":
                    print("✅ SQLite integrity check passed!")
                else:
                    print(f"❌ SQLite integrity check failed: {row}")
                    sys.exit(1)
                conn.close()
            except Exception as e:
                print(f"❌ Failed to verify backup: {e}")
                sys.exit(1)
        else:
            print("⚠️ No local db.sqlite3 found. Skipping backup.")

    print("")

    # 2. Django Configuration and System Checks
    print("⚙️ Running Django configuration and validation checks...")
    success, output = run_cmd([sys.executable, "manage.py", "check"])
    if not success:
        print(f"❌ Django system checks failed:\n{output}")
        sys.exit(1)
    print("✅ Django system validation check passed.\n")

    # 3. Check for Pending Database Migrations & Destructive Operations
    print("⚡ Checking for pending unapplied database migrations...")
    success, output = run_cmd([sys.executable, "manage.py", "showmigrations"])
    if not success:
        print(f"❌ Failed to retrieve migrations:\n{output}")
        sys.exit(1)

    app_name = None
    unapplied = []
    for line in output.splitlines():
        if not line.strip():
            continue
        if line.startswith(" ") or line.startswith("\t"):
            if "[ ]" in line:
                mig_name = line.replace("[ ]", "").strip()
                if app_name:
                    unapplied.append((app_name, mig_name))
        else:
            app_name = line.strip().replace(":", "")

    if unapplied:
        print(f"⚠️ Warning: The following {len(unapplied)} migrations are pending:")
        destructive_found = False
        for app, mig in unapplied:
            print(f"  - {app}: {mig}")
            destructive_ops = scan_migration_for_destructive_ops(app, mig)
            if destructive_ops:
                destructive_found = True
                print("    🚨 DESTRUCTIVE OPERATION DETECTED IN THIS MIGRATION:")
                for op in destructive_ops:
                    print(f"      👉 {op}")
        
        if destructive_found:
            print("\n❌ DESTRUCTIVE SCHEMA DETECTED!")
            print("--------------------------------------------------------------------")
            print("CRITICAL RISK: The pending database migrations contain operations that")
            print("could remove, rename, or alter existing database tables or columns.")
            print("This violates the production safety policy.")
            print("--------------------------------------------------------------------")
            print("Safe Migration Strategy Requirement:")
            print("1. Never rename or remove database columns without preserving existing data.")
            print("2. Create a data migration that safely moves existing records to backup columns before removal.")
            
            confirm = input("\nDo you want to override and proceed with this destructive change? (type 'OVERRIDE DESTRUCTIVE CHANGE' to proceed): ").strip()
            if confirm != 'OVERRIDE DESTRUCTIVE CHANGE':
                print("❌ Deployment aborted to protect database integrity.")
                sys.exit(1)
            print("⚠️ Override accepted. Proceeding with caution...\n")
        else:
            print("✅ All pending migrations are safe (no destructive operations detected).\n")
    else:
        print("✅ All database migrations are fully applied.\n")

    # 4. Regression Testing
    print("🧪 Running regression test suite...")
    success, output = run_cmd([sys.executable, "manage.py", "test"])
    if not success:
        print(f"❌ Regression test suite failed:\n{output}")
        sys.exit(1)
    print("✅ Regression test suite passed successfully!\n")

    print("====================================================")
    print("🎉 Safety checks completed. Ready for safe deployment!")
    print("====================================================")

if __name__ == "__main__":
    main()
