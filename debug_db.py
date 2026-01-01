import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def get_db_info():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cur.fetchall()
        print("Tables in public schema:")
        for table in tables:
            print(f"- {table['table_name']}")
            
        # Check voucher table structure if it exists
        if any(t['table_name'] == 'voucher' for t in tables):
            print("\nVoucher table structure:")
            cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'voucher'")
            columns = cur.fetchall()
            for col in columns:
                print(f"- {col['column_name']}: {col['data_type']}")
        else:
            print("\nVoucher table NOT found!")

        # Check package table structure
        if any(t['table_name'] == 'package' for t in tables):
            print("\nPackage table structure:")
            cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'package'")
            columns = cur.fetchall()
            for col in columns:
                print(f"- {col['column_name']}: {col['data_type']}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_db_info()
