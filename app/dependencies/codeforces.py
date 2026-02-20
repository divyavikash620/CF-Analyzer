from fastapi import Request


async def get_codeforces_client(request: Request):
    """Async dependency that yields the app-wide CodeforcesClient when available.

    If no app-wide client was initialized (startup not run), this will create a
    short-lived client and ensure it is closed after the request using the
    client's async context manager.
    """
    client = getattr(request.app.state, "codeforces_client", None)
    if client is None:
        from app.clients.codeforces import make_codeforces_client

        async with make_codeforces_client() as c:
            yield c
    else:
        yield client
