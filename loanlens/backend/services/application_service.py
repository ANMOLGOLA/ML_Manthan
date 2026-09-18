from typing import Any

async def process_application(payload: Any) -> str:
    return "app_mock_123"

async def get_application(app_id: str) -> Any:
    return {"application_id": app_id}

async def get_results(app_id: str) -> Any:
    return {}

async def get_evidence(app_id: str) -> Any:
    return {}
