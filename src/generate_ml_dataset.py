import os
import pandas as pd
import numpy as np

def generate_ml_dataset(n_samples=3000):
    np.random.seed(42)
    
    categories = [
        "CONSISTENT", 
        "SALARY_MISMATCH", 
        "EMI_MISMATCH", 
        "EMPLOYMENT_MISMATCH", 
        "MULTIPLE_MISMATCH", 
        "DATA_QUALITY_ISSUE"
    ]
    probs = [0.40, 0.15, 0.15, 0.10, 0.10, 0.10]
    
    data = []
    
    for i in range(n_samples):
        cat = np.random.choice(categories, p=probs)
        
        declared_salary = round(float(np.random.normal(75000, 15000)), 2)
        declared_emi = round(float(declared_salary * np.random.uniform(0.1, 0.35)), 2)
        
        slip_salary = declared_salary
        bank_salary = declared_salary
        bank_emi = declared_emi
        
        confidence = 0.95
        missing_docs = 0
        missing_fields = 0
        low_conf_count = 0
        extraction_failures = 0
        emp_match = 1
        
        if cat == "SALARY_MISMATCH":
            bank_salary = round(declared_salary * np.random.uniform(0.5, 0.8), 2)
        elif cat == "EMI_MISMATCH":
            bank_emi = round(declared_emi * np.random.uniform(1.5, 2.5), 2)
        elif cat == "EMPLOYMENT_MISMATCH":
            emp_match = 0
        elif cat == "MULTIPLE_MISMATCH":
            bank_salary = round(declared_salary * 0.6, 2)
            bank_emi = round(declared_emi * 2.0, 2)
        elif cat == "DATA_QUALITY_ISSUE":
            confidence = round(float(np.random.uniform(0.1, 0.4)), 2)
            missing_docs = np.random.randint(1, 3)
            missing_fields = np.random.randint(1, 4)
            low_conf_count = np.random.randint(1, 3)
            extraction_failures = 1
            
        data.append({
            "case_id": f"SYN_{i+1:04d}",
            "declared_salary": declared_salary,
            "declared_emi": declared_emi,
            "slip_salary": slip_salary,
            "bank_salary_average": bank_salary,
            "bank_emi_total": bank_emi,
            "employer_match_score": emp_match,
            "slip_extraction_confidence": confidence,
            "missing_document_count": missing_docs,
            "missing_field_count": missing_fields,
            "low_confidence_count": low_conf_count,
            "extraction_failure_count": extraction_failures,
            "consistency_category": cat
        })
        
    df = pd.DataFrame(data)
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/train_dataset.csv", index=False)
    print(f"Dataset with {n_samples} records successfully generated at 'data/processed/train_dataset.csv'")

if __name__ == "__main__":
    generate_ml_dataset()