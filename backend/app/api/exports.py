from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.core.database import get_db
from app.models.models import Lead, User, ImportJob
from app.services.export_service import export_leads_csv, export_leads_excel
from app.api.deps import get_current_user

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/leads")
def export_leads(
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
    stage: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Lead).filter(Lead.organization_id == current_user.organization_id)

    if stage:
        query = query.filter(Lead.crm_status == stage)
    if priority:
        query = query.filter(Lead.priority == priority)
    if industry:
        query = query.filter(Lead.industry == industry)
    if city:
        query = query.filter(Lead.city == city)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Lead.company_name.ilike(s),
                Lead.general_business_email.ilike(s),
                Lead.city.ilike(s),
                Lead.industry.ilike(s)
            )
        )

    leads = query.order_by(desc(Lead.created_at)).all()

    filename = f"leads_export_{current_user.organization_id}"
    if stage:
        filename += f"_{stage.lower().replace(' ', '_')}"
    if priority:
        filename += f"_{priority.lower().replace(' ', '_')}"

    if format == "csv":
        file_stream = export_leads_csv(leads)
        media_type = "text/csv"
        ext = "csv"
    else:
        file_stream = export_leads_excel(leads)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"

    headers = {
        "Content-Disposition": f"attachment; filename={filename}.{ext}"
    }

    return StreamingResponse(file_stream, media_type=media_type, headers=headers)
