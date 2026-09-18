import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

def train_and_evaluate():
    # Load dataset
    df = pd.read_csv("data/processed/train_dataset.csv")
    
    # Feature Engineering / Feature Selection
    feature_cols = [
        "declared_salary", "declared_emi", "slip_salary", 
        "bank_salary_average", "bank_emi_total", "employer_match_score",
        "slip_extraction_confidence", "missing_document_count", 
        "missing_field_count", "low_confidence_count", "extraction_failure_count"
    ]
    
    X = df[feature_cols]
    y = df["consistency_category"]
    
    # Train-Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("--- Training Logistic Regression ---")
    log_reg = LogisticRegression(max_iter=1000, random_state=42)
    log_reg.fit(X_train, y_train)
    y_pred_lr = log_reg.predict(X_test)
    print(f"Logistic Regression Accuracy: {accuracy_score(y_test, y_pred_lr):.4f}")
    
    print("\n--- Training Random Forest ---")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    print(f"Random Forest Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}\n")
    
    print("--- Random Forest Classification Report ---")
    print(classification_report(y_test, y_pred_rf))
    
    # Save the trained Random Forest model
    os.makedirs("models", exist_ok=True)
    joblib.dump(rf, "models/random_forest_model.pkl")
    print("Model saved successfully as 'models/random_forest_model.pkl'")

if __name__ == "__main__":
    train_and_evaluate()