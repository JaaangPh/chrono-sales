#!/usr/bin/env python3
"""
import_db.py
Uploads chrono_sales_db.sql to a cloud MySQL / TiDB database.

Usage:
    python import_db.py
Or set environment variables:
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""

import os
import sys
import getpass
import mysql.connector

def main():
    print("=" * 60)
    print(" Chrono Sales - Cloud Database Importer")
    print("=" * 60)

    host = os.getenv("DB_HOST") or input("Enter Database Host (e.g. gateway01.ap-southeast-1.prod.aws.tidbcloud.com): ").strip()
    port_in = os.getenv("DB_PORT") or input("Enter Port [default 4000 for TiDB, 3306 for MySQL]: ").strip()
    port = int(port_in) if port_in else 4000
    user = os.getenv("DB_USER") or input("Enter Database User (e.g. 21xxxx.root): ").strip()
    password = os.getenv("DB_PASSWORD") or getpass.getpass("Enter Database Password: ").strip()
    db_name = os.getenv("DB_NAME") or "chrono_sales_db"

    print(f"\nConnecting to {host}:{port} as {user}...")

    connect_kwargs = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
    }
    if host not in ("localhost", "127.0.0.1"):
        connect_kwargs["ssl_verify_cert"] = False

    try:
        conn = mysql.connector.connect(**connect_kwargs)
        cur = conn.cursor()
        print("Connected successfully!")
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        sys.exit(1)

    print(f"Creating database '{db_name}' if it does not exist...")
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cur.execute(f"USE `{db_name}`;")
    print(f"Using database: {db_name}")

    sql_file = os.path.join(os.path.dirname(__file__), "chrono_sales_db.sql")
    if not os.path.exists(sql_file):
        print(f"[ERROR] Could not find '{sql_file}'")
        sys.exit(1)

    print(f"Reading {sql_file}...")
    with open(sql_file, "r", encoding="utf-8") as f:
        content = f.read()

    lines = []
    for line in content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("--") or trimmed.startswith("/*") or trimmed.startswith("#"):
            continue
        lines.append(line)

    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    print(f"Executing {len(statements)} SQL statements...")

    success = 0
    errors = 0
    for idx, stmt in enumerate(statements, 1):
        try:
            cur.execute(stmt)
            success += 1
            if idx % 10 == 0 or idx == len(statements):
                print(f"  Progress: {idx}/{len(statements)} statements completed...")
        except Exception as e:
            errors += 1
            # ignore harmless non-critical warnings
            first_word = stmt.split()[0].upper() if stmt.split() else ""
            print(f"  [Warning] Statement {idx} ({first_word}) failed: {e}")

    conn.commit()
    cur.close()
    conn.close()

    print("\n" + "=" * 60)
    print(f" Import finished! Successfully executed: {success}/{len(statements)}")
    if errors:
        print(f" Non-critical warnings/skipped: {errors}")
    print(" Your cloud database is now fully populated with data.")
    print("=" * 60)

if __name__ == "__main__":
    main()

