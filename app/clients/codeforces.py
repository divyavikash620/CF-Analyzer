from typing import Any, Dict, Optional

import httpx


class CodeforcesAPIError(Exception):
    """Raised for HTTP, JSON, or Codeforces API status failures."""

    def __init__(
        self,
        message: str,
        *,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        api_status: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.endpoint = endpoint
        self.status_code = status_code
        self.api_status = api_status
        self.comment = comment


class CodeforcesClient:
    BASE_URL = "https://codeforces.com/api/"

    def __init__(self, timeout: float = 10.0):
        timeout_cfg = httpx.Timeout(timeout, connect=min(timeout, 5.0))
        self._client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=timeout_cfg)

    async def __aenter__(self) -> "CodeforcesClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = await self._client.get(endpoint, params=params)
        except httpx.RequestError as exc:
            raise CodeforcesAPIError(
                f"request error calling {endpoint}: {exc}",
                endpoint=endpoint,
            ) from exc

        if response.status_code != 200:
            raise CodeforcesAPIError(
                f"http {response.status_code} calling {endpoint}",
                endpoint=endpoint,
                status_code=response.status_code,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise CodeforcesAPIError(
                f"invalid json response from {endpoint}",
                endpoint=endpoint,
                status_code=response.status_code,
            ) from exc

        if not isinstance(payload, dict):
            raise CodeforcesAPIError(
                f"unexpected payload type from {endpoint}",
                endpoint=endpoint,
                status_code=response.status_code,
            )

        api_status = payload.get("status")
        if api_status != "OK":
            comment = payload.get("comment")
            raise CodeforcesAPIError(
                f"api status={api_status} endpoint={endpoint} comment={comment}",
                endpoint=endpoint,
                status_code=response.status_code,
                api_status=str(api_status) if api_status is not None else None,
                comment=str(comment) if comment is not None else None,
            )

        return payload.get("result")

    async def get_user_info(self, handle: str) -> Any:
        return await self._get("user.info", params={"handles": handle})

    async def get_user_rating(self, handle: str) -> Any:
        return await self._get("user.rating", params={"handle": handle})

    async def get_user_submissions(self, handle: str, from_: int = 1, count: int = 1000) -> Any:
        return await self._get(
            "user.status",
            params={"handle": handle, "from": from_, "count": count},
        )


def make_codeforces_client(timeout: Optional[float] = 10.0) -> CodeforcesClient:
    """Create a Codeforces client. Use `async with` or call `close()`."""
    return CodeforcesClient(timeout=timeout or 10.0)
