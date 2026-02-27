import sqlite3

conn = sqlite3.connect("courseenrollmate.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'student'
)
""")

conn.commit()
conn.close()

print("Database created successfully!")