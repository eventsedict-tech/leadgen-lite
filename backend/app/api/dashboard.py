from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.models.models import (
    User, Lead, WebsiteAudit, FollowUpTask, ImportJob, ResearchJob, LeadSource
)
from app.models.enums import CRMStage, LeadPriority, TaskStatus
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _format_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    try:
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(dt)


def _is_task_overdue(due_date: Optional[datetime]) -> bool:
    if not due_date:
        return False
    try:
        if due_date.tzinfo is not None:
            return due_date < datetime.now(timezone.utc)
        return due_date < datetime.utcnow()
    except Exception:
        return False


@router.get("/metrics")
def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    org_id = current_user.organization_id
    now_utc = datetime.utcnow()

    try:
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
            FollowUpTask.due_date <= now_utc
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
                    "created_at": _format_datetime(j.created_at)
                }
                for j in recent_imports
            ],
            "recent_research_jobs": [
                {
                    "id": r.id,
                    "company_name": r.lead.company_name if r.lead else "Unknown",
                    "status": r.status,
                    "log": r.log,
                    "created_at": _format_datetime(r.created_at)
                }
                for r in recent_jobs
            ],
            "upcoming_follow_ups": [
                {
                    "id": t.id,
                    "lead_id": t.lead_id,
                    "company_name": t.lead.company_name if t.lead else "Unknown",
                    "title": t.title,
                    "due_date": _format_datetime(t.due_date),
                    "is_overdue": _is_task_overdue(t.due_date)
                }
                for t in upcoming_tasks
            ]
        }
    except Exception as e:
        logger.error(f"Error computing dashboard metrics: {str(e)}", exc_info=True)
        return {
            "metrics": {
                "total_leads": 0,
                "leads_imported": 0,
                "leads_discovered": 0,
                "high_priority_leads": 0,
                "websites_analyzed": 0,
                "qualified_leads": 0,
                "follow_ups_due": 0,
                "converted_leads": 0
            },
            "distributions": {
                "by_industry": [],
                "by_city": [],
                "by_source": [],
                "by_priority": []
            },
            "recent_imports": [],
            "recent_research_jobs": [],
            "upcoming_follow_ups": []
        }

