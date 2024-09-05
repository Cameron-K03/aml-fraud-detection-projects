import pandas as pd
import sqlite3
import datetime
import time
import logging
import os
import signal
import sys
from config import THRESHOLD_AMOUNT, HIGH_RISK_COUNTRIES, TRANSACTION_FREQUENCY_LIMIT, ROUND_AMOUNT_MULTIPLE, MONITORING_INTERVAL, DATABASE_NAME, ARCHIVE_AGE_DAYS

# Connect to SQLite database
conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Graceful shutdown handler
def signal_handler(sig, frame):
    logging.info('Shutting down gracefully...')
    conn.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Function to validate transaction data
def validate_transaction_data(transactions):
    for index, row in transactions.iterrows():
        if row['amount'] <= 0:
            logging.warning(f"Invalid transaction amount: {row['amount']} for transaction ID {row['transaction_id']}")
        if pd.isnull(row['transaction_date']) or pd.isnull(row['amount']) or pd.isnull(row['account_id']):
            logging.warning(f"Missing data in transaction ID {row['transaction_id']}")

# Function to monitor transactions using advanced SQL
def monitor_transactions():
    try:
        # Fetch only unprocessed transactions
        transactions = pd.read_sql("SELECT * FROM transactions WHERE processed = 0", conn, parse_dates=['transaction_date'])
        if transactions.empty:
            logging.info("No new transactions to process.")
            return

        # Validate transaction data
        validate_transaction_data(transactions)

        # Process transactions using advanced SQL queries
        alerts = generate_alerts(transactions)

        # Log alerts and update transaction status
        for index, row in alerts.iterrows():
            log_alert(row['transaction_id'], row['alert_type'])
        
        # Mark transactions as processed
        mark_transactions_processed(transactions['transaction_id'].tolist())

    except Exception as e:
        logging.error(f"Error processing transactions: {e}")

def mark_transactions_processed(transaction_ids):
    with conn:
        conn.executemany("UPDATE transactions SET processed = 1 WHERE transaction_id = ?", [(tid,) for tid in transaction_ids])
    logging.info(f"Marked transactions as processed: {transaction_ids}")

def generate_alerts(transactions):
    # Combine advanced SQL queries for alerts generation
    query = """
    WITH high_risk_countries AS (
        SELECT transaction_id, 'High-Risk Country' AS alert_type
        FROM transactions
        WHERE country IN ({})
    ),
    rapid_succession AS (
        SELECT transaction_id, 'Rapid Succession' AS alert_type
        FROM (
            SELECT transaction_id, 
                   account_id,
                   transaction_date,
                   LAG(transaction_date) OVER (PARTITION BY account_id ORDER BY transaction_date) AS prev_transaction_date
            FROM transactions
        ) subquery
        WHERE prev_transaction_date IS NOT NULL 
              AND (strftime('%s', transaction_date) - strftime('%s', prev_transaction_date)) < 60
    ),
    round_amount AS (
        SELECT transaction_id, 'Round Amount' AS alert_type
        FROM transactions
        WHERE amount % {} = 0
    ),
    high_frequency AS (
        SELECT transaction_id, 'High Frequency' AS alert_type
        FROM (
            SELECT transaction_id,
                   account_id,
                   COUNT(*) OVER (PARTITION BY account_id, DATE(transaction_date)) AS transaction_count
            FROM transactions
        ) subquery
        WHERE transaction_count > {}
    ),
    new_payees AS (
        WITH payee_counts AS (
            SELECT account_id, payee_id, COUNT(*) AS count
            FROM transactions
            GROUP BY account_id, payee_id
        )
        SELECT transaction_id, 'New Payee' AS alert_type
        FROM transactions
        WHERE (account_id, payee_id) IN (SELECT account_id, payee_id FROM payee_counts WHERE count = 1)
    )
    SELECT * FROM high_risk_countries
    UNION ALL
    SELECT * FROM rapid_succession
    UNION ALL
    SELECT * FROM round_amount
    UNION ALL
    SELECT * FROM high_frequency
    UNION ALL
    SELECT * FROM new_payees;
    """.format(','.join(f"'{country}'" for country in HIGH_RISK_COUNTRIES), ROUND_AMOUNT_MULTIPLE, TRANSACTION_FREQUENCY_LIMIT)
    
    # Execute the combined query and fetch results
    return pd.read_sql(query, conn)

# Function to log alerts
def log_alert(transaction_id, alert_type):
    try:
        with conn:
            conn.execute("INSERT INTO alerts (transaction_id, alert_type) VALUES (?, ?)", (transaction_id, alert_type))
        logging.info(f"Alert logged for transaction ID {transaction_id}: {alert_type}")
    except Exception as e:
        logging.error(f"Failed to log alert for transaction ID {transaction_id}: {e}")

# Data retention function
def archive_old_transactions():
    try:
        archive_date = datetime.datetime.now() - datetime.timedelta(days=ARCHIVE_AGE_DAYS)
        cursor.execute("INSERT INTO transactions_archive SELECT * FROM transactions WHERE transaction_date < ?", (archive_date,))
        cursor.execute("DELETE FROM transactions WHERE transaction_date < ?", (archive_date,))
        conn.commit()
        logging.info(f"Archived transactions older than {ARCHIVE_AGE_DAYS} days.")
    except Exception as e:
        logging.error(f"Error archiving old transactions: {e}")

# Run monitoring in a loop
def run_monitoring_loop(interval=MONITORING_INTERVAL):
    while True:
        monitor_transactions()
        archive_old_transactions()
        logging.info(f"Monitoring completed at {datetime.datetime.now()}")
        time.sleep(interval)

if __name__ == "__main__":
    run_monitoring_loop()
