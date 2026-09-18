import os
import random
import numpy as np
import pandas as pd
from typing import Tuple

def generate_ml_dataset(num_samples: int = 3000, random_seed: int = 42) -> pd.DataFrame:
    """Generates a realistic synthetic dataset of PS14 document consistency patterns."""
    np.random.seed(random_seed)
    random.seed(random_seed)

    records = []
    classes = ["CONSISTENT", "SALARY_MISMATCH", "EMI_MISMATCH", "EMPLOYMENT_MISMATCH", "MULTIPLE_MISMATCH", "DATA_QUALITY_ISSUE"]
    weights = [0.35, 0.20, 0.15, 0.12, 0.10, 0.08]

    for i in range(num_samples):
        cls = np.random.choice(classes, p=weights)
        
        # Base realistic applicant values
        base_salary = float(np.random.choice([30000, 45000, 60000, 80000, 100000, 150000]))
        base_emi = float(np.random.choice([0, 3000, 5000, 8000, 12000, 20000]))
        emp_diff_days = 0

        declared_salary = base_salary
        salary_slip_salary = base_salary
        bank_salary_average = base_salary
        salary_credit_count = random.randint(2, 6)

        declared_emi = base_emi
        liability_emi = base_emi
        bank_recurring_emi = base_emi
        recurring_emi_count = random.randint(1, 4) if base_emi > 0 else 0

        missing_doc_count = 0
        missing_field_count = 0
        extraction_failure_count = 0
        low_confidence_count = 0

        if cls == "CONSISTENT":
            # Minor random noise within 2%
            salary_slip_salary = round(base_salary * (1 + np.random.uniform(-0.02, 0.02)), 2)
            bank_salary_average = round(base_salary * (1 + np.random.uniform(-0.02, 0.02)), 2)
            if base_emi > 0:
                liability_emi = round(base_emi * (1 + np.random.uniform(-0.02, 0.02)), 2)
                bank_recurring_emi = round(base_emi * (1 + np.random.uniform(-0.02, 0.02)), 2)
            emp_diff_days = random.choice([0, 0, 0, 1])

        elif cls == "SALARY_MISMATCH":
            # Salary differs by 15% to 50%
            dev = np.random.uniform(0.15, 0.50)
            if random.random() > 0.5:
                salary_slip_salary = round(base_salary * (1 - dev), 2)
                bank_salary_average = round(base_salary * (1 - dev), 2)
            else:
                salary_slip_salary = round(base_salary * (1 + dev), 2)
                bank_salary_average = round(base_salary * (1 + dev), 2)

        elif cls == "EMI_MISMATCH":
            # EMI differs by 20% to 100%
            dev_emi = np.random.uniform(2000, 15000)
            bank_recurring_emi = round(base_emi + dev_emi, 2)
            liability_emi = round(base_emi + dev_emi, 2)

        elif cls == "EMPLOYMENT_MISMATCH":
            # Employment date differs by 30 to 500 days
            emp_diff_days = random.randint(30, 500)

        elif cls == "MULTIPLE_MISMATCH":
            # Both salary and EMI differ
            salary_slip_salary = round(base_salary * 0.70, 2)
            bank_salary_average = round(base_salary * 0.70, 2)
            bank_recurring_emi = round(base_emi + 8000.0, 2)
            emp_diff_days = random.randint(15, 200)

        elif cls == "DATA_QUALITY_ISSUE":
            missing_doc_count = random.choice([1, 2])
            missing_field_count = random.choice([1, 2, 3])
            low_confidence_count = random.choice([0, 1, 2])
            if random.random() > 0.5:
                bank_salary_average = 0.0
                salary_credit_count = 0
            if random.random() > 0.5:
                bank_recurring_emi = 0.0
                recurring_emi_count = 0

        # Feature calculations
        sal_diff = round(abs(declared_salary - bank_salary_average), 2)
        sal_var_pct = round((sal_diff / declared_salary) * 100.0, 2) if declared_salary > 0 else 0.0

        emi_diff = round(abs(declared_emi - bank_recurring_emi), 2)
        emi_var_pct = round((emi_diff / declared_emi) * 100.0, 2) if declared_emi > 0 else (0.0 if emi_diff == 0 else 100.0)

        records.append({
            "case_id": f"CASE-{i+1:04d}",
            "declared_salary": declared_salary,
            "salary_slip_salary": salary_slip_salary,
            "bank_salary_average": bank_salary_average,
            "salary_credit_count": salary_credit_count,
            "declared_emi": declared_emi,
            "liability_emi": liability_emi,
            "bank_recurring_emi": bank_recurring_emi,
            "recurring_emi_count": recurring_emi_count,
            "salary_difference": sal_diff,
            "salary_variance_pct": sal_var_pct,
            "emi_difference": emi_diff,
            "emi_variance_pct": emi_var_pct,
            "employment_date_difference": emp_diff_days,
            "missing_document_count": missing_doc_count,
            "missing_field_count": missing_field_count,
            "extraction_failure_count": extraction_failure_count,
            "low_confidence_count": low_confidence_count,
            "consistency_pattern": cls
        })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    out_dir = os.path.join("loanlens", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ml_dataset.csv")
    df = generate_ml_dataset(3000)
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} samples saved to {out_path}")
