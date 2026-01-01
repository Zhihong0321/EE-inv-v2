import psycopg2

def check_inv():
    dsn = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    
    cur.execute("SELECT invoice_number, customer_name_snapshot FROM invoice_new WHERE invoice_number = 'INV-000008'")
    row = cur.fetchone()
    
    if row:
        print(f"Invoice: {row[0]}, Customer: {row[1]}")
    else:
        print("Invoice not found")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_inv()
