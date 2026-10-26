from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, FollowUpTask, Lead
from app.models.enums import TaskStatus
from app.api.deps import get_current_user

router = APIRouter(prefix="/tasks", tags=["Follow-Up Tasks"])


class TaskCreate(BaseModel):
    lead_id: int
    title: str
    due_date: datetime
    notes: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    lead_id: int
    company_name: Optional[str] = None
    title: str
    due_date: datetime
    status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    req: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == req.lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    task = FollowUpTask(
        organization_id=current_user.organization_id,
        lead_id=lead.id,
        title=req.title.strip(),
        due_date=req.due_date,
        status=TaskStatus.PENDING.value,
        notes=req.notes
    )
    db.add(task)

    # Sync lead follow up date
    lead.follow_up_date = req.due_date
    db.commit()
    db.refresh(task)

    return TaskResponse(
        id=task.id,
        lead_id=task.lead_id,
        company_name=lead.company_name,
        title=task.title,
        due_date=task.due_date,
        status=task.status,
        notes=task.notes,
        created_at=task.created_at
    )


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    status_filter: Optional[str] = Query(None, description="pending, completed, cancelled"),
    lead_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FollowUpTask).filter(
        FollowUpTask.organization_id == current_user.organization_id
    )
    if status_filter:
        query = query.filter(FollowUpTask.status == status_filter)
    if lead_id:
        query = query.filter(FollowUpTask.lead_id == lead_id)

    tasks = query.order_by(FollowUpTask.due_date.asc()).all()

    resp = []
    for t in tasks:
        comp_name = t.lead.company_name if t.lead else "Unknown"
        resp.append(TaskResponse(
            id=t.id,
            lead_id=t.lead_id,
            company_name=comp_name,
            title=t.title,
            due_date=t.due_date,
            status=t.status,
            notes=t.notes,
            created_at=t.created_at
        ))
    return resp


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    req: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(FollowUpTask).filter(
        FollowUpTask.id == task_id,
        FollowUpTask.organization_id == current_user.organization_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if req.title is not None:
        task.title = req.title.strip()
    if req.due_date is not None:
        task.due_date = req.due_date
    if req.status is not None:
        task.status = req.status
    if req.notes is not None:
        task.notes = req.notes

    db.commit()
    db.refresh(task)

    comp_name = task.lead.company_name if task.lead else "Unknown"
    return TaskResponse(
        id=task.id,
        lead_id=task.lead_id,
        company_name=comp_name,
        title=task.title,
        due_date=task.due_date,
        status=task.status,
        notes=task.notes,
        created_at=task.created_at
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(FollowUpTask).filter(
        FollowUpTask.id == task_id,
        FollowUpTask.organization_id == current_user.organization_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return None
