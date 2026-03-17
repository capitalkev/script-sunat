from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.interfaces.routers import sunat


def create_application() -> FastAPI:
    """
    Application factory function.
    Returns:
        FastAPI: The configured application instance.
    """
    application = FastAPI(
        title="Operaciones SaaS Peru",
        description="API para la gestión de operaciones en Perú",
        version="1.0.0",
    )

    origins = ["http://localhost:5173", "*"]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(sunat.router)

    return application


app = create_application()
