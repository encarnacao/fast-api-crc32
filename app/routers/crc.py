import structlog
import zlib
from fastapi import APIRouter, Depends, Request, UploadFile

from app.dependencies.pdf import validate_pdf

logger = structlog.stdlib.get_logger()


class CrcRouter:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/v1")
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route(
            "/calcular_crc",
            self.calcular_crc,
            methods=["POST"],
        )

    async def calcular_crc(
        self,
        request: Request,
        file: UploadFile = Depends(validate_pdf),
    ) -> dict:
        content = await file.read()

        crc_value = zlib.crc32(content) & 0xFFFFFFFF
        
        if(crc_value == 0):
            logger.warning(
                "crc_calculation_warning",
                filename=file.filename,
                reason="crc32_zero",
            )

        logger.info(
            "request_received",
            method=request.method,
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            filename=file.filename,
            file_size=len(content),
            crc32_value=crc_value,
        )
        

        return {
            "filename": file.filename,
            "size": len(content),
            "status": "received",
            "crc32": crc_value,
        }
