from typing import Any, Dict, Optional

import httpx


class CodeforcesAPIError(Exception):
    """Raised when Codeforces API responds with a non-OK status or on request failures."""


class CodeforcesClient:
    BASE_URL = "https://codeforces.com/api/"

    def __init__(self, timeout: float = 10.0):
        timeout_cfg = httpx.Timeout(timeout, connect=5.0)
        self._client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=timeout_cfg)

    async def close(self) -> None:
        """Close the underlying httpx.AsyncClient."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

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
    """Factory that returns a configured CodeforcesClient instance.

    The caller is responsible for calling `await client.close()` or using
    `async with make_codeforces_client() as client:`.
    """
    return CodeforcesClient(timeout=timeout)
