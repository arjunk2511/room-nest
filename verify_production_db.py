import os
import sys

# 1. Print all available database environment variables during startup (safely masked)
print("====================================================")
print("🔍 Startup Environment Variables Check:")
print("====================================================")
vars_to_check = [
    "DATABASE_URL",
    "DATABASE_PUBLIC_URL",
    "PGHOST",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGPASSWORD"
]

def mask_value(name, val):
    if not val:
        return "None / Empty"
    if name in ["DATABASE_URL", "DATABASE_PUBLIC_URL"]:
        if "@" in val and "://" in val:
            prefix, rest = val.split("://", 1)
            if "@" in rest:
                creds, host_part = rest.split("@", 1)
                if ":" in creds:
                    user, _ = creds.split(":", 1)
                    return f"{prefix}://{user}:***@{host_part}"
                return f"{prefix}://***@{host_part}"
        return "*** (Masked URL)"
    if name == "PGPASSWORD":
        return "***"
    return val

for name in vars_to_check:
    val = os.environ.get(name)
    print(f"  {name}: {mask_value(name, val)}")
print("====================================================\n")

import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roomnest.settings')
try:
    django.setup()
except Exception as e:
    print(f"❌ ERROR: Failed to initialize Django settings: {e}")
    sys.exit(1)

from django.db import connections
from django.db.utils import OperationalError
from django.contrib.auth import get_user_model
from django.db.migrations.recorder import MigrationRecorder
from listings.models import Listing

def main():
    print("====================================================")
    print("🔒 Running Pre-Startup Production Database Safety Checks")
    print("====================================================")
    
    # 2. Retrieve the default database connection
    db_conn = connections['default']
    
    # Print the final database engine, host, and name that Django is actually using after startup
    db_name = db_conn.settings_dict.get('NAME')
    db_host = db_conn.settings_dict.get('HOST')
    db_engine = db_conn.settings_dict.get('ENGINE')
    print("ℹ️ Active Database Settings used by Django:")
    print(f"  Engine: {db_engine}")
    print(f"  Database Name: {db_name}")
    print(f"  Host: {db_host}")
    print("----------------------------------------------------")
    
    # 3. Verify PostgreSQL connection
    try:
        db_conn.ensure_connection()
        print("✅ Database connection verified.")
        
        # Run active diagnostic queries to fetch actual DB name, version, and migrations count
        try:
            with db_conn.cursor() as cursor:
                # Query database name
                cursor.execute("SELECT current_database();")
                actual_db_name = cursor.fetchone()[0]
                
                # Query postgres/engine version
                cursor.execute("SELECT version();")
                actual_db_version = cursor.fetchone()[0]
                
                # Verify migrations count
                table_names = db_conn.introspection.table_names()
                migrations_count = "N/A (django_migrations table missing)"
                if 'django_migrations' in table_names:
                    cursor.execute("SELECT COUNT(*) FROM django_migrations;")
                    migrations_count = cursor.fetchone()[0]
                    
            print("📊 Active Database Diagnostic Query Results:")
            print(f"  Current Database: {actual_db_name}")
            print(f"  Database Version: {actual_db_version}")
            print(f"  Applied Migrations Count: {migrations_count}")
            print("----------------------------------------------------")
        except Exception as q_err:
            print(f"⚠️ Warning: Failed to run diagnostic queries: {q_err}")
            
    except OperationalError as e:
        print(f"❌ DATABASE CONNECTION ERROR: Could not connect to the remote database: {e}")
        print("Startup blocked to prevent data loss or fallback issues.")
        sys.exit(1)
        
    # 4. Double-check database engine is not SQLite in production
    is_production_env = (
        os.environ.get('DJANGO_ENV', 'development').lower() in ['staging', 'production']
        or os.environ.get('IS_PRODUCTION', 'False') == 'True'
        or 'RAILWAY_ENVIRONMENT' in os.environ
        or 'RENDER' in os.environ
    )
    
    if is_production_env and 'sqlite' in db_engine:
        print("❌ CRITICAL DATABASE ERROR: SQLite configuration is prohibited in production!")
        print("Startup blocked to prevent data loss on ephemeral filesystems.")
        sys.exit(1)

    # 5. Verify critical Django tables exist
    table_names = db_conn.introspection.table_names()
    required_tables = ['auth_user', 'listings_listing', 'django_migrations']
    missing_tables = [table for table in required_tables if table not in table_names]
    
    if missing_tables:
        print(f"❌ DATABASE STRUCTURE ERROR: Missing critical Django tables: {missing_tables}")
        print("Startup blocked. Ensure migrations are applied or correct database is specified.")
        sys.exit(1)
    else:
        print("✅ Critical Django tables verified.")

    # 6. Verify migration history exists
    try:
        recorder = MigrationRecorder(db_conn)
        applied_migrations = recorder.applied_migrations()
        if not applied_migrations:
            print("❌ DATABASE HISTORY ERROR: Migration history is empty (no applied migrations in django_migrations)!")
            print("Startup blocked.")
            sys.exit(1)
        else:
            print(f"✅ Migration history verified ({len(applied_migrations)} migrations applied).")
    except Exception as e:
        print(f"❌ DATABASE HISTORY ERROR: Failed to read migration history: {e}")
        sys.exit(1)

    # 7. Verify database is not empty (contains users, listings)
    try:
        User = get_user_model()
        user_count = User.objects.count()
        listing_count = Listing.objects.count()
        
        print(f"ℹ️ Database Scan: Found {user_count} users and {listing_count} listings.")
        if user_count == 0:
            print("❌ DATABASE CONTENT ERROR: The database contains 0 registered users (it is empty)!")
            print("Startup blocked to prevent running against an empty/wiped database.")
            sys.exit(1)
        else:
            print("✅ Database contains existing records (not empty).")
    except Exception as e:
        print(f"❌ DATABASE CONTENT ERROR: Failed to query existing database records: {e}")
        sys.exit(1)

    print("🎉 All pre-startup database safety checks passed successfully!")
    sys.exit(0)

if __name__ == '__main__':
    main()
