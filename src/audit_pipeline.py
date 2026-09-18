import os
import json
import pandas as pd
import joblib

def audit_cases():
    model = joblib.load("models/random_forest_model.pkl")
    cases_dir = "data/raw/cases"
    
    if not os.path.exists(cases_dir):
        print("No cases directory found!")
        return

    case_ids = sorted(os.listdir(cases_dir))
    audit_results = []

    for cid in case_ids:
        cpath = os.path.join(cases_dir, cid)
        if not os.path.isdir(cpath):
            continue

        # Load Application Data
        app_file = os.path.join(cpath, "application.json")
        with open(app_file) as f:
            app = json.load(f)

        # Load Liability Data
        liab_file = os.path.join(cpath, "liability.json")
        with open(liab_file) as f:
            liab = json.load(f)

        # Load Bank Statement Data
        bank_file = os.path.join(cpath, "bank_statement.csv")
        bank_df = pd.read_csv(bank_file)
        
        salary_txns = bank_df[bank_df['description'].str.contains('SALARY', na=False)]
        bank_salary = salary_txns['amount'].values[0] if not salary_txns.empty else 0.0

        emi_txns = bank_df[bank_df['description'].str.contains('EMI', na=False)]
        bank_emi = emi_txns['amount'].values[0] if not emi_txns.empty else 0.0

        # Features for ML Prediction
        features = pd.DataFrame([{
            "declared_salary": app["declared_monthly_income"],
            "declared_emi": app["declared_emi"],
            "slip_salary": app["declared_monthly_income"], # Default alignment
            "bank_salary_average": bank_salary,
            "bank_emi_total": bank_emi,
            "employer_match_score": 1 if app["employer_name"] != "Unknown Enterprise" else 0,
            "slip_extraction_confidence": 0.95 if bank_salary > 0 else 0.2,
            "missing_document_count": 0 if bank_salary > 0 else 1,
            "missing_field_count": 0,
            "low_confidence_count": 0,
            "extraction_failure_count": 0 if bank_salary > 0 else 1
        }])

        pred_cat = model.predict(features)[0]

        audit_results.append({
            "Case ID": cid,
            "Applicant Salary": app["declared_monthly_income"],
            "Bank Salary": bank_salary,
            "Applicant EMI": app["declared_emi"],
            "Bank EMI": bank_emi,
            "Predicted Status": pred_cat
        })

    summary_df = pd.DataFrame(audit_results)
    os.makedirs("reports", exist_ok=True)
    summary_df.to_csv("reports/audit_summary.csv", index=False)
    
    print("\n================ AUDIT SUMMARY REPORT ================")
    print(summary_df.to_string(index=False))
    print("\nAudit report generated at 'reports/audit_summary.csv'")

if __name__ == "__main__":
    audit_cases()