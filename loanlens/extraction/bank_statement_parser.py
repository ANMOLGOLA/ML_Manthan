import csv
import os
from typing import List, Dict, Any, Tuple
from backend.models import BankTransaction, DocumentType, ExtractedField, ExtractionStatus
from extraction.base_extractor import BaseExtractor

class BankStatementParser(BaseExtractor):
    """Deterministic parser for bank statement CSV transaction data."""

    @staticmethod
    def parse_csv(file_path: str) -> Tuple[List[BankTransaction], List[ExtractedField]]:
        transactions: List[BankTransaction] = []
        fields: List[ExtractedField] = []
        doc_type = DocumentType.BANK_STATEMENT

        if not os.path.exists(file_path):
            fields.append(BankStatementParser.create_field(
                "bank_statement_csv", None, doc_type, file_path, 0.0, ExtractionStatus.MISSING
            ))
            return transactions, fields

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row_idx = 1
                for row in reader:
                    row_idx += 1
                    tx_id = row.get("transaction_id", f"TX-ROW-{row_idx}")
                    tx_date = row.get("date", "")
                    desc = row.get("description", "")
                    amount_val = row.get("amount", "0")
                    tx_type = row.get("type", "DEBIT").upper()
                    is_sal = str(row.get("is_salary", "")).lower() == "true"
                    is_rec = str(row.get("is_recurring_debit", "")).lower() == "true"

                    try:
                        amt = float(amount_val)
                    except ValueError:
                        amt = 0.0

                    tx = BankTransaction(
                        transaction_id=tx_id,
                        transaction_date=tx_date,
                        description=desc,
                        amount=amt,
                        transaction_type=tx_type,
                        is_salary=is_sal,
                        is_recurring_debit=is_rec
                    )
                    transactions.append(tx)

            fields.append(BankStatementParser.create_field(
                "transaction_records_count", len(transactions), doc_type, f"CSV: {os.path.basename(file_path)}", 0.99, ExtractionStatus.SUCCESS
            ))
        except Exception as e:
            fields.append(BankStatementParser.create_field(
                "bank_statement_csv", str(e), doc_type, file_path, 0.1, ExtractionStatus.FAILURE
            ))

        return transactions, fields
