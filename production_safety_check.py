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
        print(f"❌ Command failed! Error:\n{result.stderr}")
        return False, result.stderr
    return True, result.stdout

def main():
    print("====================================================")
    print("🔒 RoomNest Production Safety & Regression Check")
    print("====================================================\n")

    # 1. Check if database is SQLite or remote PostgreSQL
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        print("ℹ️ Detected Remote Database (DATABASE_URL is set).")
        print("⚠️ Ensure you have initiated a cloud snapshot/backup on your hosting platform (e.g., Railway PG Backup) before migrating!\n")
    else:
        print("📦 Detected Local SQLite Database.")
        db_path = "db.sqlite3"
        if not os.path.exists(db_path):
            print("❌ db.sqlite3 not found in current directory.")
            sys.exit(1)
            
        # Create backups directory
        os.makedirs("backups", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backups/db_backup_{timestamp}.sqlite3"
        
        # 1. Perform Backup
        print(f"🔄 Backing up {db_path} to {backup_path}...")
        try:
            shutil.copy2(db_path, backup_path)
            print("✅ Backup file created successfully.")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            sys.exit(1)
            
        # 2. Verify Backup Integrity
        print("🔍 Verifying backup database integrity check...")
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            if row and row[0] == "ok":
                print("✅ SQLite integrity check passed! The backup file is sound.")
            else:
                print(f"❌ SQLite integrity check failed: {row}")
                sys.exit(1)
            conn.close()
        except Exception as e:
            print(f"❌ Failed to verify backup: {e}")
            sys.exit(1)
            
    print("")
    
    # 2. Django Settings & System Config Check
    print("⚙️ Running Django configuration and validation checks...")
    success, output = run_cmd([sys.executable, "manage.py", "check"])
    if not success:
        print("❌ Django system checks failed. Aborting deployment.")
        sys.exit(1)
    print("✅ Django system validation check passed.")
    print("")

    # 3. Check for Pending Database Migrations
    print("⚡ Checking for any pending unapplied database migrations...")
    success, output = run_cmd([sys.executable, "manage.py", "showmigrations"])
    if not success:
        sys.exit(1)
    
    unapplied = []
    for line in output.splitlines():
        if "[ ]" in line:
            unapplied.append(line.strip())
            
    if unapplied:
        print("⚠️ Warning: The following migrations are pending and have NOT been applied yet:")
        for m in unapplied:
            print(f"  - {m}")
        print("👉 Run 'python manage.py migrate' after checking backups to apply them safely.\n")
    else:
        print("✅ All database migrations are fully applied.\n")

    # 4. Regression Testing
    print("🧪 Running regression test suite...")
    success, output = run_cmd([sys.executable, "manage.py", "test"])
    if not success:
        print("❌ Regression test suite failed. Fix failures before deploying.")
        sys.exit(1)
    print("✅ Regression test suite passed successfully!\n")

    print("====================================================")
    print("🎉 Safety checks completed. Ready for safe deployment!")
    print("====================================================")

if __name__ == "__main__":
    main()
