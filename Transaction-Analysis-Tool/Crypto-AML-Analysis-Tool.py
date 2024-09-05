import pandas as pd
import sqlite3
import datetime
import networkx as nx
import matplotlib.pyplot as plt
import logging
import os
import signal
import sys
from config import (THRESHOLD_VALUE_USD, HIGH_RISK_ADDRESSES, FREQUENT_TXN_LIMIT, 
                    GRAPH_ANALYSIS_LIMIT, MONITORING_INTERVAL, DATABASE_NAME, ARCHIVE_AGE_DAYS)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Graceful shutdown handler
def signal_handler(sig, frame):
    logging.info('Shutting down gracefully...')
    conn.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def connect_to_db(db_name):
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect(db_name)
        logging.info(f"Connected to database {db_name} successfully.")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        sys.exit(1)

def validate_transaction_data(transactions):
    """Validate transaction data for missing or incorrect values."""
    invalid_transactions = transactions[
        (transactions['value_usd'] <= 0) | 
        transactions[['transaction_date', 'value_usd', 'from_address', 'to_address']].isnull().any(axis=1)
    ]
    
    for _, row in invalid_transactions.iterrows():
        if row['value_usd'] <= 0:
            logging.warning(f"Invalid transaction value: {row['value_usd']} for transaction ID {row['transaction_id']}")
        if pd.isnull(row[['transaction_date', 'value_usd', 'from_address', 'to_address']]).any():
            logging.warning(f"Missing data in transaction ID {row['transaction_id']}")

def analyze_transactions(conn):
    """Analyze unprocessed transactions using various detection algorithms."""
    try:
        transactions = pd.read_sql("SELECT * FROM crypto_transactions WHERE processed = 0", conn, parse_dates=['transaction_date'])
        
        if transactions.empty:
            logging.info("No new transactions to process.")
            return
        
        validate_transaction_data(transactions)

        flagged_threshold = transactions[transactions['value_usd'] > THRESHOLD_VALUE_USD]
        flagged_high_risk = transactions[
            transactions['from_address'].isin(HIGH_RISK_ADDRESSES) | 
            transactions['to_address'].isin(HIGH_RISK_ADDRESSES)
        ]
        flagged_frequent = detect_frequent_transactions(transactions)
        flagged_complex = detect_complex_patterns(transactions)

        all_flagged = pd.concat([flagged_threshold, flagged_high_risk, flagged_frequent, flagged_complex]).drop_duplicates()

        for _, row in all_flagged.iterrows():
            risk_score = calculate_risk_score(row)
            log_alert(conn, row['transaction_id'], risk_score)
        
        mark_transactions_processed(conn, transactions['transaction_id'].tolist())

    except Exception as e:
        logging.error(f"Error analyzing transactions: {e}")

def detect_frequent_transactions(transactions):
    """Detect transactions that occur too frequently from the same address."""
    flagged_frequent = transactions.groupby('from_address').apply(
        lambda x: x.set_index('transaction_date').sort_index().diff().transaction_date < pd.Timedelta(minutes=10)
    ).reset_index().query('transaction_date == True')
    
    logging.info(f"Detected {len(flagged_frequent)} frequent transactions.")
    return flagged_frequent

def detect_complex_patterns(transactions):
    """Detect complex transaction patterns using network analysis."""
    if len(transactions) > GRAPH_ANALYSIS_LIMIT:
        logging.info("Skipping complex pattern detection due to large transaction set.")
        return pd.DataFrame()  # Return empty DataFrame if too large

    G = nx.from_pandas_edgelist(transactions, 'from_address', 'to_address', ['value_usd'])

    clusters = nx.connected_components(G)
    flagged_transactions = []

    for cluster in clusters:
        subgraph = G.subgraph(cluster)
        if len(subgraph.nodes) > FREQUENT_TXN_LIMIT:
            flagged_transactions.extend(subgraph.edges(data=True))

    flagged_df = pd.DataFrame(flagged_transactions, columns=['from_address', 'to_address', 'data'])
    flagged_df['transaction_id'] = flagged_df['data'].apply(lambda x: x.get('transaction_id'))
    
    logging.info(f"Detected {len(flagged_df)} complex pattern transactions.")
    return flagged_df.drop(columns='data')

def calculate_risk_score(transaction):
    """Calculate risk score based on transaction attributes."""
    score = 0
    if transaction['value_usd'] > THRESHOLD_VALUE_USD:
        score += 30
    if transaction['from_address'] in HIGH_RISK_ADDRESSES or transaction['to_address'] in HIGH_RISK_ADDRESSES:
        score += 50
    if transaction['transaction_id'] in detect_complex_patterns(pd.DataFrame())['transaction_id'].values:
        score += 20
    return min(score, 100)

def log_alert(conn, transaction_id, risk_score):
    """Log alerts for flagged transactions."""
    alert_type = 'High Risk' if risk_score >= 70 else 'Moderate Risk'
    try:
        with conn:
            conn.execute(
                "INSERT INTO crypto_alerts (transaction_id, alert_type, risk_score) VALUES (?, ?, ?)",
                (transaction_id, alert_type, risk_score)
            )
        logging.info(f"Alert logged for transaction ID {transaction_id}: {alert_type} with risk score {risk_score}")
    except Exception as e:
        logging.error(f"Failed to log alert for transaction ID {transaction_id}: {e}")

def mark_transactions_processed(conn, transaction_ids):
    """Mark transactions as processed after analysis."""
    try:
        with conn:
            conn.executemany(
                "UPDATE crypto_transactions SET processed = 1 WHERE transaction_id = ?",
                [(tid,) for tid in transaction_ids]
            )
        logging.info(f"Marked transactions as processed: {transaction_ids}")
    except Exception as e:
        logging.error(f"Failed to mark transactions as processed: {e}")

def archive_old_transactions(conn):
    """Archive transactions older than a specified age to a separate table."""
    try:
        archive_date = datetime.datetime.now() - datetime.timedelta(days=ARCHIVE_AGE_DAYS)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO crypto_transactions_archive SELECT * FROM crypto_transactions WHERE transaction_date < ?", 
                (archive_date,)
            )
            cursor.execute(
                "DELETE FROM crypto_transactions WHERE transaction_date < ?", 
                (archive_date,)
            )
        logging.info(f"Archived transactions older than {ARCHIVE_AGE_DAYS} days.")
    except Exception as e:
        logging.error(f"Error archiving old transactions: {e}")

def run_monitoring_loop(conn, interval=MONITORING_INTERVAL):
    """Continuously run the monitoring loop to analyze and archive transactions."""
    try:
        while True:
            analyze_transactions(conn)
            archive_old_transactions(conn)
            logging.info(f"Monitoring completed at {datetime.datetime.now()}")
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Monitoring loop interrupted. Exiting...")

if __name__ == "__main__":
    conn = connect_to_db(DATABASE_NAME)
    run_monitoring_loop(conn)
