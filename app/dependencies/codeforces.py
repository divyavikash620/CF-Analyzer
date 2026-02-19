from fastapi import Request, Depends

from app.clients.codeforces import CodeforcesClient


def get_codeforces_client(request: Request) -> CodeforcesClient:
    """Dependency that returns the app-wide CodeforcesClient instance created on startup."""
    client = getattr(request.app.state, "codeforces_client", None)
    if client is None:
        # fallback: create a temporary client (not attached to app state)
        # Note: callers that depend on the app-wide client should ensure the app
        # startup handler ran; this fallback creates a short-lived client.
        from app.clients.codeforces import make_codeforces_client

        return make_codeforces_client()
    return client
