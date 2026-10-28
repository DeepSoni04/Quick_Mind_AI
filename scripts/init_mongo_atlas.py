#!/usr/bin/env python3
"""
QueryMind AI — MongoDB Atlas Initializer & Seeder Script
Analyzes the entire application schema and creates all collections, indexes,
and initial seed accounts (Admin, Analyst, Viewer) on MongoDB Atlas.

Usage:
    python scripts/init_mongo_atlas.py
    # Or pass explicit Atlas URI:
    python scripts/init_mongo_atlas.py --uri "mongodb+srv://user:pass@cluster.mongodb.net/querymind"
"""

import sys
import os
import argparse
from datetime import datetime, timezone
import bcrypt
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure

# Try loading .env from backEnd directory
try:
    from dotenv import load_dotenv
    backend_env = os.path.join(os.path.dirname(__file__), "..", "backEnd", ".env")
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
        print(f"[OK] Loaded configuration from {os.path.abspath(backend_env)}")
except ImportError:
    pass


def hash_pwd(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def get_utc_now():
    return datetime.now(timezone.utc)


def main():
    parser = argparse.ArgumentParser(description="Initialize MongoDB Atlas collections & indexes for QueryMind AI")
    parser.add_argument("--uri", type=str, default=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
                        help="MongoDB Connection URI (defaults to MONGODB_URI in backEnd/.env)")
    parser.add_argument("--database", type=str, default=os.getenv("MONGODB_DATABASE", "querymind"),
                        help="Target Database name (default: querymind)")
    parser.add_argument("--reset", action="store_true", help="Drop existing collections before initializing")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("      QueryMind AI — MongoDB Atlas Schema Initializer")
    print("=" * 65)

    uri = args.uri
    db_name = args.database

    # Mask sensitive credentials when printing
    masked_uri = uri
    if "@" in masked_uri:
        prefix, host_part = masked_uri.split("@", 1)
        scheme_and_user = prefix.split("://", 1)
        if len(scheme_and_user) == 2 and ":" in scheme_and_user[1]:
            user = scheme_and_user[1].split(":")[0]
            masked_uri = f"{scheme_and_user[0]}://{user}:******@{host_part}"

    print(f"[*] Target URI:      {masked_uri}")
    print(f"[*] Target Database: {db_name}")
    print(f"[*] Connecting to cluster...")

    try:
        import certifi
        client = MongoClient(uri, serverSelectionTimeoutMS=20000, tlsCAFile=certifi.where())
        # Test connection
        client.admin.command('ping')
        print("[OK] Successfully connected to MongoDB!")
    except ConnectionFailure as e:
        print(f"[!] Error: Could not connect to MongoDB: {e}")
        print("\nTip: If connecting to MongoDB Atlas:")
        print("  1. Verify your IP address is whitelisted in Atlas (Network Access -> Add IP Address -> Allow 0.0.0.0/0)")
        print("  2. Verify your database username and password in the connection string.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Unexpected connection error: {e}")
        sys.exit(1)

    db = client[db_name]

    if args.reset:
        print("\n[*] --reset flag passed: Dropping existing collections...")
        collections_to_drop = [
            "users", "database_connections", "schema_access",
            "query_sessions", "queries", "query_logs",
            "user_settings", "role_requests"
        ]
        for c in collections_to_drop:
            db[c].drop()
            print(f"    - Dropped collection: {c}")

    print("\n[*] Initializing Collections & Indexes...")

    # 1. users collection
    print("  1. Setting up 'users' collection...")
    db.users.create_index("email", unique=True)
    db.users.create_index("role")

    # 2. database_connections collection
    print("  2. Setting up 'database_connections' collection...")
    db.database_connections.create_index("created_by")
    db.database_connections.create_index("name")

    # 3. schema_access collection
    print("  3. Setting up 'schema_access' collection...")
    db.schema_access.create_index([("database_id", ASCENDING), ("table_name", ASCENDING)], unique=True)

    # 4. query_sessions collection
    print("  4. Setting up 'query_sessions' collection...")
    db.query_sessions.create_index("user_id")
    db.query_sessions.create_index([("created_at", DESCENDING)])

    # 5. queries collection
    print("  5. Setting up 'queries' collection...")
    db.queries.create_index("user_id")
    db.queries.create_index("database_id")
    db.queries.create_index("session_id")
    db.queries.create_index([("created_at", DESCENDING)])

    # 6. query_logs collection
    print("  6. Setting up 'query_logs' collection...")
    db.query_logs.create_index("query_id")
    db.query_logs.create_index("user_id")
    db.query_logs.create_index("severity")
    db.query_logs.create_index([("created_at", DESCENDING)])

    # 7. user_settings collection
    print("  7. Setting up 'user_settings' collection...")
    db.user_settings.create_index("user_id", unique=True)

    # 8. role_requests collection
    print("  8. Setting up 'role_requests' collection...")
    db.role_requests.create_index("user_id")
    db.role_requests.create_index("status")
    db.role_requests.create_index([("created_at", DESCENDING)])

    print("[OK] All 8 collections and indexes created successfully!")

    # ── Seed Initial Users ────────────────────────────────────────────────
    print("\n[*] Checking & Seeding Default Application Accounts...")

    admin_email = os.getenv("ADMIN_EMAIL", "admin@querymind.ai").lower()
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")

    now = get_utc_now()

    default_accounts = [
        {
            "name": "Deep Soni",
            "email": admin_email,
            "password_hash": hash_pwd(admin_pass),
            "role": "admin",
            "status": "active",
            "title": "Lead Data Architect & AI Admin",
            "department": "Data Platform & AI Infrastructure",
            "avatar": "DS",
            "created_at": now,
            "updated_at": now
        },
        {
            "name": "Heer Sachdev",
            "email": "heer@querymind.ai",
            "password_hash": hash_pwd("analyst123"),
            "role": "analyst",
            "status": "active",
            "title": "Senior Database Analyst",
            "department": "Business Intelligence & Student Analytics",
            "avatar": "HS",
            "created_at": now,
            "updated_at": now
        },
        {
            "name": "Neel Shah",
            "email": "neel@querymind.ai",
            "password_hash": hash_pwd("viewer123"),
            "role": "viewer",
            "status": "active",
            "title": "Data Auditor & Reviewer",
            "department": "Operations & Compliance",
            "avatar": "NS",
            "created_at": now,
            "updated_at": now
        }
    ]

    for acc in default_accounts:
        existing = db.users.find_one({"email": acc["email"]})
        if not existing:
            res = db.users.insert_one(acc)
            user_id = str(res.inserted_id)
            print(f"  [+] Created account: {acc['name']} ({acc['email']}) [Role: {acc['role']}]")

            # Seed default settings for each new user
            db.user_settings.update_one(
                {"user_id": user_id},
                {"$setOnInsert": {
                    "user_id": user_id,
                    "confirm_updates": True,
                    "confirm_deletes": True,
                    "row_limit": 100,
                    "query_timeout": 30,
                    "created_at": now,
                    "updated_at": now
                }},
                upsert=True
            )
        else:
            print(f"  [·] Account already exists: {acc['name']} ({acc['email']})")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("      MongoDB Atlas Initialization Complete!")
    print("=" * 65)
    print("Collection Summary:")
    for col in db.list_collection_names():
        count = db[col].count_documents({})
        print(f"  • {col:25} -> {count:4} documents")

    print("\nYou can now update backEnd/.env with your Atlas URI:")
    print(f"  MONGODB_URI={uri}")
    print(f"  MONGODB_DATABASE={db_name}")
    print("\nAnd restart the backend server with:")
    print("  uvicorn app.main:app --reload --port 8000")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
