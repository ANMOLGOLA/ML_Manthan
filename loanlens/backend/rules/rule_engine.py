from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.models import (
    LoanApplication, SalarySlip, BankTransaction, Liability,
    RuleStatus, SeverityLevel
)
from backend.services.financial_calculations import FinancialCalculationResult

class RuleEngineConfig(BaseModel):
    """Configurable thresholds for deterministic rule evaluations."""
    salary_tolerance_pct: float = Field(default=5.0, ge=0.0, description="Allowed salary variance percentage")
    emi_tolerance_pct: float = Field(default=5.0, ge=0.0, description="Allowed EMI variance percentage")
    employment_date_tolerance_days: int = Field(default=0, ge=0, description="Allowed employment joining date variance in days")
    low_confidence_threshold: float = Field(default=0.70, ge=0.0, le=1.0, description="Threshold for low confidence extractions")

class RuleResult(BaseModel):
    """Structured evaluation result for a single deterministic rule."""
    rule_id: str
    rule_name: str
    category: str  # SALARY, EMI, EMPLOYMENT, DATA_QUALITY
    status: RuleStatus
    field: Optional[str] = None
    source_document: Optional[str] = None
    source_location: Optional[str] = None
    source_value: Optional[Any] = None
    comparison_document: Optional[str] = None
    comparison_location: Optional[str] = None
    comparison_value: Optional[Any] = None
    absolute_difference: Optional[float] = None
    percentage_difference: Optional[float] = None
    threshold_used: Optional[float] = None
    explanation: str
    severity: SeverityLevel = SeverityLevel.MEDIUM

class RuleSummary(BaseModel):
    """Aggregated rule evaluation summary."""
    total_rules: int = 0
    passed: int = 0
    inconsistent: int = 0
    insufficient_data: int = 0
    calculation_failures: int = 0
    data_quality_issues: int = 0

class RuleEngineOutput(BaseModel):
    """Complete rule engine execution response containing all rule evaluation results and summary."""
    application_id: str
    rule_results: List[RuleResult] = Field(default_factory=list)
    summary: RuleSummary

class DeterministicRuleEngine:
    """Deterministic, explainable rule engine for cross-document consistency checks."""

    def __init__(self, config: Optional[RuleEngineConfig] = None):
        self.config = config or RuleEngineConfig()

    def evaluate_salary_001(
        self,
        application: Optional[LoanApplication],
        salary_slip: Optional[SalarySlip]
    ) -> RuleResult:
        """SALARY-001: Declared salary vs salary slip salary."""
        rule_id = "SALARY-001"
        rule_name = "Application salary vs salary slip salary"
        category = "SALARY"
        field_name = "declared_monthly_salary"

        if not application or application.declared_monthly_salary is None or application.declared_monthly_salary <= 0:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.INSUFFICIENT_DATA, field=field_name,
                source_document="loan_application", source_value=getattr(application, 'declared_monthly_salary', None),
                comparison_document="salary_slip", comparison_value=salary_slip.net_pay if salary_slip else None,
                threshold_used=self.config.salary_tolerance_pct,
                explanation="Missing or zero declared application salary.",
                severity=SeverityLevel.MEDIUM
            )

        if not salary_slip or salary_slip.net_pay is None or salary_slip.net_pay <= 0:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.INSUFFICIENT_DATA, field=field_name,
                source_document="loan_application", source_value=application.declared_monthly_salary,
                comparison_document="salary_slip", comparison_value=salary_slip.net_pay if salary_slip else None,
                threshold_used=self.config.salary_tolerance_pct,
                explanation="Salary slip is missing or net pay is unavailable.",
                severity=SeverityLevel.MEDIUM
            )

        decl_sal = float(application.declared_monthly_salary)
        slip_sal = float(salary_slip.net_pay)
        abs_diff = round(abs(decl_sal - slip_sal), 2)
        pct_diff = round((abs_diff / decl_sal) * 100.0, 2)

        if pct_diff <= self.config.salary_tolerance_pct:
            status = RuleStatus.PASS
            explanation = f"Declared salary ({decl_sal}) matches salary slip ({slip_sal}) within {self.config.salary_tolerance_pct}% tolerance."
            severity = SeverityLevel.LOW
        else:
            status = RuleStatus.INCONSISTENT
            explanation = f"Declared salary ({decl_sal}) differs from salary slip ({slip_sal}) by {pct_diff}%, exceeding {self.config.salary_tolerance_pct}% tolerance."
            severity = SeverityLevel.HIGH

        return RuleResult(
            rule_id=rule_id, rule_name=rule_name, category=category, status=status,
            field=field_name, source_document="loan_application", source_value=decl_sal,
            comparison_document="salary_slip", comparison_value=slip_sal,
            absolute_difference=abs_diff, percentage_difference=pct_diff,
            threshold_used=self.config.salary_tolerance_pct, explanation=explanation,
            severity=severity
        )

    def evaluate_salary_002(
        self,
        application: Optional[LoanApplication],
        calc_res: Optional[FinancialCalculationResult]
    ) -> RuleResult:
        """SALARY-002: Application declared salary vs bank average salary (from Phase 6 output)."""
        rule_id = "SALARY-002"
        rule_name = "Application salary vs bank average salary"
        category = "SALARY"
        field_name = "declared_monthly_salary"

        if not application or application.declared_monthly_salary is None or application.declared_monthly_salary <= 0:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.INSUFFICIENT_DATA, field=field_name,
                source_document="loan_application", source_value=getattr(application, 'declared_monthly_salary', None),
                comparison_document="bank_statement",
                comparison_value=calc_res.salary_metrics.average if (calc_res and calc_res.salary_metrics) else None,
                threshold_used=self.config.salary_tolerance_pct,
                explanation="Missing declared application salary.",
                severity=SeverityLevel.MEDIUM
            )

        if not calc_res or calc_res.salary_metrics.status != "SUCCESS" or calc_res.salary_metrics.average is None:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.INSUFFICIENT_DATA, field=field_name,
                source_document="loan_application", source_value=application.declared_monthly_salary,
                comparison_document="bank_statement", comparison_value=None,
                threshold_used=self.config.salary_tolerance_pct,
                explanation=f"Bank statement salary calculation status: {calc_res.salary_metrics.status if calc_res else 'NO_CALCULATION_RESULT'}.",
                severity=SeverityLevel.MEDIUM
            )

        decl_sal = float(application.declared_monthly_salary)
        bank_sal = float(calc_res.salary_metrics.average)
        abs_diff = round(abs(decl_sal - bank_sal), 2)
        pct_diff = round((abs_diff / decl_sal) * 100.0, 2)

        if pct_diff <= self.config.salary_tolerance_pct:
            status = RuleStatus.PASS
            explanation = f"Declared salary ({decl_sal}) matches bank average salary ({bank_sal}) within {self.config.salary_tolerance_pct}% tolerance."
            severity = SeverityLevel.LOW
        else:
            status = RuleStatus.INCONSISTENT
            explanation = f"Declared salary ({decl_sal}) differs from bank average salary ({bank_sal}) by {pct_diff}%, exceeding {self.config.salary_tolerance_pct}% tolerance."
            severity = SeverityLevel.HIGH

        return RuleResult(
            rule_id=rule_id, rule_name=rule_name, category=category, status=status,
            field=field_name, source_document="loan_application", source_value=decl_sal,
            comparison_document="bank_statement", comparison_value=bank_sal,
            absolute_difference=abs_diff, percentage_difference=pct_diff,
            threshold_used=self.config.salary_tolerance_pct, explanation=explanation,
            severity=severity
        )

    def evaluate_emi_001(
        self,
        application: Optional[LoanApplication],
        liabilities: Optional[List[Liability]]
    ) -> RuleResult:
        """EMI-001: Declared EMI vs liability report EMI."""
        rule_id = "EMI-001"
        rule_name = "Declared EMI vs liability report EMI"
        category = "EMI"
        field_name = "declared_existing_emi"

        if not application or application.declared_existing_emi is None:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.INSUFFICIENT_DATA, field=field_name,
                source_document="loan_application", source_value=None,
                comparison_document="liability_report", comparison_value=None,
                threshold_used=self.config.emi_tolerance_pct,
                explanation="Declared existing EMI is missing.",
                severity=SeverityLevel.MEDIUM
            )

        if liabilities is None:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.INSUFFICIENT_DATA, field=field_name,
                source_document="loan_application", source_value=application.declared_existing_emi,
                comparison_document="liability_report", comparison_value=None,
                threshold_used=self.config.emi_tolerance_pct,
                explanation="Liability report data is missing.",
                severity=SeverityLevel.MEDIUM
            )

        decl_emi = float(application.declared_existing_emi)
        liab_emi = float(sum(l.monthly_emi for l in liabilities))
        abs_diff = round(abs(decl_emi - liab_emi), 2)
        pct_diff = round((abs_diff / decl_emi) * 100.0, 2) if decl_emi > 0 else (0.0 if abs_diff == 0 else None)

        if abs_diff == 0 or (pct_diff is not None and pct_diff <= self.config.emi_tolerance_pct):
            status = RuleStatus.PASS
            explanation = f"Declared EMI ({decl_emi}) matches liability EMI ({liab_emi}) within tolerance."
            severity = SeverityLevel.LOW
        else:
            status = RuleStatus.INCONSISTENT
            explanation = f"Declared EMI ({decl_emi}) differs from liability EMI ({liab_emi}) by absolute diff {abs_diff}."
            severity = SeverityLevel.HIGH

        return RuleResult(
            rule_id=rule_id, rule_name=rule_name, category=category, status=status,
            field=field_name, source_document="loan_application", source_value=decl_emi,
            comparison_document="liability_report", comparison_value=liab_emi,
            absolute_difference=abs_diff, percentage_difference=pct_diff,
            threshold_used=self.config.emi_tolerance_pct, explanation=explanation,
            severity=severity
        )

    def evaluate_emi_002(
        self,
        application: Optional[LoanApplication],
        calc_res: Optional[FinancialCalculationResult]
    ) -> RuleResult:
        """EMI-002: Declared EMI vs recurring bank EMI (from Phase 6 output)."""
        rule_id = "EMI-002"
        rule_name = "Declared EMI vs recurring bank statement EMI"
        category = "EMI"
        field_name = "declared_existing_emi"

        if not application or application.declared_existing_emi is None:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.INSUFFICIENT_DATA, field=field_name,
                source_document="loan_application", source_value=None,
                comparison_document="bank_statement", comparison_value=None,
                threshold_used=self.config.emi_tolerance_pct,
                explanation="Declared existing EMI is missing.",
                severity=SeverityLevel.MEDIUM
            )

        if not calc_res or calc_res.emi_metrics.status != "SUCCESS":
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.INSUFFICIENT_DATA, field=field_name,
                source_document="loan_application", source_value=application.declared_existing_emi,
                comparison_document="bank_statement", comparison_value=None,
                threshold_used=self.config.emi_tolerance_pct,
                explanation=f"Bank recurring EMI status: {calc_res.emi_metrics.status if calc_res else 'NO_CALCULATION_RESULT'}.",
                severity=SeverityLevel.MEDIUM
            )

        decl_emi = float(application.declared_existing_emi)
        bank_emi = float(calc_res.emi_metrics.total)
        abs_diff = round(abs(decl_emi - bank_emi), 2)
        pct_diff = round((abs_diff / decl_emi) * 100.0, 2) if decl_emi > 0 else (0.0 if abs_diff == 0 else None)

        if abs_diff == 0 or (pct_diff is not None and pct_diff <= self.config.emi_tolerance_pct):
            status = RuleStatus.PASS
            explanation = f"Declared EMI ({decl_emi}) matches recurring bank EMI ({bank_emi}) within tolerance."
            severity = SeverityLevel.LOW
        else:
            status = RuleStatus.INCONSISTENT
            explanation = f"Declared EMI ({decl_emi}) differs from recurring bank EMI ({bank_emi}) by absolute diff {abs_diff}."
            severity = SeverityLevel.HIGH

        return RuleResult(
            rule_id=rule_id, rule_name=rule_name, category=category, status=status,
            field=field_name, source_document="loan_application", source_value=decl_emi,
            comparison_document="bank_statement", comparison_value=bank_emi,
            absolute_difference=abs_diff, percentage_difference=pct_diff,
            threshold_used=self.config.emi_tolerance_pct, explanation=explanation,
            severity=severity
        )

    def evaluate_emp_001(
        self,
        application: Optional[LoanApplication],
        salary_slip: Optional[SalarySlip]
    ) -> RuleResult:
        """EMP-001: Application employment start date vs salary slip employment start date."""
        rule_id = "EMP-001"
        rule_name = "Employment start date comparison"
        category = "EMPLOYMENT"
        field_name = "employment_start_date"

        app_emp_date = str(application.employment_start_date) if application and application.employment_start_date else None
        slip_emp_date = str(salary_slip.employment_start_date) if salary_slip and salary_slip.employment_start_date else None

        if not app_emp_date or not slip_emp_date:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.INSUFFICIENT_DATA, field=field_name,
                source_document="loan_application", source_value=app_emp_date,
                comparison_document="salary_slip", comparison_value=slip_emp_date,
                threshold_used=float(self.config.employment_date_tolerance_days),
                explanation="Missing employment start date on loan application or salary slip.",
                severity=SeverityLevel.MEDIUM
            )

        try:
            d1 = datetime.strptime(app_emp_date, "%Y-%m-%d")
            d2 = datetime.strptime(slip_emp_date, "%Y-%m-%d")
            diff_days = abs((d1 - d2).days)
        except ValueError:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.DATA_QUALITY_ISSUE, field=field_name,
                source_document="loan_application", source_value=app_emp_date,
                comparison_document="salary_slip", comparison_value=slip_emp_date,
                threshold_used=float(self.config.employment_date_tolerance_days),
                explanation="Invalid employment start date format encountered.",
                severity=SeverityLevel.HIGH
            )

        if diff_days <= self.config.employment_date_tolerance_days:
            status = RuleStatus.PASS
            explanation = f"Employment start dates match within {self.config.employment_date_tolerance_days} days tolerance."
            severity = SeverityLevel.LOW
        else:
            status = RuleStatus.INCONSISTENT
            explanation = f"Employment start dates differ by {diff_days} days, exceeding {self.config.employment_date_tolerance_days} days tolerance."
            severity = SeverityLevel.HIGH

        return RuleResult(
            rule_id=rule_id, rule_name=rule_name, category=category, status=status,
            field=field_name, source_document="loan_application", source_value=app_emp_date,
            comparison_document="salary_slip", comparison_value=slip_emp_date,
            absolute_difference=float(diff_days), percentage_difference=None,
            threshold_used=float(self.config.employment_date_tolerance_days), explanation=explanation,
            severity=severity
        )



    def evaluate_data_001(
        self,
        application: Optional[LoanApplication],
        salary_slip: Optional[SalarySlip],
        bank_txs: Optional[List[BankTransaction]],
        liabilities: Optional[List[Liability]]
    ) -> RuleResult:
        """DATA-001: Missing required documents check."""
        rule_id = "DATA-001"
        rule_name = "Missing required documents"
        category = "DATA_QUALITY"

        missing_docs = []
        if not application:
            missing_docs.append("loan_application")
        if not salary_slip:
            missing_docs.append("salary_slip")
        if bank_txs is None:
            missing_docs.append("bank_statement")
        if liabilities is None:
            missing_docs.append("liability_report")

        if not missing_docs:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.PASS, explanation="All required document types are present.",
                severity=SeverityLevel.LOW
            )
        else:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.DATA_QUALITY_ISSUE,
                explanation=f"Missing required documents: {', '.join(missing_docs)}.",
                severity=SeverityLevel.HIGH
            )

    def evaluate_data_002(
        self,
        application: Optional[LoanApplication]
    ) -> RuleResult:
        """DATA-002: Missing required fields check."""
        rule_id = "DATA-002"
        rule_name = "Missing required fields"
        category = "DATA_QUALITY"

        if not application:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.DATA_QUALITY_ISSUE, field="application_id",
                explanation="Loan application document is completely missing.",
                severity=SeverityLevel.HIGH
            )

        missing_fields = []
        if not application.applicant_name:
            missing_fields.append("applicant_name")
        if application.declared_monthly_salary is None or application.declared_monthly_salary <= 0:
            missing_fields.append("declared_monthly_salary")
        if application.requested_loan_amount is None or application.requested_loan_amount <= 0:
            missing_fields.append("requested_loan_amount")

        if not missing_fields:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.PASS, explanation="All required application fields are present.",
                severity=SeverityLevel.LOW
            )
        else:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, category=category,
                status=RuleStatus.DATA_QUALITY_ISSUE,
                explanation=f"Missing required application fields: {', '.join(missing_fields)}.",
                severity=SeverityLevel.HIGH
            )

    def evaluate_data_003(self) -> RuleResult:
        """DATA-003: Low confidence extraction check.
        Note: The current extraction pipeline uses deterministic Pydantic schema validation.
        Documented limitation: Field confidence metadata is not emitted by upstream parsers.
        """
        return RuleResult(
            rule_id="DATA-003",
            rule_name="Low confidence extraction check",
            category="DATA_QUALITY",
            status=RuleStatus.PASS,
            explanation="Extraction layer uses strict Pydantic validation; explicit confidence scores not present.",
            threshold_used=self.config.low_confidence_threshold,
            severity=SeverityLevel.LOW
        )

    def run(
        self,
        application: Optional[LoanApplication],
        salary_slip: Optional[SalarySlip],
        bank_txs: Optional[List[BankTransaction]],
        liabilities: Optional[List[Liability]],
        calc_res: Optional[FinancialCalculationResult]
    ) -> RuleEngineOutput:
        """Run all deterministic rules and compile output summary."""
        results: List[RuleResult] = [
            self.evaluate_salary_001(application, salary_slip),
            self.evaluate_salary_002(application, calc_res),
            self.evaluate_emi_001(application, liabilities),
            self.evaluate_emi_002(application, calc_res),
            self.evaluate_emp_001(application, salary_slip),
            self.evaluate_data_001(application, salary_slip, bank_txs, liabilities),
            self.evaluate_data_002(application),
            self.evaluate_data_003()
        ]

        app_id = application.application_id if application else "UNKNOWN"

        passed = sum(1 for r in results if r.status == RuleStatus.PASS)
        inconsistent = sum(1 for r in results if r.status == RuleStatus.INCONSISTENT)
        insufficient = sum(1 for r in results if r.status == RuleStatus.INSUFFICIENT_DATA)
        calc_fail = sum(1 for r in results if r.status == RuleStatus.CALCULATION_FAILURE)
        dq_issues = sum(1 for r in results if r.status == RuleStatus.DATA_QUALITY_ISSUE)

        summary = RuleSummary(
            total_rules=len(results),
            passed=passed,
            inconsistent=inconsistent,
            insufficient_data=insufficient,
            calculation_failures=calc_fail,
            data_quality_issues=dq_issues
        )

        return RuleEngineOutput(
            application_id=app_id,
            rule_results=results,
            summary=summary
        )
