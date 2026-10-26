from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, ResearchJob, Lead
from app.services.enrichment_service import enrich_lead
from app.api.deps import get_current_user

router = APIRouter(prefix="/enrichment", tags=["Company Enrichment"])


@router.post("/queue/{lead_id}")
async def queue_enrichment(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes website enrichment for a specific lead."""
    try:
        result = await enrich_lead(
            db=db,
            org_id=current_user.organization_id,
            user_id=current_user.id,
            lead_id=lead_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrichment error: {str(e)}")


@router.get("/status/{lead_id}")
def get_enrichment_status(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ResearchJob).filter(
        ResearchJob.lead_id == lead_id,
        ResearchJob.organization_id == current_user.organization_id
    ).first()
    if not job:
        return {"lead_id": lead_id, "status": "none", "log": "No research job queued"}
    return {
        "lead_id": lead_id,
        "status": job.status,
        "log": job.log,
        "created_at": job.created_at
    }
