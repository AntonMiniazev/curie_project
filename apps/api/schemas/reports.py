# apps/api/schemas/reports.py

from pydantic import BaseModel
from pydantic import ConfigDict


class ReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None
    category: str
    streamlit_path: str
    required_role: str
    enabled: bool
    sort_order: int


class ReportsResponse(BaseModel):
    items: list[ReportItem]
    count: int
