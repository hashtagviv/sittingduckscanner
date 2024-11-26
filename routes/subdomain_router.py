from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from api.process_domains import main, stream_subdomain_data, processing_task, cancellation_event
from classes.processors import MAX_THREADS
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()


# Configure the ThreadPoolExecutor with a max number of threads
executor = ThreadPoolExecutor(max_workers=MAX_THREADS)


@router.post("/stop")
async def stop_subdomain_processing():
    """
    Signal the backend to stop subdomain processing.
    """
    if not processing_task.remaining_tasks():
        raise HTTPException(
            status_code=400, detail="No processing task is currently running.")

    # Set the cancellation event
    cancellation_event.set()
    # Update the processing task status
    processing_task.cancel_tasks()
    return {"status": "stopping", "message": "Subdomain processing is stopping."}


class DomainRequest(BaseModel):
    domain: str
    active: bool
    related_domains: Optional[List[str]] = None
    time_limit: Optional[int] = None


def run_wrapper(func, *args):
    return asyncio.run(func(*args))


async def run(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, run_wrapper, func, *args)


@router.post("/start")
async def start_subdomain_processing(request: DomainRequest, background_tasks: BackgroundTasks):
    """
    Start the subdomain processing in the background.
    """
    global processing_task

    # Check if tasks can be added
    if processing_task.remaining_tasks():
        processing_task.add_tasks()
        request_data = (request.domain, request.time_limit,
                        request.related_domains, request.active)
        background_tasks.add_task(run, main, *request_data)
        return {"status": "started", "message": f"Subdomain processing started for {request.domain}"}
    else:
        raise HTTPException(
            status_code=409, detail="Subdomain processing is already running.")


@ router.get("/stream")
async def stream_data():
    """
    Stream the subdomain data in real-time.
    """
    try:
        return await stream_subdomain_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error streaming data")
