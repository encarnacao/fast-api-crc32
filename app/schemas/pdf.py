import base64

from pydantic import BaseModel, field_validator


class PdfUploadSchema(BaseModel):
    filename: str
    content_type: str
    data: str

    @field_validator("filename")
    @classmethod
    def filename_must_be_pdf(cls, v: str) -> str:
        if not v.lower().endswith(".pdf"):
            raise ValueError("Filename must have a .pdf extension")
        return v

    @field_validator("content_type")
    @classmethod
    def content_type_must_be_pdf(cls, v: str) -> str:
        if v != "application/pdf":
            raise ValueError("Content type must be application/pdf")
        return v

    @field_validator("data")
    @classmethod
    def data_must_be_valid_base64(cls, v: str) -> str:
        try:
            decoded = base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("Data must be valid base64-encoded content")
        if decoded[:5] != b"%PDF-":
            raise ValueError(
                "Decoded data does not appear to be a valid PDF (missing %PDF- header)"
            )
        return v
