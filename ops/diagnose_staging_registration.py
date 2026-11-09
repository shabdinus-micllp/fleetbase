#!/usr/bin/env python3
"""Read-only inspection of Fleetbase v0.7.75 staging registration state."""
import os, ssl, tempfile, sys, json
import pymysql

DB = "fleetbase_v075_stage"
def env(*keys):
    return next((os.getenv(k) for k in keys if os.getenv(k)), None)

host = env("AIVEN_MYSQL_HOST", "AIVEN_HOST", "DB_HOST")
port = int(env("AIVEN_MYSQL_PORT", "AIVEN_PORT", "DB_PORT") or "3306")
user = env("AIVEN_MYSQL_USER", "AIVEN_USER", "DB_USERNAME")
password = env("AIVEN_MYSQL_PASSWORD", "AIVEN_PASSWORD", "DB_PASSWORD")
ca = env("AIVEN_MYSQL_CA_PEM", "AIVEN_CA_PEM", "AIVEN_CA_CERT")
if not all([host, user, password, ca]) or "BEGIN CERTIFICATE" not in ca:
    print("BLOCKED: required staging DB credentials/TLS CA are not configured; no query executed.")
    sys.exit(2)

with tempfile.NamedTemporaryFile(mode="w", suffix=".pem") as pem:
    pem.write(ca); pem.flush()
    tls = ssl.create_default_context(cafile=pem.name)
    conn = pymysql.connect(host=host, port=port, user=user, password=password,
        database=DB, ssl=tls, connect_timeout=10, read_timeout=10,
        write_timeout=10, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DATABASE(), @@hostname, @@port, @@version, @@max_connections")
            row = cur.fetchone()
            print("DB_IDENTITY:", json.dumps({"database":row[0],"server":row[1],"port":row[2],"version":row[3],"max_connections":row[4]}))
            cur.execute("SHOW COLUMNS FROM companies")
            cols = [r[0] for r in cur.fetchall()]
            print("COMPANY_ONBOARDING_COLUMNS:", json.dumps({c:(c in cols) for c in ["onboarding_completed_at","onboarding_completed_by_uuid"]}))
            cur.execute("SELECT id, public_id, name, owner_uuid, onboarding_completed_at, onboarding_completed_by_uuid, created_at FROM companies WHERE name IN (%s,%s) ORDER BY id", ("METRIX INTEGRATED CONSULTANCY LLP","Technovision Systems Limited"))
            print("MATCHING_COMPANIES:", json.dumps(cur.fetchall(), default=str))
            cur.execute("SELECT COUNT(*) FROM users")
            print("USERS_TOTAL:", cur.fetchone()[0])
            cur.execute("SELECT id, uuid, name, email, phone, company_uuid, created_at FROM users ORDER BY id DESC LIMIT 10")
            print("LATEST_USERS:", json.dumps(cur.fetchall(), default=str))
            cur.execute("SHOW GLOBAL STATUS LIKE 'Threads_connected'")
            print("THREADS_CONNECTED:", json.dumps(cur.fetchone()))
            cur.execute("SHOW GLOBAL STATUS LIKE 'Max_used_connections'")
            print("MAX_USED_CONNECTIONS:", json.dumps(cur.fetchone()))
            cur.execute("SHOW FULL PROCESSLIST")
            processes = cur.fetchall()
            print("PROCESSLIST:", json.dumps([{"id":r[0],"user":r[1],"host":r[2],"db":r[3],"command":r[4],"time":r[5],"state":r[6],"info":(r[7] or "")[:180]} for r in processes], default=str))
            print("READ_ONLY_DIAGNOSTIC_COMPLETE")
    finally:
        conn.close()
