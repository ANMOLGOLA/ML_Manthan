import os
import json
import csv
import pytest

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
TEST_CASES_DIR = os.path.join(DATA_DIR, "test_cases")

def test_dataset_integrity():
    # 1. Load manifest
    manifest_path = os.path.join(TEST_CASES_DIR, "manifest.json")
    assert os.path.exists(manifest_path), "manifest.json missing"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert len(manifest) == 20, f"Expected 20 test cases, found {len(manifest)}"

    # Check unique IDs
    tc_ids = [item["test_case_id"] for item in manifest]
    app_ids = [item["applicant_id"] for item in manifest]

    assert len(tc_ids) == len(set(tc_ids)), "Duplicate test_case_id found"
    assert len(app_ids) == len(set(app_ids)), "Duplicate applicant_id found"

    expected_ids = [f"TC{i:03d}" for i in range(1, 21)]
    assert sorted(tc_ids) == expected_ids, f"Missing or invalid TC IDs: {set(expected_ids) - set(tc_ids)}"

    # 2. Check raw JSON data
    with open(os.path.join(RAW_DIR, "applications.json"), "r", encoding="utf-8") as f:
        apps = json.load(f)
    with open(os.path.join(RAW_DIR, "salary_slips.json"), "r", encoding="utf-8") as f:
        slips = json.load(f)
    with open(os.path.join(RAW_DIR, "liabilities.json"), "r", encoding="utf-8") as f:
        liabs = json.load(f)

    assert len(apps) == 20, "applications.json does not match 20 records"

    # 3. Check Bank CSV files existence & structure
    for tc_id in tc_ids:
        csv_file = os.path.join(RAW_DIR, f"bank_transactions_{tc_id}.csv")
        assert os.path.exists(csv_file), f"Missing CSV for {tc_id}"
        
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == ["transaction_id", "date", "description", "amount", "type", "is_salary", "is_recurring_debit"]
            rows = list(reader)
            assert len(rows) > 0, f"CSV for {tc_id} is empty"

    print("Dataset integrity check PASSED: 20 unique test cases, no missing or duplicate IDs!")

if __name__ == "__main__":
    test_dataset_integrity()
