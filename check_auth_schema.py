"""
Check auth_user table schema and sample data from PROD DB
"""
import psycopg2
from psycopg2.extras import RealDictCursor

PROD_DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

conn = psycopg2.connect(PROD_DB_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("AUTH_USER TABLE SCHEMA")
print("=" * 80)
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name = 'auth_user' 
    ORDER BY ordinal_position
""")
for col in cur.fetchall():
    print(f"{col['column_name']:<30} {col['data_type']:<25} nullable: {col['is_nullable']}")

print("\n" + "=" * 80)
print("SAMPLE AUTH_USER DATA (Top 5)")
print("=" * 80)
cur.execute("SELECT user_id, whatsapp_number, name, role FROM auth_user LIMIT 5")
for row in cur.fetchall():
    print(f"user_id: {row['user_id']} (type: {type(row['user_id']).__name__})")
    print(f"  whatsapp: {row['whatsapp_number']}")
    print(f"  name: {row['name']}")
    print(f"  role: {row['role']}")
    print()

print("=" * 80)
print("CHECKING user_id VALUES")
print("=" * 80)
cur.execute("SELECT user_id FROM auth_user LIMIT 10")
for row in cur.fetchall():
    print(f"user_id: '{row['user_id']}' (type: {type(row['user_id']).__name__})")

cur.close()
conn.close()

