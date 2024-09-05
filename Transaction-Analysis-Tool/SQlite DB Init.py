import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('crypto_transaction_analysis.db')
cursor = conn.cursor()

# Create transactions table
cursor.execute('''
CREATE TABLE IF NOT EXISTS crypto_transactions (
    transaction_id TEXT PRIMARY KEY,
    from_address TEXT,
    to_address TEXT,
    value_usd DECIMAL(18, 8),
    transaction_fee DECIMAL(18, 8),
    transaction_date TIMESTAMP,
    blockchain VARCHAR(50)
)
''')

# Create alerts table
cursor.execute('''
CREATE TABLE IF NOT EXISTS crypto_alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    alert_type VARCHAR(50),
    alert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    risk_score DECIMAL(5, 2)
)
''')

conn.commit()
