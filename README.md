## Project 1: Transaction Monitoring System Simulation

### Overview

This project simulates a transaction monitoring system to detect suspicious financial activities based on predefined AML rules. The system uses Python and SQLite to flag unusual transactions, such as those above a certain threshold or involving high-risk countries.

### Key Features

* Real-time monitoring of transactions.
* Advanced SQL queries to detect high-risk activities.
* Configurable rules via config.py.
* Graceful shutdown and error handling.
* Data retention and archival of old transactions.

### Setup Instructions

**Clone the Repository**

```bash
git clone https://github.com/CameronK03/aml-fraud-detection-projects.git
cd aml-fraud-detection-projects/Transaction-Monitoring-System
```

**Install Dependencies**

```bash
pip install -r requirements.txt
```

**Initialize the Database**

```bash
python SQLite_DB_init.py
```

**Run the Monitoring System**

```bash
python Transaction-Monitoring-System.py
```

## Project 2: Crypto Transaction Analysis Tool

### Overview

A tool to analyze cryptocurrency transactions for potential AML violations, identifying patterns indicative of money laundering or fraud.

### Key Features

* Real-time analysis of crypto transactions.
* Detection of high-risk transactions and complex laundering patterns.
* Uses network analysis with networkx to detect complex patterns.
* Configurable rules via config.py.

### Setup Instructions

**Clone the Repository**

```bash
git clone https://github.com/CameronK03/aml-fraud-detection-projects.git
cd aml-fraud-detection-projects/Crypto-AML-Analysis-Tool
```

**Install Dependencies**

```bash
pip install -r requirements.txt
```

**Initialize the Database**

```bash
python SQLite_DB_init.py
```

**Run the Analysis Tool**

```bash
python Crypto-AML-Analysis-Tool.py
```

## Project 3: Data Pipeline for Financial Compliance Reporting

### Overview

An ETL pipeline using Apache Airflow to automate the extraction, transformation, and loading (ETL) of transaction data for compliance reporting.

### Key Features

* Automated ETL pipeline using Apache Airflow.
* Extraction from multiple data sources (CSV files, SQLite databases).
* Data transformation including cleaning and applying business rules.
* Data loading into a reporting database and generating compliance reports.

### Setup Instructions

**Clone the Repository**

```bash
git clone https://github.com/CameronK03/aml-fraud-detection-projects.git
cd aml-fraud-detection-projects/Financial-Compliance-ETL-Pipeline
```

**Install Dependencies**

```bash
pip install -r requirements.txt
```

**Install Apache Airflow**

```bash
pip install apache-airflow
airflow db init
airflow users create --username admin --password admin --firstname FIRSTNAME --lastname LASTNAME --role Admin --email admin@example.com
```

**Start Airflow Services**

```bash
airflow scheduler &
airflow webserver --port 8080 &
```

**Run the ETL Pipeline**

Add the `financial_compliance_etl.py` script to your Airflow DAGs folder and trigger it from the Airflow web interface.

## Project 4: Machine Learning Model for Fraud Detection

### Overview

Develops a supervised learning model to detect fraudulent transactions within a dataset using advanced machine learning techniques.

### Key Features

* Data preprocessing, feature selection, and model training.
* Hyperparameter tuning for optimal model performance.
* Model evaluation using cross-validation and various metrics.
* Deployment script for real-time predictions using Flask.

### Setup Instructions

**Clone the Repository**

```bash
git clone https://github.com/CameronK03/aml-fraud-detection-projects.git
cd aml-fraud-detection-projects/Fraud-Detection-ML-Model
```

**Install Dependencies**

```bash
pip install -r requirements.txt
```

**Run the Scripts**

* Data Preprocessing: `python scripts/preprocess.py`
* Model Training: `python scripts/train_model.py`
* Model Evaluation: `python scripts/evaluate_model.py`
* Deploy the Model (Optional): `python scripts/deploy_model.py`

## Project 5: Automated Compliance Documentation Generator

### Overview

Creates a tool that automatically generates compliance documentation (Suspicious Activity Reports - SARs) based on transaction monitoring outputs.

### Key Features

* Parses monitoring data and applies compliance rules.
* Generates formatted SAR documents using Jinja2 templates and FPDF.
* Supports parallel processing for efficient document generation.

### Setup Instructions

**Clone the Repository**

```bash
git clone https://github.com/CameronK03/aml-fraud-detection-projects.git
cd aml-fraud-detection-projects/Compliance-Doc-Generator
```

**Install Dependencies**

```bash
pip install -r requirements.txt
```

**Run the Documentation Generator**

```bash
python Compliance-Doc-Generator.py
```

**General Notes:**

Ensure all necessary Python dependencies are installed by running:

```bash
pip install -r requirements.txt
```
