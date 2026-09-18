from engine.schema import ExtractedData, CalculatedMetrics

class CalculationEngine:
    @staticmethod
    def calculate(data: ExtractedData) -> CalculatedMetrics:
        # 1. Average salary
        if data.salary_credits_3m:
            avg_salary = sum(data.salary_credits_3m) / len(data.salary_credits_3m)
        else:
            avg_salary = data.stated_monthly_income or 0.0

        # 2. Recurring debits average
        if data.recurring_debits_3m:
            avg_recurring_debits = sum(data.recurring_debits_3m) / len(data.recurring_debits_3m)
        else:
            avg_recurring_debits = 0.0

        # 3. Detected existing EMI from bank debits
        if data.existing_emi_debits_3m:
            detected_emi = sum(data.existing_emi_debits_3m) / len(data.existing_emi_debits_3m)
        else:
            detected_emi = data.claimed_existing_emi or 0.0

        # Take max of claimed EMI vs detected bank EMI for conservatism
        effective_existing_emi = max(data.claimed_existing_emi or 0.0, detected_emi)

        # 4. Total EMI (Existing + Proposed)
        total_emi = effective_existing_emi + (data.proposed_monthly_emi or 0.0)

        # 5. Debt-to-Income (DTI) Ratio %
        if avg_salary > 0:
            dti = (total_emi / avg_salary) * 100.0
        else:
            dti = 100.0 if total_emi > 0 else 0.0

        # 6. Net Disposable Income
        net_disposable = avg_salary - avg_recurring_debits - total_emi

        return CalculatedMetrics(
            average_salary=round(avg_salary, 2),
            recurring_debits_avg=round(avg_recurring_debits, 2),
            detected_existing_emi=round(detected_emi, 2),
            total_emi=round(total_emi, 2),
            dti_ratio=round(dti, 2),
            net_disposable_income=round(net_disposable, 2)
        )
