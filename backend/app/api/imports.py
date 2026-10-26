import os
import uuid
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.models import User, ImportJob
from app.schemas.import_export import (
    FilePreviewResponse, ColumnMappingRequest, ImportValidationPreview,
    ImportCommitRequest, ImportResultResponse
)
from app.services.import_service import (
    parse_and_preview_file, validate_import_preview, execute_import
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post("/preview", response_model=FilePreviewResponse)
async def upload_and_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a .csv or .xlsx file."
        )

    # Validate file size
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB)"
        )

    temp_id = str(uuid.uuid4())
    temp_filename = f"{temp_id}_{file.filename}"
    temp_path = os.path.join(settings.UPLOAD_DIR, temp_filename)

    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        preview_data = parse_and_preview_file(temp_path, file.filename or "uploaded_file")
        return FilePreviewResponse(
            temp_file_id=temp_filename,
            filename=file.filename or "uploaded_file",
            total_detected_rows=preview_data["total_detected_rows"],
            headers=preview_data["headers"],
            sample_rows=preview_data["sample_rows"],
            suggested_mappings=preview_data["suggested_mappings"]
        )
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")


@router.post("/validate", response_model=ImportValidationPreview)
def validate_mapping(
    req: ColumnMappingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    temp_path = os.path.join(settings.UPLOAD_DIR, req.temp_file_id)
    if not os.path.exists(temp_path):
        raise HTTPException(status_code=404, detail="Uploaded file session expired or not found.")

    try:
        preview = validate_import_preview(db, current_user.organization_id, temp_path, req.column_mapping)
        return ImportValidationPreview(
            temp_file_id=req.temp_file_id,
            total_rows=preview["total_rows"],
            valid_new_records=preview["valid_new_records"],
            duplicate_records=preview["duplicate_records"],
            invalid_records=preview["invalid_records"],
            preview_items=preview["preview_items"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@router.post("/commit", response_model=ImportResultResponse)
def commit_import(
    req: ImportCommitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    temp_path = os.path.join(settings.UPLOAD_DIR, req.temp_file_id)
    if not os.path.exists(temp_path):
        raise HTTPException(status_code=404, detail="Uploaded file session expired or not found.")

    # Original filename from temp_id_original.ext
    parts = req.temp_file_id.split("_", 1)
    original_name = parts[1] if len(parts) > 1 else req.temp_file_id

    try:
        result = execute_import(
            db=db,
            org_id=current_user.organization_id,
            user_id=current_user.id,
            file_path=temp_path,
            filename=original_name,
            column_mapping=req.column_mapping,
            skip_duplicates=req.skip_duplicates,
            merge_existing=req.merge_existing
        )
        return ImportResultResponse(**result)
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.get("/history")
def get_import_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    jobs = db.query(ImportJob).filter(
        ImportJob.organization_id == current_user.organization_id
    ).order_by(ImportJob.created_at.desc()).limit(20).all()
    
    return [
        {
            "id": j.id,
            "filename": j.filename,
            "total_records": j.total_records,
            "imported_records": j.imported_records,
            "skipped_records": j.skipped_records,
            "merged_records": j.merged_records,
            "created_at": j.created_at
        }
        for j in jobs
    ]


@router.get("/{job_id}/errors")
def get_job_errors(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ImportJob).filter(
        ImportJob.id == job_id,
        ImportJob.organization_id == current_user.organization_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    errors = json.loads(job.error_report_json) if job.error_report_json else []
    return {"job_id": job.id, "filename": job.filename, "errors": errors}
