from datetime import datetime
from typing import Dict, Any, List
from engine.schema import ExtractedData, CalculatedMetrics, AuditRecord, ReviewStatus, RiskLevel, InconsistencyEvidence
from engine.extractor import ExtractionEngine
from engine.validator import ValidatorEngine
from engine.calculator import CalculationEngine
from engine.rule_engine import RuleEngine

class AuditPipeline:
    @staticmethod
    def process_document(input_payload: Dict[str, Any]) -> AuditRecord:
        app_id = input_payload.get("applicant_id", f"APP-{datetime.now().strftime('%M%S%f')[:6]}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. EXTRACTION
        extracted_data = ExtractionEngine.extract_from_dict_or_text(input_payload, applicant_id=app_id)

        # Handle Extraction Failure Branch directly -> MANUAL_REVIEW
        if extracted_data.extraction_failed:
            return AuditRecord(
                application_id=app_id,
                applicant_name=extracted_data.applicant_name or "Unknown Applicant",
                timestamp=timestamp,
                extracted_data=extracted_data,
                calculated_metrics=CalculatedMetrics(),
                inconsistencies=[InconsistencyEvidence(
                    code="EXTRACTION_FAILURE",
                    field="raw_text",
                    severity=RiskLevel.HIGH,
                    title="Extraction / OCR Failure",
                    description=extracted_data.failure_reason or "Document text unreadable or unparseable.",
                    expected_value="Readable Document",
                    actual_value="Corrupted / OCR Failed",
                    source_document="OCR Pipeline"
                )],
                status=ReviewStatus.MANUAL_REVIEW,
                risk_level=RiskLevel.HIGH,
                routing_reason="Extraction Failure -> Routed to Manual Review Queue"
            )

        # 2. SCHEMA VALIDATION
        is_schema_valid, schema_inconsistencies = ValidatorEngine.validate_schema(extracted_data)

        # 3. NORMALIZATION (already applied inside ExtractionEngine / Normalizer)

        # 4. CALCULATION ENGINE
        metrics = CalculationEngine.calculate(extracted_data)

        # 5. RULE ENGINE
        rule_inconsistencies = RuleEngine.evaluate(extracted_data, metrics)

        # Combine Inconsistencies
        all_inconsistencies = schema_inconsistencies + rule_inconsistencies

        # 6. ROUTING DECISION
        has_high_risk = any(inc.severity == RiskLevel.HIGH for inc in all_inconsistencies)
        has_inconsistencies = len(all_inconsistencies) > 0

        if has_high_risk:
            status = ReviewStatus.FLAGGED
            risk_level = RiskLevel.HIGH
            routing_reason = "High Severity Inconsistent Evidence Chain -> Sent to Review Queue"
        elif has_inconsistencies:
            status = ReviewStatus.FLAGGED
            risk_level = RiskLevel.MEDIUM
            routing_reason = "Moderate Inconsistencies Detected -> Sent to Review Queue"
        else:
            status = ReviewStatus.APPROVED
            risk_level = RiskLevel.LOW
            routing_reason = "Passed all extraction, schema, calculation & rule engine checks"

        return AuditRecord(
            application_id=app_id,
            applicant_name=extracted_data.applicant_name or "Applicant",
            timestamp=timestamp,
            extracted_data=extracted_data,
            calculated_metrics=metrics,
            inconsistencies=all_inconsistencies,
            status=status,
            risk_level=risk_level,
            routing_reason=routing_reason
        )
