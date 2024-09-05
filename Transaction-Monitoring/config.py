# config.py

# AML Rule Configurations
THRESHOLD_AMOUNT = 10000
HIGH_RISK_COUNTRIES = ['North Korea', 'Iran', 'Afghanistan', 'Syria', 'Sudan', 'Yemen', 'Venezuela', 'Iraq', 'Myanmar', 'Libya']
TRANSACTION_FREQUENCY_LIMIT = 10
ROUND_AMOUNT_MULTIPLE = 1000

# Monitoring Configuration
MONITORING_INTERVAL = 300  # Interval in seconds

# Database Configuration
DATABASE_NAME = 'transaction_monitoring.db'

# Archive Configuration
ARCHIVE_AGE_DAYS = 30  # Number of days after which transactions are archived
