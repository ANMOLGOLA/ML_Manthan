# ML Feature Dictionary — PS14 LoanLens

| Feature Name | Data Type | Source Document/Calculation | Calculation / Description |
|---|---|---|---|
| `salary_difference` | `float` | Application vs. Bank Statement | `abs(declared_salary - bank_salary_average)` |
| `salary_variance_pct` | `float` | Application vs. Bank Statement | `(salary_difference / declared_salary) * 100.0` |
| `bank_salary_average` | `float` | Bank Statement | Mean of detected salary credit transactions |
| `salary_credit_count` | `float` | Bank Statement | Count of verified monthly salary credits |
| `emi_difference` | `float` | Application vs. Bank / Liability | `abs(declared_emi - bank_recurring_emi)` |
| `emi_variance_pct` | `float` | Application vs. Bank / Liability | `(emi_difference / declared_emi) * 100.0` |
| `recurring_emi_count` | `float` | Bank Statement | Count of detected recurring EMI debits |
| `employment_date_difference` | `float` | Application vs. Salary Slip | Absolute difference in days between employment start dates |
| `missing_document_count` | `float` | Intake Pipeline | Total count of required missing document files |
| `missing_field_count` | `float` | Extraction / Normalization | Total count of missing required fields |
| `extraction_failure_count` | `float` | Extraction Layer | Total count of failed field extractions |
| `low_confidence_count` | `float` | Extraction Layer | Count of fields extracted below confidence threshold |
