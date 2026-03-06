import structlog
from fastapi import HTTPException, UploadFile

logger = structlog.stdlib.get_logger()

PDF_MAGIC_BYTES = b"%PDF-"
ALLOWED_CONTENT_TYPES = {"application/pdf"}


async def validate_pdf(file: UploadFile) -> UploadFile:
    if file.filename is None or not file.filename.lower().endswith(".pdf"):
        logger.warning(
            "pdf_validation_failed",
            reason="invalid_extension",
            filename=file.filename,
        )
        raise HTTPException(
            status_code=422,
            detail="Uploaded file must have a .pdf extension",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(
            "pdf_validation_failed",
            reason="invalid_content_type",
            content_type=file.content_type,
        )
        raise HTTPException(
            status_code=422,
            detail=f"Content type must be application/pdf, got {file.content_type}",
        )

    header = await file.read(5)
    if header != PDF_MAGIC_BYTES:
        logger.warning(
            "pdf_validation_failed",
            reason="invalid_magic_bytes",
            filename=file.filename,
        )
        raise HTTPException(
            status_code=422,
            detail="File content does not appear to be a valid PDF",
        )

    await file.seek(0)

    logger.info(
        "pdf_validation_passed",
        filename=file.filename,
        content_type=file.content_type,
    )
    return file
