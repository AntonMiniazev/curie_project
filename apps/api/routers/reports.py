from typing import Annotated
from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from ..schemas.reports import ReportsResponse
from ..db.session import get_db_session
from ..db.models import Report

router = APIRouter(prefix="/api/reports", tags=["reports"])

db_dependency = Annotated[Session, Depends(get_db_session)]


@router.get("", response_model=ReportsResponse, status_code=status.HTTP_200_OK)
def get_reports(db: db_dependency):
    reports = (
        db.query(Report)
        .filter(Report.enabled.is_(True))
        .order_by(Report.sort_order, Report.title)
        .all()
    )
    return ReportsResponse(items=reports, count=len(reports))
