from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, SuppressionList, Lead
from app.models.enums import CRMStage
from app.api.deps import get_current_user

router = APIRouter(prefix="/suppression", tags=["Suppression List"])


class SuppressionCreate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    domain: Optional[str] = None
    reason: str = "Requested Unsubscribe"


class SuppressionResponse(BaseModel):
    id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    domain: Optional[str] = None
    reason: str
    added_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[SuppressionResponse])
def list_suppression(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = db.query(SuppressionList).filter(
        SuppressionList.organization_id == current_user.organization_id
    ).order_by(SuppressionList.created_at.desc()).all()

    return [SuppressionResponse.model_validate(i) for i in items]


@router.post("", response_model=SuppressionResponse, status_code=status.HTTP_201_CREATED)
def add_to_suppression(
    req: SuppressionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not req.email and not req.phone and not req.domain:
        raise HTTPException(status_code=400, detail="Must provide at least one of email, phone, or domain.")

    supp = SuppressionList(
        organization_id=current_user.organization_id,
        email=req.email.strip().lower() if req.email else None,
        phone=req.phone.strip() if req.phone else None,
        domain=req.domain.strip().lower() if req.domain else None,
        reason=req.reason.strip(),
        added_by=current_user.full_name
    )
    db.add(supp)

    # Immediately update any matching leads in CRM to "Do Not Contact"
    leads_to_update = db.query(Lead).filter(Lead.organization_id == current_user.organization_id)
    if supp.email:
        leads_to_update = leads_to_update.filter(Lead.general_business_email == supp.email)
    elif supp.domain:
        leads_to_update = leads_to_update.filter(Lead.normalized_domain == supp.domain)
    elif supp.phone:
        leads_to_update = leads_to_update.filter(Lead.public_business_phone == supp.phone)

    for l in leads_to_update.all():
        l.crm_status = CRMStage.DO_NOT_CONTACT.value

    db.commit()
    db.refresh(supp)
    return SuppressionResponse.model_validate(supp)


@router.delete("/{suppression_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_suppression(
    suppression_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    supp = db.query(SuppressionList).filter(
        SuppressionList.id == suppression_id,
        SuppressionList.organization_id == current_user.organization_id
    ).first()
    if not supp:
        raise HTTPException(status_code=404, detail="Suppression entry not found")

    db.delete(supp)
    db.commit()
    return None
