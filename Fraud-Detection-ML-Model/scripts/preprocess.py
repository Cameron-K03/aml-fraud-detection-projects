import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

# Load the dataset
df = pd.read_csv('/path/to/creditcard.csv')

# Preprocessing: Handle missing values, scale features
# Assuming no missing values for simplicity
scaler = StandardScaler()
df[['Amount', 'Time']] = scaler.fit_transform(df[['Amount', 'Time']])

# Save preprocessed data if needed
df.to_csv('data/processed/creditcard_preprocessed.csv', index=False)

# Save the scaler for later use
joblib.dump(scaler, 'models/scaler.pkl')
