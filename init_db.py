import sqlite3

# This script creates the SQLite database and required tables for the app.
conn = sqlite3.connect('su79_database.sqlite3')
cursor = conn.cursor()

# Create admin table
cursor.execute('''
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# Drop and recreate products table to ensure correct schema
cursor.execute('DROP TABLE IF EXISTS products')
cursor.execute('''
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    details TEXT,
    price REAL NOT NULL,
    category TEXT,
    image TEXT
)
''')

# Insert a default admin user (username: admin, password: admin)
cursor.execute('''
INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)
''', ("admin", "admin"))

conn.commit()
conn.close()
print("Database and tables created. Default admin: admin/admin")
