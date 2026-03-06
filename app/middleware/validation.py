import json

import structlog
from fastapi import Request, Response
from pydantic import BaseModel, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.stdlib.get_logger()


class SchemaRegistry:
    def __init__(self) -> None:
        self._schemas: dict[tuple[str, str], type[BaseModel]] = {}

    def register(self, method: str, path: str, schema: type[BaseModel]) -> None:
        key = (method.upper(), path)
        self._schemas[key] = schema
        logger.info(
            "schema_registered",
            method=method.upper(),
            path=path,
            schema=schema.__name__,
        )

    def get(self, method: str, path: str) -> type[BaseModel] | None:
        return self._schemas.get((method.upper(), path))


class ValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, registry: SchemaRegistry) -> None:
        super().__init__(app)
        self.registry = registry

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        schema = self.registry.get(request.method, request.url.path)

        if schema is None:
            return await call_next(request)

        body = await request.body()

        if not body:
            logger.warning(
                "validation_failed", reason="empty_body", path=request.url.path
            )
            return Response(
                content=json.dumps(
                    {
                        "detail": [
                            {
                                "loc": ["body"],
                                "msg": "Request body is empty",
                                "type": "missing",
                            }
                        ]
                    }
                ),
                status_code=422,
                media_type="application/json",
            )

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            logger.warning(
                "validation_failed", reason="invalid_json", path=request.url.path
            )
            return Response(
                content=json.dumps(
                    {
                        "detail": [
                            {
                                "loc": ["body"],
                                "msg": f"Invalid JSON: {exc.msg}",
                                "type": "json_invalid",
                            }
                        ]
                    }
                ),
                status_code=422,
                media_type="application/json",
            )

        try:
            schema.model_validate(payload)
        except ValidationError as exc:
            errors = [
                {
                    "loc": ["body", *str(e["loc"][0]).split(".")]
                    if e.get("loc")
                    else ["body"],
                    "msg": e["msg"],
                    "type": e["type"],
                }
                for e in exc.errors()
            ]
            logger.warning(
                "validation_failed",
                reason="schema_mismatch",
                path=request.url.path,
                error_count=len(errors),
            )
            return Response(
                content=json.dumps({"detail": errors}),
                status_code=422,
                media_type="application/json",
            )

        logger.info("validation_passed", path=request.url.path, schema=schema.__name__)
        return await call_next(request)
