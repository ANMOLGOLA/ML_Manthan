import os
import json
import pandas as pd
from PIL import Image, ImageDraw

def create_golden_cases():
    # 20 Golden Cases covering all target scenarios
    cases = [
        # 1-4: CONSISTENT CASES
        {"id": "TC001", "app_salary": 75000, "app_emi": 15000, "app_emp": "TechCorp", "slip_salary": 75000, "bank_sal": 75000, "bank_emi": 15000, "liab_emi": 15000},
        {"id": "TC002", "app_salary": 120000, "app_emi": 30000, "app_emp": "Alpha Analytics", "slip_salary": 120000, "bank_sal": 120000, "bank_emi": 30000, "liab_emi": 30000},
        {"id": "TC003", "app_salary": 50000, "app_emi": 8000, "app_emp": "Retail Hub", "slip_salary": 50000, "bank_sal": 50000, "bank_emi": 8000, "liab_emi": 8000},
        {"id": "TC004", "app_salary": 95000, "app_emi": 20000, "app_emp": "Innovate LLC", "slip_salary": 95000, "bank_sal": 95000, "bank_emi": 20000, "liab_emi": 20000},

        # 5-8: SALARY MISMATCH
        {"id": "TC005", "app_salary": 90000, "app_emi": 12000, "app_emp": "Acme Inc", "slip_salary": 90000, "bank_sal": 60000, "bank_emi": 12000, "liab_emi": 12000},
        {"id": "TC006", "app_salary": 80000, "app_emi": 10000, "app_emp": "Beta Systems", "slip_salary": 50000, "bank_sal": 50000, "bank_emi": 10000, "liab_emi": 10000},
        {"id": "TC007", "app_salary": 110000, "app_emi": 25000, "app_emp": "CloudOps", "slip_salary": 110000, "bank_sal": 70000, "bank_emi": 25000, "liab_emi": 25000},
        {"id": "TC008", "app_salary": 65000, "app_emi": 14000, "app_emp": "Apex Corp", "slip_salary": 65000, "bank_sal": 45000, "bank_emi": 14000, "liab_emi": 14000},

        # 9-12: EMI MISMATCH
        {"id": "TC009", "app_salary": 85000, "app_emi": 10000, "app_emp": "Global Logistics", "slip_salary": 85000, "bank_sal": 85000, "bank_emi": 28000, "liab_emi": 28000},
        {"id": "TC010", "app_salary": 70000, "app_emi": 5000, "app_emp": "Prime Tech", "slip_salary": 70000, "bank_sal": 70000, "bank_emi": 18000, "liab_emi": 18000},
        {"id": "TC011", "app_salary": 100000, "app_emi": 15000, "app_emp": "Data Core", "slip_salary": 100000, "bank_sal": 100000, "bank_emi": 35000, "liab_emi": 35000},
        {"id": "TC012", "app_salary": 60000, "app_emi": 7000, "app_emp": "Smart Solutions", "slip_salary": 60000, "bank_sal": 60000, "bank_emi": 22000, "liab_emi": 22000},

        # 13-15: EMPLOYMENT MISMATCH
        {"id": "TC013", "app_salary": 75000, "app_emi": 12000, "app_emp": "TechCorp", "slip_emp": "Global Logistics", "slip_salary": 75000, "bank_sal": 75000, "bank_emi": 12000, "liab_emi": 12000},
        {"id": "TC014", "app_salary": 82000, "app_emi": 16000, "app_emp": "InfoSys India", "slip_emp": "InfoSys US LLC", "slip_salary": 82000, "bank_sal": 82000, "bank_emi": 16000, "liab_emi": 16000},
        {"id": "TC015", "app_salary": 90000, "app_emi": 18000, "app_emp": "AeroSpace Ltd", "slip_emp": "Unknown Enterprise", "slip_salary": 90000, "bank_sal": 90000, "bank_emi": 18000, "liab_emi": 18000},

        # 16-18: MULTIPLE MISMATCHES
        {"id": "TC016", "app_salary": 100000, "app_emi": 15000, "app_emp": "Omni Group", "slip_salary": 100000, "bank_sal": 55000, "bank_emi": 32000, "liab_emi": 32000},
        {"id": "TC017", "app_salary": 85000, "app_emi": 10000, "app_emp": "Nexus Media", "slip_salary": 85000, "bank_sal": 45000, "bank_emi": 25000, "liab_emi": 25000},
        {"id": "TC018", "app_salary": 120000, "app_emi": 20000, "app_emp": "Vertex Labs", "slip_salary": 120000, "bank_sal": 80000, "bank_emi": 40000, "liab_emi": 40000},

        # 19-20: DATA QUALITY / EXTRACTION ISSUE
        {"id": "TC019", "app_salary": 70000, "app_emi": 11000, "app_emp": "FinTech Corp", "slip_salary": 0, "bank_sal": 70000, "bank_emi": 11000, "liab_emi": 11000},
        {"id": "TC020", "app_salary": 65000, "app_emi": 9000, "app_emp": "Urban Retail", "slip_salary": 65000, "bank_sal": 0, "bank_emi": 0, "liab_emi": 9000}
    ]

    for c in cases:
        path = f"data/raw/cases/{c['id']}"
        os.makedirs(path, exist_ok=True)

        # 1. Application JSON
        with open(f"{path}/application.json", "w") as f:
            json.dump({
                "applicant_id": c["id"],
                "declared_monthly_income": c["app_salary"],
                "declared_emi": c["app_emi"],
                "employer_name": c["app_emp"],
                "employment_start_date": "2021-06-15"
            }, f, indent=2)

        # 2. Salary Slip Image PNG
        slip_employer = c.get("slip_emp", c["app_emp"])
        img = Image.new('RGB', (500, 300), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((20, 30), f"Employer: {slip_employer}", fill=(0,0,0))
        d.text((20, 70), f"Net Salary: ${c['slip_salary']}", fill=(0,0,0))
        img.save(f"{path}/salary_slip.png")

        # 3. Bank Statement CSV
        txns = []
        if c["bank_sal"] > 0:
            txns.append({"date": "2026-08-01", "description": "SALARY CREDIT", "amount": c["bank_sal"], "type": "CREDIT"})
        if c["bank_emi"] > 0:
            txns.append({"date": "2026-08-05", "description": "EMI DEBIT", "amount": c["bank_emi"], "type": "DEBIT"})
        
        pd.DataFrame(txns if txns else [{"date": "2026-08-01", "description": "FEE", "amount": 10, "type": "DEBIT"}]).to_csv(f"{path}/bank_statement.csv", index=False)

        # 4. Liability JSON
        with open(f"{path}/liability.json", "w") as f:
            json.dump({"total_monthly_obligation": c["liab_emi"], "active_loans": 1}, f, indent=2)

    print("20 Golden Test Cases successfully generated under 'data/raw/cases/'!")

if __name__ == "__main__":
    create_golden_cases()