# apps/api/schemas/meta.py

from pydantic import BaseModel


class MetaResponse(BaseModel):
    app: str
    environment: str
    features: list[str]
