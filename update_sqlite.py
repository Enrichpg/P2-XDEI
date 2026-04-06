import sqlite3
import os

db_path = "/home/enrique/XDEI/P2-XDEI/smart_store.db"
updates = {
    "Coconuts": "/static/img/products/coconuts.png",
    "Raspberries": "/static/img/products/raspberries.png",
    "Pineapples": "/static/img/products/pineapples.png",
    "Oranges": "/static/img/products/oranges.png",
    "Grapes": "/static/img/products/grapes.png"
}

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for name, path in updates.items():
        cursor.execute("UPDATE product SET image = ? WHERE name = ?", (path, name))
    conn.commit()
    print(f"Updated {name} to {path} in SQLite")
    conn.close()
else:
    print("Database not found")
