from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.models.models import (
    User, Lead, WebsiteAudit, FollowUpTask, ImportJob, ResearchJob, LeadSource
)
from app.models.enums import CRMStage, LeadPriority, TaskStatus
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics")
def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    org_id = current_user.organization_id
    now = datetime.now(timezone.utc)

    # Core Metrics calculated strictly from database
    total_leads = db.query(Lead).filter(Lead.organization_id == org_id).count()

    leads_imported = db.query(Lead).filter(
        Lead.organization_id == org_id,
        Lead.data_source.ilike("File Import%")
    ).count()

    leads_discovered = db.query(Lead).filter(
        Lead.organization_id == org_id,
        Lead.data_source.not_ilike("File Import%"),
        Lead.data_source != "Manual Entry"
    ).count()

    high_priority_leads = db.query(Lead).filter(
        Lead.organization_id == org_id,
        Lead.priority == LeadPriority.HIGH.value
    ).count()

    websites_analyzed = db.query(WebsiteAudit).filter(
        WebsiteAudit.organization_id == org_id
    ).count()

    qualified_leads = db.query(Lead).filter(
        Lead.organization_id == org_id,
        Lead.crm_status == CRMStage.QUALIFIED.value
    ).count()

    follow_ups_due = db.query(FollowUpTask).filter(
        FollowUpTask.organization_id == org_id,
        FollowUpTask.status == TaskStatus.PENDING.value,
        FollowUpTask.due_date <= now
    ).count()

    converted_leads = db.query(Lead).filter(
        Lead.organization_id == org_id,
        Lead.crm_status == CRMStage.CONVERTED.value
    ).count()

    # Distribution: By Industry
    industry_counts = db.query(
        Lead.industry, func.count(Lead.id)
    ).filter(
        Lead.organization_id == org_id,
        Lead.industry != None
    ).group_by(Lead.industry).order_by(desc(func.count(Lead.id))).limit(8).all()

    # Distribution: By City
    city_counts = db.query(
        Lead.city, func.count(Lead.id)
    ).filter(
        Lead.organization_id == org_id,
        Lead.city != None
    ).group_by(Lead.city).order_by(desc(func.count(Lead.id))).limit(8).all()

    # Distribution: By Source
    source_counts = db.query(
        Lead.data_source, func.count(Lead.id)
    ).filter(
        Lead.organization_id == org_id
    ).group_by(Lead.data_source).order_by(desc(func.count(Lead.id))).limit(6).all()

    # Distribution: By Priority
    priority_counts = db.query(
        Lead.priority, func.count(Lead.id)
    ).filter(
        Lead.organization_id == org_id
    ).group_by(Lead.priority).all()

    # Recent Imports (last 5)
    recent_imports = db.query(ImportJob).filter(
        ImportJob.organization_id == org_id
    ).order_by(desc(ImportJob.created_at)).limit(5).all()

    # Recent Research Jobs (last 5)
    recent_jobs = db.query(ResearchJob).filter(
        ResearchJob.organization_id == org_id
    ).order_by(desc(ResearchJob.created_at)).limit(5).all()

    # Upcoming Follow-Ups (next 5)
    upcoming_tasks = db.query(FollowUpTask).filter(
        FollowUpTask.organization_id == org_id,
        FollowUpTask.status == TaskStatus.PENDING.value
    ).order_by(FollowUpTask.due_date.asc()).limit(5).all()

    return {
        "metrics": {
            "total_leads": total_leads,
            "leads_imported": leads_imported,
            "leads_discovered": leads_discovered,
            "high_priority_leads": high_priority_leads,
            "websites_analyzed": websites_analyzed,
            "qualified_leads": qualified_leads,
            "follow_ups_due": follow_ups_due,
            "converted_leads": converted_leads
        },
        "distributions": {
            "by_industry": [{"label": str(k or "Unspecified"), "count": v} for k, v in industry_counts],
            "by_city": [{"label": str(k or "Unspecified"), "count": v} for k, v in city_counts],
            "by_source": [{"label": str(k or "Direct"), "count": v} for k, v in source_counts],
            "by_priority": [{"label": str(k or "Unscored"), "count": v} for k, v in priority_counts]
        },
        "recent_imports": [
            {
                "id": j.id,
                "filename": j.filename,
                "imported": j.imported_records,
                "skipped": j.skipped_records,
                "merged": j.merged_records,
                "created_at": j.created_at.strftime("%Y-%m-%d %H:%M") if j.created_at else ""
            }
            for j in recent_imports
        ],
        "recent_research_jobs": [
            {
                "id": r.id,
                "company_name": r.lead.company_name if r.lead else "Unknown",
                "status": r.status,
                "log": r.log,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""
            }
            for r in recent_jobs
        ],
        "upcoming_follow_ups": [
            {
                "id": t.id,
                "lead_id": t.lead_id,
                "company_name": t.lead.company_name if t.lead else "Unknown",
                "title": t.title,
                "due_date": t.due_date.strftime("%Y-%m-%d %H:%M"),
                "is_overdue": t.due_date < now
            }
            for t in upcoming_tasks
        ]
    }
