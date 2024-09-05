import os
import pandas as pd
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader
from fpdf import FPDF
from datetime import datetime
import logging
from multiprocessing import Pool, cpu_count

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define constants
DB_PATH = 'sqlite:///transaction_monitoring.db'  # Update this path to your actual database
TEMPLATE_DIR = 'templates'
OUTPUT_DIR = 'generated_reports'

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def load_alerts(db_path):
    """
    Load flagged transactions from the database.

    Parameters:
    db_path (str): The path to the SQLite database.

    Returns:
    DataFrame: Pandas DataFrame containing alerts data.
    """
    try:
        with create_engine(db_path).connect() as connection:
            query = "SELECT * FROM alerts"
            df = pd.read_sql(query, connection)
        logging.info(f"Loaded {len(df)} alerts from the database.")
        return df
    except Exception as e:
        logging.error(f"Error loading alerts: {e}")
        return pd.DataFrame()  # Return an empty DataFrame if there is an error

def validate_alert(alert):
    """
    Validate alert data before generating a SAR.

    Parameters:
    alert (Series): A pandas Series representing a single alert.

    Returns:
    bool: True if data is valid, False otherwise.
    """
    required_fields = ['transaction_id', 'alert_id', 'alert_type']
    missing_fields = [field for field in required_fields if pd.isnull(alert.get(field))]
    if missing_fields:
        logging.warning(f"Invalid data for alert ID {alert['alert_id']}: Missing fields {', '.join(missing_fields)}.")
        return False
    return True

def generate_sar(report_data, template_name='sar_template.html'):
    """
    Generate a SAR document from the provided data.

    Parameters:
    report_data (dict): Data required to populate the SAR template.
    template_name (str): The name of the Jinja2 template file.
    """
    try:
        template = env.get_template(template_name)
        report_content = template.render(report_data)

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, report_content)

        # Save PDF
        report_filename = os.path.join(OUTPUT_DIR, f"SAR_{report_data['report_id']}.pdf")
        pdf.output(report_filename)
        logging.info(f"Generated SAR for report ID {report_data['report_id']}")

    except Exception as e:
        logging.error(f"Error generating SAR for report ID {report_data['report_id']}: {e}")

def prepare_report_data(alert):
    """
    Prepare report data from an alert for SAR generation.

    Parameters:
    alert (Series): A pandas Series representing a single alert.

    Returns:
    dict: A dictionary containing data for SAR generation.
    """
    return {
        'report_id': alert['alert_id'],
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'subject_name': alert.get('subject_name', 'John Doe'),  # Replace with actual data if available
        'account_number': alert.get('account_number', '1234567890'),  # Replace with actual data if available
        'transaction_id': alert['transaction_id'],
        'activity_description': alert['alert_type'],
        'comments': 'Automatically generated SAR for suspicious activity.'
    }

def generate_sar_from_alert(alert):
    """
    Helper function to generate SAR from an alert.

    Parameters:
    alert (Series): A pandas Series representing a single alert.
    """
    if validate_alert(alert):
        report_data = prepare_report_data(alert)
        generate_sar(report_data)

def generate_reports():
    """
    Generate SARs for all valid alerts in parallel using multiprocessing.
    """
    alerts = load_alerts(DB_PATH)

    # Filter and validate alerts
    valid_alerts = [alert for _, alert in alerts.iterrows() if validate_alert(alert)]

    # Generate reports in parallel
    num_workers = min(cpu_count(), len(valid_alerts))  # Use number of CPUs or number of alerts, whichever is smaller
    with Pool(processes=num_workers) as pool:
        pool.map(generate_sar_from_alert, valid_alerts)

if __name__ == "__main__":
    generate_reports()
    logging.info("Compliance documentation generation completed successfully.")
