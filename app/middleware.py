from fastapi.middleware.cors import CORSMiddleware
from .core.config import ALLOWED_ORIGINS


def add_cors_middleware(app):
    """
    Adds CORS middleware to the FastAPI application.

    This allows cross-origin requests from any origin.
    You can specify allowed origins as needed.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
