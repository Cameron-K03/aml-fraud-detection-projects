import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
import joblib

# Load preprocessed data
df = pd.read_csv('data/processed/creditcard_preprocessed.csv')
X = df.drop('Class', axis=1)
y = df['Class']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Initialize and train model with hyperparameter tuning
model = RandomForestClassifier(random_state=42)
param_grid = {...}  # Define your parameter grid
search = RandomizedSearchCV(model, param_grid, n_iter=50, cv=3, scoring='roc_auc', n_jobs=-1)
search.fit(X_train, y_train)

# Save the best model
joblib.dump(search.best_estimator_, 'models/fraud_detection_model.pkl')
