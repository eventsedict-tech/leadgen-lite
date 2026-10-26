from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class FilePreviewResponse(BaseModel):
    temp_file_id: str
    filename: str
    total_detected_rows: int
    headers: List[str]
    sample_rows: List[Dict[str, Any]]
    suggested_mappings: Dict[str, str]  # file_header -> lead_field


class ColumnMappingRequest(BaseModel):
    temp_file_id: str
    column_mapping: Dict[str, str]  # file_header -> lead_field
    skip_duplicates: bool = True
    merge_existing: bool = False


class ImportValidationPreview(BaseModel):
    temp_file_id: str
    total_rows: int
    valid_new_records: int
    duplicate_records: int
    invalid_records: int
    preview_items: List[Dict[str, Any]]


class ImportCommitRequest(BaseModel):
    temp_file_id: str
    column_mapping: Dict[str, str]
    skip_duplicates: bool = True
    merge_existing: bool = False


class ImportResultResponse(BaseModel):
    job_id: int
    total_records: int
    imported_records: int
    skipped_records: int
    merged_records: int
    errors: List[Dict[str, Any]]
