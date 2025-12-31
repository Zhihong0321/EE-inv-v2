import psycopg2

conn = psycopg2.connect("postgresql://postgres:OOQTkeMhuPRXJpCWuncoPgzUJNvJzdPC@crossover.proxy.rlwy.net:42492/railway")
cur = conn.cursor()

print("=" * 80)
print("PACKAGE TABLE COLUMNS")
print("=" * 80)
cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'package' ORDER BY ordinal_position")
for col in cur.fetchall():
    print(f"{col[0]:<30} {col[1]:<20} {col[2]}")

print("\n" + "=" * 80)
print("SAMPLE PACKAGES (Top 5)")
print("=" * 80)
cur.execute("SELECT bubble_id, name, type, price, panel, panel_qty FROM package LIMIT 5")
for row in cur.fetchall():
    print(f"ID: {row[0]:<15} Name: {row[1]:<30} Type: {row[2]:<15} Price: {row[3]}")

print("\n" + "=" * 80)
print("SAMPLE AGENTS (Top 5)")
print("=" * 80)
cur.execute("SELECT bubble_id, name, contact, email FROM agent LIMIT 5")
for row in cur.fetchall():
    print(f"ID: {row[0]:<15} Name: {row[1]:<30} Contact: {row[2]:<15} Email: {row[3]}")

print("\n" + "=" * 80)
print("SAMPLE AUTH_USERS")
print("=" * 80)
cur.execute("SELECT user_id, whatsapp_number, name, role FROM auth_user LIMIT 5")
for row in cur.fetchall():
    print(f"ID: {row[0]:<36} WhatsApp: {row[1]:<15} Name: {row[2]:<20} Role: {row[3]}")

cur.close()
conn.close()
