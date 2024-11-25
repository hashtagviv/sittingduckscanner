from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from api.process_domains import main, stream_subdomain_data, processing_task

router = APIRouter()


class DomainRequest(BaseModel):
    domain: str
    active: bool
    related_domains: Optional[List[str]] = None
    time_limit: Optional[int] = None


@router.post("/start")
async def start_subdomain_processing(request: DomainRequest, background_tasks: BackgroundTasks):
    global processing_task
    if processing_task.remaining_tasks():
        processing_task.add_tasks()
        background_tasks.add_task(
            main, request.domain, time_limit=request.time_limit, related_domains=request.related_domains, active=request.active)
        return {"status": "started", "message": f"Subdomain processing started for {request.domain}"}
    else:
        return {"status": "failed", "message": "Subdomain processing is already running."}


@router.get("/stream")
async def stream_data():
    return await stream_subdomain_data()
