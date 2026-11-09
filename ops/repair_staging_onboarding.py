#!/usr/bin/env python3
"""Safe additive schema repair for Fleetbase v0.7.75 STAGING only."""
import os
import sys
import ssl
import tempfile
import pymysql

TARGET = "fleetbase_v075_stage"

def env(*keys):
    return next((os.getenv(key) for key in keys if os.getenv(key)), None)

host = env("AIVEN_MYSQL_HOST", "AIVEN_HOST", "DB_HOST")
port = int(env("AIVEN_MYSQL_PORT", "AIVEN_PORT", "DB_PORT") or "3306")
user = env("AIVEN_MYSQL_USER", "AIVEN_USER", "DB_USERNAME")
password = env("AIVEN_MYSQL_PASSWORD", "AIVEN_PASSWORD", "DB_PASSWORD")
ca = env("AIVEN_MYSQL_CA_PEM", "AIVEN_CA_PEM", "AIVEN_CA_CERT")
requested = env("AIVEN_MYSQL_DATABASE", "AIVEN_DATABASE", "DB_DATABASE")
if requested and requested != TARGET:
    print("REFUSED: configured database name is not the v0.7.75 staging database.")
    sys.exit(2)
if not host or not user or not password:
    print("BLOCKED: missing MySQL connection secrets; no SQL executed.")
    sys.exit(2)
if not ca:
    print("BLOCKED: Aiven TLS CA secret not configured; no SQL executed.")
    sys.exit(2)
if "BEGIN CERTIFICATE" not in ca:
    print("BLOCKED: TLS CA content invalid; no SQL executed.")
    sys.exit(2)

with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".pem") as pem:
    pem.write(ca)
    pem.flush()
    tls = ssl.create_default_context(cafile=pem.name)
    conn = pymysql.connect(host=host, port=port, user=user, password=password,
                           database=TARGET, ssl=tls, connect_timeout=12,
                           read_timeout=15, write_timeout=15, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DATABASE()")
            actual = cur.fetchone()[0]
            if actual != TARGET:
                raise RuntimeError("REFUSED: database identity mismatch")
            cur.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='companies'
                AND COLUMN_NAME IN ('onboarding_completed_at','onboarding_completed_by_uuid')
                """, (TARGET,))
            existing = {r[0] for r in cur.fetchall()}
            cur.execute("SHOW TABLES LIKE 'companies'")
            if cur.fetchone() is None:
                raise RuntimeError("REFUSED: companies table not found; migration required")
            if "onboarding_completed_at" not in existing:
                cur.execute("ALTER TABLE companies ADD COLUMN onboarding_completed_at TIMESTAMP NULL DEFAULT NULL")
                print("ADDED: onboarding_completed_at")
            else:
                print("EXISTS: onboarding_completed_at")
            if "onboarding_completed_by_uuid" not in existing:
                cur.execute("ALTER TABLE companies ADD COLUMN onboarding_completed_by_uuid VARCHAR(255) NULL DEFAULT NULL")
                print("ADDED: onboarding_completed_by_uuid")
            else:
                print("EXISTS: onboarding_completed_by_uuid")
            cur.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='companies'
                AND COLUMN_NAME='onboarding_completed_at'
                """, (TARGET,))
            if cur.fetchone()[0] == 0:
                cur.execute("CREATE INDEX companies_onboarding_completed_at_index ON companies (onboarding_completed_at)")
                print("ADDED: onboarding index")
            else:
                print("EXISTS: onboarding index")
            cur.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='companies'
                AND COLUMN_NAME IN ('onboarding_completed_at','onboarding_completed_by_uuid')
                """, (TARGET,))
            verified = {r[0] for r in cur.fetchall()}
            assert verified == {"onboarding_completed_at", "onboarding_completed_by_uuid"}
            print("SUCCESS: staging onboarding columns verified. No data rows changed.")
    finally:
        conn.close()
