from pydantic import BaseModel
from typing import Any, Optional

class UploadResponse(BaseModel):
    dataset_id: str
    rows: int
    cols: int

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    tool: str
    explanation: str
    table: Optional[list[dict]] = None
    profile: Optional[dict[str, Any]] = None