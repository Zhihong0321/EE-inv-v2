import psycopg2
conn = psycopg2.connect("postgresql://postgres:OOQTkeMhuPRXJpCWuncoPgzUJNvJzdPC@crossover.proxy.rlwy.net:42492/railway")
cur = conn.cursor()

# Get all table names
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")
tables = cur.fetchall()

print("=" * 80)
print("DATABASE SCHEMA - Postgres Tables")
print("=" * 80)
for table in tables:
    table_name = table[0]
    print(f"\n{'=' * 80}")
    print(f"TABLE: {table_name}")
    print(f"{'=' * 80}")
    
    # Get columns for this table
    cur.execute(f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    columns = cur.fetchall()
    
    print(f"{'Column Name':<30} {'Data Type':<20} {'Nullable':<10} {'Default'}")
    print("-" * 80)
    for col in columns:
        col_name, data_type, is_nullable, col_default = col
        nullable = "YES" if is_nullable == "YES" else "NO"
        default_val = str(col_default) if col_default else ""
        print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default_val}")

cur.close()
conn.close()
print("\n" + "=" * 80)
print("Schema extraction complete!")
print("=" * 80)
