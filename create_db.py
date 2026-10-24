import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT UNIQUE,
    name TEXT,
    address TEXT,
    phone TEXT,
    description TEXT,
    category TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully!")