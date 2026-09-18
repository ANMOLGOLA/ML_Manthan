from typing import List
from datetime import datetime
from engine.schema import ExtractedData, CalculatedMetrics, InconsistencyEvidence, RiskLevel

class RuleEngine:
    @staticmethod
    def evaluate(data: ExtractedData, metrics: CalculatedMetrics) -> List[InconsistencyEvidence]:
        evidences: List[InconsistencyEvidence] = []

        # 1. Salary Check (Stated vs Bank Statement Average)
        if data.stated_monthly_income > 0 and metrics.average_salary > 0:
            diff = abs(data.stated_monthly_income - metrics.average_salary)
            variance_pct = (diff / data.stated_monthly_income) * 100.0

            # If stated salary is inflated by > 10%
            if data.stated_monthly_income > metrics.average_salary and variance_pct > 10.0:
                severity = RiskLevel.HIGH if variance_pct > 25.0 else RiskLevel.MEDIUM
                evidences.append(InconsistencyEvidence(
                    code="SALARY_MISMATCH_INFLATED",
                    field="stated_monthly_income",
                    severity=severity,
                    title="Stated Salary Discrepancy (Inflated)",
                    description=f"Stated income of ${data.stated_monthly_income:,.2f} is {variance_pct:.1f}% higher than verified 3-month bank average of ${metrics.average_salary:,.2f}.",
                    expected_value=f"${metrics.average_salary:,.2f} (Bank Verified)",
                    actual_value=f"${data.stated_monthly_income:,.2f} (Stated)",
                    discrepancy_variance_pct=round(variance_pct, 2),
                    source_document="Payslip / Bank Statement Cross-Check"
                ))

        # 2. EMI Check (Claimed vs Bank EMI Debits)
        if metrics.detected_existing_emi > (data.claimed_existing_emi + 50.0):
            unreported_emi = metrics.detected_existing_emi - data.claimed_existing_emi
            evidences.append(InconsistencyEvidence(
                code="UNDECLARED_EXISTING_EMI",
                field="claimed_existing_emi",
                severity=RiskLevel.HIGH,
                title="Undeclared Existing Loan EMIs",
                description=f"Detected ${metrics.detected_existing_emi:,.2f}/mo recurring EMI debits in bank statement, but applicant only declared ${data.claimed_existing_emi:,.2f}/mo.",
                expected_value=f"${metrics.detected_existing_emi:,.2f}/mo (Detected in Bank)",
                actual_value=f"${data.claimed_existing_emi:,.2f}/mo (Declared)",
                discrepancy_variance_pct=round((unreported_emi / (data.claimed_existing_emi or 1)) * 100, 2),
                source_document="Bank Statement Debit Audit"
            ))

        # DTI Ratio Risk Check
        if metrics.dti_ratio > 50.0:
            severity = RiskLevel.HIGH if metrics.dti_ratio > 65.0 else RiskLevel.MEDIUM
            evidences.append(InconsistencyEvidence(
                code="HIGH_DTI_RATIO",
                field="dti_ratio",
                severity=severity,
                title="Excessive Debt-to-Income (DTI) Ratio",
                description=f"Total monthly EMI commitments represent {metrics.dti_ratio:.1f}% of verified income (threshold: 50.0%).",
                expected_value="<= 50.0%",
                actual_value=f"{metrics.dti_ratio:.1f}%",
                discrepancy_variance_pct=round(metrics.dti_ratio - 50.0, 2),
                source_document="Calculation Engine DTI Output"
            ))

        # Negative Net Disposable Income
        if metrics.net_disposable_income < 0:
            evidences.append(InconsistencyEvidence(
                code="NEGATIVE_DISPOSABLE_INCOME",
                field="net_disposable_income",
                severity=RiskLevel.HIGH,
                title="Negative Net Disposable Income",
                description=f"After accounting for expenses and EMI commitments, net income is negative (${metrics.net_disposable_income:,.2f}).",
                expected_value="> $0.00",
                actual_value=f"${metrics.net_disposable_income:,.2f}",
                source_document="Risk Engine Cash Flow Analysis"
            ))

        # 3. Date Check (Staleness / Future Date / Mismatch)
        if data.application_date and data.statement_end_date:
            try:
                app_dt = datetime.strptime(data.application_date, "%Y-%m-%d")
                stmt_dt = datetime.strptime(data.statement_end_date, "%Y-%m-%d")
                days_diff = (app_dt - stmt_dt).days
                if days_diff > 90:
                    evidences.append(InconsistencyEvidence(
                        code="STALE_BANK_STATEMENT",
                        field="statement_end_date",
                        severity=RiskLevel.MEDIUM,
                        title="Outdated Bank Statement (>90 Days)",
                        description=f"Bank statement end date ({data.statement_end_date}) is {days_diff} days prior to application date ({data.application_date}).",
                        expected_value="Within 90 Days",
                        actual_value=f"{days_diff} Days Old",
                        source_document="Bank Statement Metadata"
                    ))
                elif days_diff < -5:
                    evidences.append(InconsistencyEvidence(
                        code="FUTURE_DATED_DOCUMENT",
                        field="statement_end_date",
                        severity=RiskLevel.HIGH,
                        title="Future-Dated Bank Statement Detected",
                        description=f"Bank statement end date ({data.statement_end_date}) is set after the application date ({data.application_date}).",
                        expected_value="<= Application Date",
                        actual_value=data.statement_end_date,
                        source_document="Document Timestamp Inspection"
                    ))
            except Exception:
                pass

        # 4. Missing Data Check (e.g. less than 3 months statement data)
        if len(data.salary_credits_3m) > 0 and len(data.salary_credits_3m) < 3:
            evidences.append(InconsistencyEvidence(
                code="INCOMPLETE_STATEMENT_HISTORY",
                field="salary_credits_3m",
                severity=RiskLevel.MEDIUM,
                title="Incomplete Bank Statement (Less than 3 Months)",
                description=f"Only {len(data.salary_credits_3m)} month(s) of bank statement credits were provided instead of the required 3 full months.",
                expected_value="3 Months",
                actual_value=f"{len(data.salary_credits_3m)} Month(s)",
                source_document="Bank Statement Parser"
            ))

        return evidences
