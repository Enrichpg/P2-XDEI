import sqlite3
import os

db_path = "/home/enrique/XDEI/P2-XDEI/smart_store.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("--- STORES ---")
    cursor.execute("SELECT id, name, location FROM store")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Name: {row[1]}, Location: {row[2]}")
    conn.close()
else:
    print("Database not found")
