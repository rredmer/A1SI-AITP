from datetime import datetime

from pydantic import BaseModel


class JobCreate(BaseModel):
    job_type: str
    params: dict | None = None


class JobProgress(BaseModel):
    progress: float
    progress_message: str


class JobRead(BaseModel):
    id: str
    job_type: str
    status: str
    progress: float
    progress_message: str
    params: dict | None = None
    result: dict | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
