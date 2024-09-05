import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('transaction_monitoring.db')
cursor = conn.cursor()

# Create transactions table with an additional column for processing status
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY,
    account_id INTEGER,
    amount DECIMAL(10, 2),
    transaction_date TIMESTAMP,
    country VARCHAR(50),
    transaction_type VARCHAR(50),
    payee_id INTEGER,
    processed BOOLEAN DEFAULT 0  -- New column to track processed transactions
)
''')

# Create alerts table
cursor.execute('''
CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY,
    transaction_id INTEGER,
    alert_type VARCHAR(50),
    alert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
