from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.modules.authentication.presentation.router import router as authentication_router
from src.modules.transport_data.presentation.router import router as transport_router


def create_app() -> FastAPI:
    """Compose the single-worker modular-monolith HTTP application."""
    app = FastAPI(title="Uzair Transport Service API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(authentication_router)
    app.include_router(transport_router)

    @app.get("/health", tags=["platform"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
