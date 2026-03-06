from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging import configure_logging
from app.middleware.validation import SchemaRegistry, ValidationMiddleware
from app.routers.crc import CrcRouter
from app.routers.health import HealthRouter

logger = structlog.stdlib.get_logger()


class Application:
    def __init__(self) -> None:
        configure_logging()
        self.schema_registry = SchemaRegistry()
        self.app = FastAPI(
            title=settings.app_name,
            lifespan=self._lifespan,
        )
        self._configure_cors()
        self._configure_validation()
        self._register_routers()

    @staticmethod
    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
        logger.info("application_startup", app_name=settings.app_name)
        yield
        logger.info("application_shutdown", app_name=settings.app_name)

    def _configure_cors(self) -> None:
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_routers(self) -> None:
        health = HealthRouter()
        crc = CrcRouter()
        self.app.include_router(health.router)
        self.app.include_router(crc.router)

    def _configure_validation(self) -> None:
        self._register_schemas()
        self.app.add_middleware(ValidationMiddleware, registry=self.schema_registry)

    def _register_schemas(self) -> None:
        # Validation Middleware só funcionaria com JSON, decidi passar pra multipart e implementar a validação diretamente na rota.
        pass  


app = Application().app
