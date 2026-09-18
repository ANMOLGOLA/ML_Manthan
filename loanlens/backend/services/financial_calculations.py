import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from backend.models import (
    LoanApplication, SalarySlip, BankTransaction, Liability
)

class TraceabilityInfo(BaseModel):
    calculation_name: str
    source_documents: List[str] = Field(default_factory=list)
    source_fields: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    input_values: Dict[str, Any] = Field(default_factory=dict)
    calculated_value: Any = None

class SalaryMetrics(BaseModel):
    count: int = 0
    total: float = 0.0
    average: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    std_dev: Optional[float] = None
    status: str = "INSUFFICIENT_DATA"
    traceability: Optional[TraceabilityInfo] = None

class EMIMetrics(BaseModel):
    count: int = 0
    total: float = 0.0
    average: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    status: str = "INSUFFICIENT_DATA"
    traceability: Optional[TraceabilityInfo] = None

class EmploymentMetrics(BaseModel):
    app_date: Optional[str] = None
    slip_date: Optional[str] = None
    diff_days: Optional[int] = None
    status: str = "MISSING_DATES"
    traceability: Optional[TraceabilityInfo] = None

class ComparisonMetrics(BaseModel):
    declared_vs_salary_slip_difference: Optional[float] = None
    declared_vs_salary_slip_diff_pct: Optional[float] = None
    
    declared_vs_bank_salary_difference: Optional[float] = None
    declared_vs_bank_salary_diff_pct: Optional[float] = None
    
    salary_slip_vs_bank_salary_difference: Optional[float] = None
    salary_slip_vs_bank_salary_diff_pct: Optional[float] = None

    declared_vs_liability_emi_difference: Optional[float] = None
    declared_vs_liability_emi_diff_pct: Optional[float] = None
    
    declared_vs_bank_emi_difference: Optional[float] = None
    declared_vs_bank_emi_diff_pct: Optional[float] = None
    
    liability_vs_bank_emi_difference: Optional[float] = None
    liability_vs_bank_emi_diff_pct: Optional[float] = None
    
    traceability: List[TraceabilityInfo] = Field(default_factory=list)

class FinancialCalculationResult(BaseModel):
    salary_metrics: SalaryMetrics
    emi_metrics: EMIMetrics
    employment_metrics: EmploymentMetrics
    comparison_metrics: ComparisonMetrics
    calculation_status: str = "SUCCESS"
    warnings: List[str] = Field(default_factory=list)

class FinancialCalculator:
    """Calculates financial metrics, averages, standard deviations, and cross-document comparisons."""

    @staticmethod
    def _safe_pct_diff(val1: Optional[float], val2: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
        if val1 is None or val2 is None:
            return None, None
        abs_diff = round(abs(val1 - val2), 2)
        if val1 == 0:
            return abs_diff, None
        pct_diff = round((abs_diff / abs(val1)) * 100.0, 2)
        return abs_diff, pct_diff

    @staticmethod
    def calculate_salary_metrics(bank_txs: Optional[List[BankTransaction]]) -> SalaryMetrics:
        if bank_txs is None:
            return SalaryMetrics(count=0, total=0.0, status="MISSING_BANK_STATEMENT")
            
        sal_txs = [tx for tx in bank_txs if tx.is_salary or (tx.transaction_type == "CREDIT" and "SALARY" in tx.description.upper())]
        sal_credits = [abs(tx.amount) for tx in sal_txs]
        sal_ids = [tx.transaction_id for tx in sal_txs]

        if not sal_credits:
            return SalaryMetrics(
                count=0, total=0.0, status="NO_SALARY_CREDITS_FOUND",
                traceability=TraceabilityInfo(
                    calculation_name="salary_metrics",
                    source_documents=["bank_statement"],
                    source_fields=["transaction_type", "description", "amount"],
                    transaction_ids=[],
                    input_values={"sal_credits": []},
                    calculated_value=None
                )
            )

        total = sum(sal_credits)
        avg = float(np.mean(sal_credits))
        min_v = float(np.min(sal_credits))
        max_v = float(np.max(sal_credits))
        std_v = float(np.std(sal_credits)) if len(sal_credits) >= 2 else 0.0

        res_avg = round(avg, 2)
        return SalaryMetrics(
            count=len(sal_credits),
            total=round(total, 2),
            average=res_avg,
            min_val=round(min_v, 2),
            max_val=round(max_v, 2),
            std_dev=round(std_v, 2),
            status="SUCCESS",
            traceability=TraceabilityInfo(
                calculation_name="salary_metrics",
                source_documents=["bank_statement"],
                source_fields=["amount"],
                transaction_ids=sal_ids,
                input_values={"sal_credits": sal_credits},
                calculated_value=res_avg
            )
        )

    @staticmethod
    def calculate_emi_metrics(bank_txs: Optional[List[BankTransaction]], liabilities: Optional[List[Liability]]) -> EMIMetrics:
        if bank_txs is None and liabilities is None:
            return EMIMetrics(count=0, total=0.0, status="MISSING_BANK_AND_LIABILITY_DATA")
            
        bank_tx_list = bank_txs or []
        emi_txs = [tx for tx in bank_tx_list if tx.is_recurring_debit or (tx.transaction_type == "DEBIT" and "EMI" in tx.description.upper())]
        bank_emis = [abs(tx.amount) for tx in emi_txs]
        emi_ids = [tx.transaction_id for tx in emi_txs]

        liab_list = liabilities or []
        bureau_emis = [l.monthly_emi for l in liab_list if l.monthly_emi > 0]

        all_emis = bank_emis if bank_emis else bureau_emis
        source_docs = ["bank_statement"] if bank_emis else (["liability_report"] if bureau_emis else [])

        if not all_emis:
            return EMIMetrics(
                count=0, total=0.0, status="NO_RECURRING_EMI_FOUND",
                traceability=TraceabilityInfo(
                    calculation_name="emi_metrics",
                    source_documents=source_docs,
                    source_fields=["amount", "monthly_emi"],
                    transaction_ids=[],
                    input_values={"emis": []},
                    calculated_value=None
                )
            )

        total = sum(all_emis)
        avg = float(np.mean(all_emis))
        min_v = float(np.min(all_emis))
        max_v = float(np.max(all_emis))

        res_avg = round(avg, 2)
        return EMIMetrics(
            count=len(all_emis),
            total=round(total, 2),
            average=res_avg,
            min_val=round(min_v, 2),
            max_val=round(max_v, 2),
            status="SUCCESS",
            traceability=TraceabilityInfo(
                calculation_name="emi_metrics",
                source_documents=source_docs,
                source_fields=["amount", "monthly_emi"],
                transaction_ids=emi_ids,
                input_values={"all_emis": all_emis},
                calculated_value=res_avg
            )
        )

    @staticmethod
    def calculate_employment_metrics(app_start: Optional[str], slip_start: Optional[str]) -> EmploymentMetrics:
        if not app_start or not slip_start:
            return EmploymentMetrics(
                app_date=app_start, slip_date=slip_start, status="MISSING_EMPLOYMENT_DATES",
                traceability=TraceabilityInfo(
                    calculation_name="employment_metrics",
                    source_documents=["loan_application", "salary_slip"],
                    source_fields=["employment_start_date"],
                    input_values={"app_start": app_start, "slip_start": slip_start},
                    calculated_value=None
                )
            )

        try:
            d1 = datetime.strptime(app_start, "%Y-%m-%d")
            d2 = datetime.strptime(slip_start, "%Y-%m-%d")
            diff = abs((d1 - d2).days)
            return EmploymentMetrics(
                app_date=app_start,
                slip_date=slip_start,
                diff_days=diff,
                status="SUCCESS" if diff == 0 else "DATE_MISMATCH",
                traceability=TraceabilityInfo(
                    calculation_name="employment_metrics",
                    source_documents=["loan_application", "salary_slip"],
                    source_fields=["employment_start_date"],
                    input_values={"app_start": app_start, "slip_start": slip_start},
                    calculated_value=diff
                )
            )
        except ValueError:
            return EmploymentMetrics(
                app_date=app_start, slip_date=slip_start, status="INVALID_DATE_FORMAT",
                traceability=TraceabilityInfo(
                    calculation_name="employment_metrics",
                    source_documents=["loan_application", "salary_slip"],
                    source_fields=["employment_start_date"],
                    input_values={"app_start": app_start, "slip_start": slip_start},
                    calculated_value=None
                )
            )

    @staticmethod
    def process(
        application: Optional[LoanApplication],
        salary_slip: Optional[SalarySlip],
        bank_txs: Optional[List[BankTransaction]],
        liabilities: Optional[List[Liability]]
    ) -> FinancialCalculationResult:
        warnings = []

        # 1. Salary Metrics
        sal_metrics = FinancialCalculator.calculate_salary_metrics(bank_txs)
        if sal_metrics.status != "SUCCESS":
            warnings.append(f"Salary Metrics Warning: {sal_metrics.status}")

        # 2. EMI Metrics
        emi_metrics = FinancialCalculator.calculate_emi_metrics(bank_txs, liabilities)
        if emi_metrics.status != "SUCCESS":
            warnings.append(f"EMI Metrics Warning: {emi_metrics.status}")

        # 3. Employment Metrics
        slip_emp_date = str(salary_slip.pay_period_end) if (salary_slip and salary_slip.pay_period_end) else None
        app_emp_date = None
        if application and hasattr(application, 'employment_start_date'):
            app_emp_date = str(getattr(application, 'employment_start_date'))
        emp_metrics = FinancialCalculator.calculate_employment_metrics(app_emp_date, slip_emp_date)

        # 4. Cross-Document Comparisons
        declared_sal = application.declared_monthly_salary if application else None
        slip_sal = salary_slip.net_pay if salary_slip else None
        bank_sal = sal_metrics.average

        decl_vs_slip_diff, decl_vs_slip_pct = FinancialCalculator._safe_pct_diff(declared_sal, slip_sal)
        decl_vs_bank_diff, decl_vs_bank_pct = FinancialCalculator._safe_pct_diff(declared_sal, bank_sal)
        slip_vs_bank_diff, slip_vs_bank_pct = FinancialCalculator._safe_pct_diff(slip_sal, bank_sal)

        declared_emi = application.declared_existing_emi if application else None
        liability_emi = sum(l.monthly_emi for l in liabilities) if liabilities else (0.0 if liabilities is not None else None)
        bank_emi = emi_metrics.total if emi_metrics.status == "SUCCESS" else None

        decl_vs_liab_diff, decl_vs_liab_pct = FinancialCalculator._safe_pct_diff(declared_emi, liability_emi)
        decl_vs_bank_emi_diff, decl_vs_bank_emi_pct = FinancialCalculator._safe_pct_diff(declared_emi, bank_emi)
        liab_vs_bank_emi_diff, liab_vs_bank_emi_pct = FinancialCalculator._safe_pct_diff(liability_emi, bank_emi)

        traces = []
        if decl_vs_slip_diff is not None:
            traces.append(TraceabilityInfo(
                calculation_name="declared_vs_salary_slip_difference",
                source_documents=["loan_application", "salary_slip"],
                source_fields=["declared_monthly_salary", "net_pay"],
                input_values={"declared": declared_sal, "salary_slip": slip_sal},
                calculated_value=decl_vs_slip_diff
            ))

        comp_metrics = ComparisonMetrics(
            declared_vs_salary_slip_difference=decl_vs_slip_diff,
            declared_vs_salary_slip_diff_pct=decl_vs_slip_pct,
            declared_vs_bank_salary_difference=decl_vs_bank_diff,
            declared_vs_bank_salary_diff_pct=decl_vs_bank_pct,
            salary_slip_vs_bank_salary_difference=slip_vs_bank_diff,
            salary_slip_vs_bank_salary_diff_pct=slip_vs_bank_pct,
            declared_vs_liability_emi_difference=decl_vs_liab_diff,
            declared_vs_liability_emi_diff_pct=decl_vs_liab_pct,
            declared_vs_bank_emi_difference=decl_vs_bank_emi_diff,
            declared_vs_bank_emi_diff_pct=decl_vs_bank_emi_pct,
            liability_vs_bank_emi_difference=liab_vs_bank_emi_diff,
            liability_vs_bank_emi_diff_pct=liab_vs_bank_emi_pct,
            traceability=traces
        )

        calc_status = "SUCCESS" if not warnings else "PARTIAL_SUCCESS"

        return FinancialCalculationResult(
            salary_metrics=sal_metrics,
            emi_metrics=emi_metrics,
            employment_metrics=emp_metrics,
            comparison_metrics=comp_metrics,
            calculation_status=calc_status,
            warnings=warnings
        )

