import psycopg2

conn = psycopg2.connect("postgresql://postgres:OOQTkeMhuPRXJpCWuncoPgzUJNvJzdPC@crossover.proxy.rlwy.net:42492/railway")
cur = conn.cursor()

print("=" * 80)
print("AGENT TABLE COLUMNS")
print("=" * 80)
cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'agent' ORDER BY ordinal_position")
for col in cur.fetchall():
    print(f"{col[0]:<30} {col[1]:<20} {col[2]}")

print("\n" + "=" * 80)
print("AUTH_USER TABLE COLUMNS")
print("=" * 80)
cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'auth_user' ORDER BY ordinal_position")
for col in cur.fetchall():
    print(f"{col[0]:<30} {col[1]:<20} {col[2]}")

print("\n" + "=" * 80)
print("USER TABLE (LEGACY) COLUMNS")
print("=" * 80)
cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'user' ORDER BY ordinal_position")
for col in cur.fetchall():
    print(f"{col[0]:<30} {col[1]:<20} {col[2]}")

cur.close()
conn.close()
