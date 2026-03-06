import io
import zlib

import pytest
from fastapi import UploadFile
from httpx import ASGITransport, AsyncClient

from app.dependencies.pdf import validate_pdf
from app.main import app

PDF_CONTENT = b"%PDF-1.4 fake pdf content for testing"


def _make_upload(
    content: bytes = PDF_CONTENT,
    filename: str = "test.pdf",
    content_type: str = "application/pdf",
) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(content),
        filename=filename,
        headers={"content-type": content_type},
    )


# ---------------------------------------------------------------------------
# validate_pdf unit tests
# ---------------------------------------------------------------------------


class TestValidatePdfExtension:
    @pytest.mark.asyncio
    async def test_rejects_wrong_extension(self):
        file = _make_upload(filename="test.txt")
        with pytest.raises(Exception) as exc_info:
            await validate_pdf(file)
        assert exc_info.value.status_code == 422
        assert "pdf extension" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_rejects_missing_filename(self):
        file = _make_upload(filename=None)
        with pytest.raises(Exception) as exc_info:
            await validate_pdf(file)
        assert exc_info.value.status_code == 422


class TestValidatePdfContentType:
    @pytest.mark.asyncio
    async def test_rejects_wrong_content_type(self):
        file = _make_upload(content_type="text/plain")
        with pytest.raises(Exception) as exc_info:
            await validate_pdf(file)
        assert exc_info.value.status_code == 422
        assert "content type must be application/pdf" in exc_info.value.detail.lower()


class TestValidatePdfMagicBytes:
    @pytest.mark.asyncio
    async def test_rejects_invalid_magic_bytes(self):
        file = _make_upload(content=b"NOT-A-PDF content here")
        with pytest.raises(Exception) as exc_info:
            await validate_pdf(file)
        assert exc_info.value.status_code == 422
        assert "valid pdf" in exc_info.value.detail.lower()


class TestValidatePdfSuccess:
    @pytest.mark.asyncio
    async def test_accepts_valid_pdf(self):
        file = _make_upload()
        result = await validate_pdf(file)
        assert result.filename == "test.pdf"
        # cursor must be back at the start after validation
        content = await result.read()
        assert content == PDF_CONTENT


# ---------------------------------------------------------------------------
# POST /v1/calcular_crc integration tests
# ---------------------------------------------------------------------------


class TestCalcCrcEndpoint:
    @pytest.mark.asyncio
    async def test_valid_pdf_returns_correct_crc(self):
        expected_crc = zlib.crc32(PDF_CONTENT) & 0xFFFFFFFF

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/v1/calcular_crc",
                files={"file": ("doc.pdf", io.BytesIO(PDF_CONTENT), "application/pdf")},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["filename"] == "doc.pdf"
        assert body["size"] == len(PDF_CONTENT)
        assert body["status"] == "received"
        assert body["crc32"] == expected_crc

    @pytest.mark.asyncio
    async def test_invalid_file_returns_422(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/v1/calcular_crc",
                files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
            )

        assert resp.status_code == 422
