import os
import json
import csv
from datetime import date, datetime, timedelta

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
TEST_CASES_DIR = os.path.join(DATA_DIR, "test_cases")

def ensure_directories():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(TEST_CASES_DIR, exist_ok=True)

# Define 20 Test Cases with strict logical relationships
TEST_CASE_SPECS = [
    {
        "tc_id": "TC001",
        "applicant_id": "APP-2026-001",
        "name": "Alice Walker",
        "scenario": "Completely Consistent Application",
        "declared_salary": 8500.0,
        "payslip_salary": 8500.0,
        "bank_salary": 8500.0,
        "declared_emi": 600.0,
        "bureau_emi": 600.0,
        "app_date": "2026-09-01",
        "emp_start_app": "2021-03-15",
        "emp_start_slip": "2021-03-15",
        "expected_status": "PASS",
        "expected_inconsistencies": [],
        "expected_flag_count": 0
    },
    {
        "tc_id": "TC002",
        "applicant_id": "APP-2026-002",
        "name": "Bob Martinez",
        "scenario": "Salary Mismatch",
        "declared_salary": 14000.0,
        "payslip_salary": 8000.0,
        "bank_salary": 8000.0,
        "declared_emi": 800.0,
        "bureau_emi": 800.0,
        "app_date": "2026-09-01",
        "emp_start_app": "2020-05-10",
        "emp_start_slip": "2020-05-10",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["SALARY_MISMATCH_INFLATED"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC003",
        "applicant_id": "APP-2026-003",
        "name": "Charlie Davis",
        "scenario": "EMI Mismatch",
        "declared_salary": 9000.0,
        "payslip_salary": 9000.0,
        "bank_salary": 9000.0,
        "declared_emi": 400.0,
        "bureau_emi": 2500.0,
        "app_date": "2026-09-02",
        "emp_start_app": "2019-01-20",
        "emp_start_slip": "2019-01-20",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["UNDECLARED_EXISTING_EMI"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC004",
        "applicant_id": "APP-2026-004",
        "name": "Diana Evans",
        "scenario": "Employment Date Mismatch",
        "declared_salary": 7500.0,
        "payslip_salary": 7500.0,
        "bank_salary": 7500.0,
        "declared_emi": 500.0,
        "bureau_emi": 500.0,
        "app_date": "2026-09-02",
        "emp_start_app": "2018-06-01",
        "emp_start_slip": "2024-11-15",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["EMPLOYMENT_DATE_MISMATCH"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC005",
        "applicant_id": "APP-2026-005",
        "name": "Ethan Hunt",
        "scenario": "Multiple Mismatches",
        "declared_salary": 16000.0,
        "payslip_salary": 9500.0,
        "bank_salary": 9500.0,
        "declared_emi": 600.0,
        "bureau_emi": 3200.0,
        "app_date": "2026-09-03",
        "emp_start_app": "2017-02-01",
        "emp_start_slip": "2023-08-01",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["SALARY_MISMATCH_INFLATED", "UNDECLARED_EXISTING_EMI", "EMPLOYMENT_DATE_MISMATCH", "HIGH_DTI_RATIO"],
        "expected_flag_count": 4
    },
    {
        "tc_id": "TC006",
        "applicant_id": "APP-2026-006",
        "name": "Fiona Gallagher",
        "scenario": "Missing Salary Information in Bank",
        "declared_salary": 6500.0,
        "payslip_salary": 6500.0,
        "bank_salary": 0.0,
        "declared_emi": 300.0,
        "bureau_emi": 300.0,
        "app_date": "2026-09-03",
        "emp_start_app": "2022-04-10",
        "emp_start_slip": "2022-04-10",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["MISSING_SALARY_CREDITS"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC007",
        "applicant_id": "APP-2026-007",
        "name": "George Clark",
        "scenario": "Missing Salary Slip Document",
        "declared_salary": 8000.0,
        "payslip_salary": None,
        "bank_salary": 8000.0,
        "declared_emi": 700.0,
        "bureau_emi": 700.0,
        "app_date": "2026-09-04",
        "emp_start_app": "2020-10-01",
        "emp_start_slip": None,
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["MISSING_SALARY_SLIP_DOCUMENT"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC008",
        "applicant_id": "APP-2026-008",
        "name": "Hannah Abbott",
        "scenario": "Low Confidence Extraction Scenario",
        "declared_salary": 7200.0,
        "payslip_salary": 7200.0,
        "bank_salary": 7200.0,
        "declared_emi": 500.0,
        "bureau_emi": 500.0,
        "app_date": "2026-09-04",
        "emp_start_app": "2021-01-15",
        "emp_start_slip": "2021-01-15",
        "corrupted_ocr": True,
        "expected_status": "MANUAL_REVIEW",
        "expected_inconsistencies": ["EXTRACTION_FAILURE_LOW_CONFIDENCE"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC009",
        "applicant_id": "APP-2026-009",
        "name": "Ian Malcolm",
        "scenario": "Recurring EMI Not Declared in Application",
        "declared_salary": 11000.0,
        "payslip_salary": 11000.0,
        "bank_salary": 11000.0,
        "declared_emi": 0.0,
        "bureau_emi": 2100.0,
        "app_date": "2026-09-05",
        "emp_start_app": "2019-07-01",
        "emp_start_slip": "2019-07-01",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["UNDECLARED_EXISTING_EMI"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC010",
        "applicant_id": "APP-2026-010",
        "name": "Julia Roberts",
        "scenario": "Small Acceptable Salary Variance",
        "declared_salary": 10000.0,
        "payslip_salary": 9850.0,
        "bank_salary": 9800.0,
        "declared_emi": 1200.0,
        "bureau_emi": 1200.0,
        "app_date": "2026-09-05",
        "emp_start_app": "2020-03-01",
        "emp_start_slip": "2020-03-01",
        "expected_status": "PASS",
        "expected_inconsistencies": [],
        "expected_flag_count": 0
    },
    {
        "tc_id": "TC011",
        "applicant_id": "APP-2026-011",
        "name": "Kevin Bacon",
        "scenario": "Multiple Liabilities",
        "declared_salary": 13000.0,
        "payslip_salary": 13000.0,
        "bank_salary": 13000.0,
        "declared_emi": 1500.0,
        "bureau_emi": 4800.0,
        "app_date": "2026-09-06",
        "emp_start_app": "2016-09-15",
        "emp_start_slip": "2016-09-15",
        "multi_liabilities": True,
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["UNDECLARED_EXISTING_EMI"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC012",
        "applicant_id": "APP-2026-012",
        "name": "Laura Croft",
        "scenario": "Salary Mismatch + Undeclared Liability",
        "declared_salary": 15000.0,
        "payslip_salary": 9000.0,
        "bank_salary": 9000.0,
        "declared_emi": 500.0,
        "bureau_emi": 2800.0,
        "app_date": "2026-09-06",
        "emp_start_app": "2021-05-01",
        "emp_start_slip": "2021-05-01",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["SALARY_MISMATCH_INFLATED", "UNDECLARED_EXISTING_EMI"],
        "expected_flag_count": 2
    },
    {
        "tc_id": "TC013",
        "applicant_id": "APP-2026-013",
        "name": "Michael Scott",
        "scenario": "Employment Date Mismatch + High DTI Ratio",
        "declared_salary": 6000.0,
        "payslip_salary": 6000.0,
        "bank_salary": 6000.0,
        "declared_emi": 3800.0,
        "bureau_emi": 3800.0,
        "app_date": "2026-09-07",
        "emp_start_app": "2015-04-01",
        "emp_start_slip": "2023-01-01",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["EMPLOYMENT_DATE_MISMATCH", "HIGH_DTI_RATIO"],
        "expected_flag_count": 2
    },
    {
        "tc_id": "TC014",
        "applicant_id": "APP-2026-014",
        "name": "Nancy Wheeler",
        "scenario": "Missing Tax ID + Salary Mismatch",
        "declared_salary": 11000.0,
        "payslip_salary": 7000.0,
        "bank_salary": 7000.0,
        "declared_emi": 600.0,
        "bureau_emi": 600.0,
        "app_date": "2026-09-07",
        "missing_tax_id": True,
        "emp_start_app": "2022-08-15",
        "emp_start_slip": "2022-08-15",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["MISSING_TAX_ID", "SALARY_MISMATCH_INFLATED"],
        "expected_flag_count": 2
    },
    {
        "tc_id": "TC015",
        "applicant_id": "APP-2026-015",
        "name": "Oscar Martinez",
        "scenario": "Low Confidence Extraction + Unrecognized Format",
        "declared_salary": 8800.0,
        "payslip_salary": 8800.0,
        "bank_salary": 8800.0,
        "declared_emi": 900.0,
        "bureau_emi": 900.0,
        "app_date": "2026-09-08",
        "emp_start_app": "2019-11-01",
        "emp_start_slip": "2019-11-01",
        "corrupted_ocr": True,
        "expected_status": "MANUAL_REVIEW",
        "expected_inconsistencies": ["EXTRACTION_FAILURE_LOW_CONFIDENCE"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC016",
        "applicant_id": "APP-2026-016",
        "name": "Peter Parker",
        "scenario": "Excessive Debt-to-Income (DTI > 75%)",
        "declared_salary": 5000.0,
        "payslip_salary": 5000.0,
        "bank_salary": 5000.0,
        "declared_emi": 4000.0,
        "bureau_emi": 4000.0,
        "app_date": "2026-09-08",
        "emp_start_app": "2021-09-01",
        "emp_start_slip": "2021-09-01",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["HIGH_DTI_RATIO"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC017",
        "applicant_id": "APP-2026-017",
        "name": "Quinn Fabray",
        "scenario": "Outdated Pay Period (Payslip > 90 Days)",
        "declared_salary": 9200.0,
        "payslip_salary": 9200.0,
        "bank_salary": 9200.0,
        "declared_emi": 700.0,
        "bureau_emi": 700.0,
        "app_date": "2026-09-09",
        "emp_start_app": "2020-07-15",
        "emp_start_slip": "2020-07-15",
        "payslip_period": "2026-01-31",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["OUTDATED_PAYSLIP_PERIOD"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC018",
        "applicant_id": "APP-2026-018",
        "name": "Rachel Berry",
        "scenario": "Zero Stated Income",
        "declared_salary": 0.0,
        "payslip_salary": 7800.0,
        "bank_salary": 7800.0,
        "declared_emi": 500.0,
        "bureau_emi": 500.0,
        "app_date": "2026-09-09",
        "emp_start_app": "2022-02-01",
        "emp_start_slip": "2022-02-01",
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["INVALID_STATED_INCOME"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC019",
        "applicant_id": "APP-2026-019",
        "name": "Steve Harrington",
        "scenario": "Incomplete Bank Statement History (1 Month)",
        "declared_salary": 8400.0,
        "payslip_salary": 8400.0,
        "bank_salary": 8400.0,
        "declared_emi": 600.0,
        "bureau_emi": 600.0,
        "app_date": "2026-09-10",
        "emp_start_app": "2021-06-01",
        "emp_start_slip": "2021-06-01",
        "bank_months": 1,
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["INCOMPLETE_STATEMENT_HISTORY"],
        "expected_flag_count": 1
    },
    {
        "tc_id": "TC020",
        "applicant_id": "APP-2026-020",
        "name": "Tony Stark",
        "scenario": "Complex Profile (Multiple Liabilities + Undeclared EMI + Salary Variance)",
        "declared_salary": 25000.0,
        "payslip_salary": 18000.0,
        "bank_salary": 18000.0,
        "declared_emi": 2000.0,
        "bureau_emi": 8500.0,
        "app_date": "2026-09-10",
        "emp_start_app": "2014-01-01",
        "emp_start_slip": "2014-01-01",
        "multi_liabilities": True,
        "expected_status": "FLAGGED",
        "expected_inconsistencies": ["SALARY_MISMATCH_INFLATED", "UNDECLARED_EXISTING_EMI"],
        "expected_flag_count": 2
    }
]

def generate_synthetic_data():
    ensure_directories()
    
    applications_list = []
    salary_slips_list = []
    liabilities_list = []
    manifest_list = []

    for spec in TEST_CASE_SPECS:
        tc_id = spec["tc_id"]
        app_id = spec["applicant_id"]
        name = spec["name"]

        # 1. Application
        tax_id = None if spec.get("missing_tax_id") else f"PAN-{name.replace(' ', '').upper()[:5]}1234A"
        app_obj = {
            "test_case_id": tc_id,
            "application_id": app_id,
            "applicant_name": name,
            "tax_id": tax_id,
            "declared_monthly_salary": spec["declared_salary"],
            "declared_existing_emi": spec["declared_emi"],
            "requested_loan_amount": 150000.0,
            "requested_tenure_months": 36,
            "employment_start_date": spec["emp_start_app"],
            "application_date": spec["app_date"]
        }
        applications_list.append(app_obj)

        # 2. Salary Slip (Skip if TC007)
        if spec["payslip_salary"] is not None:
            period_end = spec.get("payslip_period", "2026-08-31")
            slip_obj = {
                "test_case_id": tc_id,
                "application_id": app_id,
                "document_id": f"DOC-SLIP-{tc_id}",
                "employee_name": name,
                "employer_name": "Acme Technologies Corp",
                "net_pay": spec["payslip_salary"],
                "gross_pay": spec["payslip_salary"] * 1.2,
                "employment_start_date": spec["emp_start_slip"],
                "pay_period_end": period_end,
                "extraction_confidence": 0.35 if spec.get("corrupted_ocr") else 0.98,
                "raw_text": f"PAYSLIP FOR {name}\nNET PAY: {spec['payslip_salary']}\nJOIN DATE: {spec['emp_start_slip']}"
            }
            salary_slips_list.append(slip_obj)

        # 3. Liabilities
        if spec.get("multi_liabilities"):
            liabs = [
                {"liability_id": f"LIA-{tc_id}-1", "lender_name": "First National Bank", "loan_type": "Auto Loan", "monthly_emi": 1200.0, "outstanding_balance": 18000.0},
                {"liability_id": f"LIA-{tc_id}-2", "lender_name": "Apex Credit Card", "loan_type": "Credit Card", "monthly_emi": 800.0, "outstanding_balance": 4500.0},
                {"liability_id": f"LIA-{tc_id}-3", "lender_name": "City Housing Finance", "loan_type": "Home Loan", "monthly_emi": spec["bureau_emi"] - 2000.0, "outstanding_balance": 120000.0}
            ]
        else:
            liabs = [
                {"liability_id": f"LIA-{tc_id}-1", "lender_name": "Standard Credit Union", "loan_type": "Personal Loan", "monthly_emi": spec["bureau_emi"], "outstanding_balance": spec["bureau_emi"] * 24}
            ] if spec["bureau_emi"] > 0 else []

        liabilities_list.append({
            "test_case_id": tc_id,
            "application_id": app_id,
            "liabilities": liabs
        })

        # 4. Bank Transactions CSV (3 months or 1 month)
        num_months = spec.get("bank_months", 3)
        bank_csv_filename = os.path.join(RAW_DIR, f"bank_transactions_{tc_id}.csv")
        
        with open(bank_csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["transaction_id", "date", "description", "amount", "type", "is_salary", "is_recurring_debit"])
            
            tx_count = 1
            start_dt = datetime.strptime("2026-06-01", "%Y-%m-%d")
            
            for m in range(num_months):
                m_date = start_dt + timedelta(days=m * 30)
                m_str = m_date.strftime("%Y-%m-%d")
                
                # Salary Credit
                if spec["bank_salary"] > 0:
                    writer.writerow([f"TX-{tc_id}-{tx_count}", f"{m_str[:7]}-05", "ACME CORP SALARY CREDIT", spec["bank_salary"], "CREDIT", True, False])
                    tx_count += 1

                # Bureau EMI Debits
                if spec["bureau_emi"] > 0:
                    writer.writerow([f"TX-{tc_id}-{tx_count}", f"{m_str[:7]}-10", "RECURRING EMI AUTO-DEBIT", -spec["bureau_emi"], "DEBIT", False, True])
                    tx_count += 1

                # General Recurring Expense Debits
                writer.writerow([f"TX-{tc_id}-{tx_count}", f"{m_str[:7]}-15", "UTILITY & BILL PAYMENT", -450.0, "DEBIT", False, True])
                tx_count += 1
                writer.writerow([f"TX-{tc_id}-{tx_count}", f"{m_str[:7]}-20", "GROCERY & SUPERMARKET", -650.0, "DEBIT", False, False])
                tx_count += 1

        # 5. Expected Manifest Item
        manifest_list.append({
            "test_case_id": tc_id,
            "applicant_id": app_id,
            "applicant_name": name,
            "scenario": spec["scenario"],
            "expected_review_status": spec["expected_status"],
            "expected_inconsistencies": spec["expected_inconsistencies"],
            "expected_flag_count": spec["expected_flag_count"]
        })

    # Save Master Files
    with open(os.path.join(RAW_DIR, "applications.json"), "w", encoding="utf-8") as f:
        json.dump(applications_list, f, indent=2)

    with open(os.path.join(RAW_DIR, "salary_slips.json"), "w", encoding="utf-8") as f:
        json.dump(salary_slips_list, f, indent=2)

    with open(os.path.join(RAW_DIR, "liabilities.json"), "w", encoding="utf-8") as f:
        json.dump(liabilities_list, f, indent=2)

    with open(os.path.join(TEST_CASES_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_list, f, indent=2)

    print(f"Generated synthetic dataset with {len(TEST_CASE_SPECS)} test cases in {RAW_DIR}")

if __name__ == "__main__":
    generate_synthetic_data()
