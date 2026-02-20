from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{handle}")
async def analyze_handle(handle: str) -> Dict[str, Any]:
    """Return mock analysis data for the given Codeforces handle."""
    _ = handle
    return {
        "tag_accuracy": {"implementation": 65, "dp": 40},
        "rating_accuracy": {"800-1000": 80, "1000-1200": 55},
        "average_solve_time": 1200,
        "insights": [
            "Weak in DP problems",
            "Strong in implementation tasks",
        ],
    }
