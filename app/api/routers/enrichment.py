from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import JobRun
from app.db.session import get_db
from app.schemas.api import EnrichmentRequest
from app.workers.tasks.enrichment import run_enrichment

router = APIRouter(prefix="/api", tags=["enrichment"])


@router.post("/enrich", status_code=202)
def start_enrichment(payload: EnrichmentRequest = Depends(), db: Session = Depends(get_db)) -> dict:
    running = db.scalar(
        select(JobRun).where(JobRun.kind == "enrichment", JobRun.status.in_(["QUEUED", "RUNNING"])).limit(1)
    )
    if running:
        return {"status": "already_running", "job_id": running.id, "message": "Enrichment is already in progress"}
    job = JobRun(kind="enrichment", status="QUEUED", parameters=payload.model_dump(), progress={"logs": []})
    db.add(job)
    db.commit()
    db.refresh(job)
    try:
        task = run_enrichment.delay(job.id)
        job.celery_task_id = task.id
        db.commit()
    except Exception as exc:
        job.status = "FAILED"
        job.error = f"Unable to publish task: {type(exc).__name__}"
        db.commit()
        raise HTTPException(status_code=503, detail="Background worker is unavailable") from exc
    return {
        "status": "queued",
        "job_id": job.id,
        "message": f"Enrichment queued for {payload.category} in {payload.country}",
    }


@router.get("/enrich-status")
def get_enrichment_status(job_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    job = (
        db.get(JobRun, job_id)
        if job_id
        else db.scalar(select(JobRun).where(JobRun.kind == "enrichment").order_by(desc(JobRun.id)).limit(1))
    )
    if not job:
        return {"running": False, "log": [], "count": 0}
    progress = job.progress or {}
    return {
        "job_id": job.id,
        "status": job.status,
        "running": job.status in {"QUEUED", "RUNNING"},
        "log": progress.get("logs", []),
        "count": progress.get("count", 0),
        "error": job.error,
    }
