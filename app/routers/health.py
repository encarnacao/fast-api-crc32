import structlog
from fastapi import APIRouter, Request

logger = structlog.stdlib.get_logger()


class HealthRouter:
    def __init__(self) -> None:
        self.router = APIRouter(tags=["health"])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route("/", self.hello, methods=["GET"])

    async def hello(self, request: Request) -> dict:
        logger.info(
            "structured_log_test",
            method=request.method,
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            query_params=str(request.query_params) if request.query_params else None,
        )
        return {"message": "Hello, World!"}
