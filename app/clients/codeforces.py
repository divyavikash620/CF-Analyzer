from typing import Any, Dict, Optional

import httpx


class CodeforcesAPIError(Exception):
    """Raised when Codeforces API responds with a non-OK status."""


class CodeforcesClient:
    BASE_URL = "https://codeforces.com/api/"

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def _get(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            resp = await self._client.get(method, params=params)
        except httpx.RequestError as exc:
            raise CodeforcesAPIError(f"request error: {exc}") from exc

        # non-2xx HTTP status
        if resp.status_code != 200:
            raise CodeforcesAPIError(f"http {resp.status_code}: {resp.text}")

        try:
            payload = resp.json()
        except ValueError as exc:
            raise CodeforcesAPIError("invalid json response") from exc

        status = payload.get("status")
        if status != "OK":
            # Codeforces returns {'status': 'FAILED', 'comment': '...'} on error
            raise CodeforcesAPIError(f"api status={status} comment={payload.get('comment')}")

        return payload.get("result")

    async def get_user_info(self, handle: str) -> Any:
        return await self._get("user.info", params={"handles": handle})

    async def get_user_rating(self, handle: str) -> Any:
        return await self._get("user.rating", params={"handle": handle})

    async def get_user_submissions(self, handle: str, from_: int = 1, count: int = 1000) -> Any:
        return await self._get("user.status", params={"handle": handle, "from": from_, "count": count})


def make_codeforces_client(timeout: Optional[float] = 10.0) -> CodeforcesClient:
    timeout_cfg = httpx.Timeout(timeout, connect=5.0)
    client = httpx.AsyncClient(base_url=CodeforcesClient.BASE_URL, timeout=timeout_cfg)
    return CodeforcesClient(client)
