import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

FEATURE_NAMES = [
    "salary_difference",
    "salary_variance_pct",
    "bank_salary_average",
    "salary_credit_count",
    "emi_difference",
    "emi_variance_pct",
    "recurring_emi_count",
    "employment_date_difference",
    "missing_document_count",
    "missing_field_count",
    "extraction_failure_count",
    "low_confidence_count"
]

def extract_features(raw_data: Dict[str, Any]) -> Dict[str, float]:
    """Extracts ML features from normalized document inputs / calculation metrics.
    
    Guarantees safe type casting, missing value handling, and zero-division protection.
    """
    decl_sal = float(raw_data.get("declared_salary") or 0.0)
    slip_sal = float(raw_data.get("salary_slip_salary") or decl_sal)
    bank_sal = float(raw_data.get("bank_salary_average") or 0.0)
    sal_cnt = int(raw_data.get("salary_credit_count") or 0)

    decl_emi = float(raw_data.get("declared_emi") or 0.0)
    liab_emi = float(raw_data.get("liability_emi") or 0.0)
    bank_emi = float(raw_data.get("bank_recurring_emi") or liab_emi)
    emi_cnt = int(raw_data.get("recurring_emi_count") or 0)

    emp_diff = int(raw_data.get("employment_date_difference") or 0)

    missing_docs = int(raw_data.get("missing_document_count") or 0)
    missing_fields = int(raw_data.get("missing_field_count") or 0)
    ext_failures = int(raw_data.get("extraction_failure_count") or 0)
    low_conf = int(raw_data.get("low_confidence_count") or 0)

    # Derived salary metrics
    effective_bank_sal = bank_sal if bank_sal > 0 else slip_sal
    sal_diff = round(abs(decl_sal - effective_bank_sal), 2)
    sal_var_pct = round((sal_diff / decl_sal) * 100.0, 2) if decl_sal > 0 else 0.0

    # Derived EMI metrics
    effective_bank_emi = bank_emi if emi_cnt > 0 else liab_emi
    emi_diff = round(abs(decl_emi - effective_bank_emi), 2)
    emi_var_pct = round((emi_diff / decl_emi) * 100.0, 2) if decl_emi > 0 else (0.0 if emi_diff == 0 else 100.0)

    return {
        "salary_difference": sal_diff,
        "salary_variance_pct": sal_var_pct,
        "bank_salary_average": bank_sal,
        "salary_credit_count": float(sal_cnt),
        "emi_difference": emi_diff,
        "emi_variance_pct": emi_var_pct,
        "recurring_emi_count": float(emi_cnt),
        "employment_date_difference": float(emp_diff),
        "missing_document_count": float(missing_docs),
        "missing_field_count": float(missing_fields),
        "extraction_failure_count": float(ext_failures),
        "low_confidence_count": float(low_conf)
    }

def build_feature_vector(raw_data: Dict[str, Any]) -> List[float]:
    """Returns feature vector ordered strictly according to FEATURE_NAMES list."""
    feats = extract_features(raw_data)
    return [feats[name] for name in FEATURE_NAMES]
