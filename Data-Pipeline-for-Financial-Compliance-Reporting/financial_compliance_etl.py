from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import pandas as pd
import os
import logging
from sqlalchemy import create_engine
from airflow.models import Variable

# Default args for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'financial_compliance_etl',
    default_args=default_args,
    description='ETL pipeline for financial compliance reporting',
    schedule_interval='@daily',
    catchup=False,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Utility function to fetch Airflow variables or default values
def get_variable(key, default_value):
    return Variable.get(key, default_value, deserialize_json=True)

# Extraction function
def extract_data(**kwargs):
    try:
        csv_path = get_variable('CSV_PATH', '/path/to/transactions.csv')
        db_path = get_variable('DB_PATH', 'sqlite:///transaction_source.db')
        temp_path = get_variable('TEMP_PATH', '/path/to/temp/')

        csv_data = pd.read_csv(csv_path)
        with create_engine(db_path).connect() as conn:
            db_data = pd.read_sql('SELECT * FROM transactions WHERE processed = 0', conn)

        combined_data = pd.concat([csv_data, db_data], ignore_index=True)
        extracted_data_path = os.path.join(temp_path, 'extracted_data.csv')
        combined_data.to_csv(extracted_data_path, index=False)
        
        logging.info(f"Data extracted successfully to {extracted_data_path}.")
        kwargs['ti'].xcom_push(key='extracted_data_path', value=extracted_data_path)

    except Exception as e:
        logging.exception("Error during data extraction")
        raise

# Transformation function
def transform_data(**kwargs):
    try:
        temp_path = get_variable('TEMP_PATH', '/path/to/temp/')
        extracted_data_path = kwargs['ti'].xcom_pull(key='extracted_data_path', task_ids='extract_data')
        data = pd.read_csv(extracted_data_path)

        data['transaction_date'] = pd.to_datetime(data['transaction_date'])
        data = data[data['amount'] > 0]
        data['amount'] = data['amount'].round(2)

        transformed_data = data[data['amount'] > 1000]
        transformed_data_path = os.path.join(temp_path, 'transformed_data.csv')
        transformed_data.to_csv(transformed_data_path, index=False)
        
        logging.info(f"Data transformed successfully to {transformed_data_path}.")
        kwargs['ti'].xcom_push(key='transformed_data_path', value=transformed_data_path)

    except Exception as e:
        logging.exception("Error during data transformation")
        raise

# Loading function
def load_data(**kwargs):
    try:
        transformed_data_path = kwargs['ti'].xcom_pull(key='transformed_data_path', task_ids='transform_data')
        engine = create_engine(get_variable('REPORT_DB_PATH', 'sqlite:///reporting_db.db'))
        
        transformed_data = pd.read_csv(transformed_data_path)
        with engine.connect() as conn:
            transformed_data.to_sql('compliance_transactions', conn, if_exists='replace', index=False)
        
        logging.info("Data loading completed successfully.")

    except Exception as e:
        logging.exception("Error during data loading")
        raise

# Report generation function
def generate_reports(**kwargs):
    try:
        report_path = get_variable('REPORT_PATH', '/path/to/reports/')
        engine = create_engine(get_variable('REPORT_DB_PATH', 'sqlite:///reporting_db.db'))
        
        with engine.connect() as conn:
            compliance_data = pd.read_sql('SELECT * FROM compliance_transactions', conn)
        
        summary = compliance_data.groupby('transaction_type').agg({'amount': ['sum', 'count']})
        report_file = os.path.join(report_path, 'summary_report.csv')
        summary.to_csv(report_file)

        logging.info(f"Report generated successfully at {report_file}.")

    except Exception as e:
        logging.exception("Error during report generation")
        raise

# Define tasks in the DAG
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    provide_context=True,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    provide_context=True,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    provide_context=True,
    dag=dag,
)

report_task = PythonOperator(
    task_id='generate_reports',
    python_callable=generate_reports,
    provide_context=True,
    dag=dag,
)

# Set task dependencies
extract_task >> transform_task >> load_task >> report_task
