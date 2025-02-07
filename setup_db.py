import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('dentist.db')
cursor = conn.cursor()

# Drop the existing appointments table to avoid conflicts (ONLY IF NECESSARY)
cursor.execute("DROP TABLE IF EXISTS appointments")

# Create the users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        phone TEXT
    )
''')

# Create the appointments table with a created_at column
cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
''')

# Insert sample data
cursor.execute('''
    INSERT INTO users (username, password, role, email, phone)
    VALUES (?, ?, ?, ?, ?)
''', ('Bob Bobby', 'Password4321', 'patient', 'bob@example.com', '123-456-7890'))

cursor.execute('''
    INSERT INTO users (username, password, role, email, phone)
    VALUES (?, ?, ?, ?, ?)
''', ('MikeDemo', 'Password', 'patient', 'mike@example.com', '123-456-7891'))


cursor.execute('''
    INSERT INTO users (username, password, role, email, phone)
    VALUES (?, ?, ?, ?, ?)
''', ('ADMIN', 'ADMINPASS1457', 'admin', 'admin@example.com', '987-654-3210'))

# Commit changes and close the connection
conn.commit()
conn.close()

print("Database setup complete!")
