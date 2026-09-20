import subprocess
import sys
from datetime import datetime, timezone

from app.core.config import BASE_DIR
from app.db.models import JobRun
from app.db.session import SessionLocal
from app.workers.celery_app import celery_app


@celery_app.task(name="leadpulse.run_enrichment", bind=True)
def run_enrichment(self, job_id: int) -> dict:
    with SessionLocal() as db:
        job = db.get(JobRun, job_id)
        if not job:
            return {"status": "missing", "job_id": job_id}
        job.status = "RUNNING"
        job.started_at = datetime.now(timezone.utc)
        job.celery_task_id = self.request.id
        db.commit()
        params = job.parameters or {}

    cmd = [sys.executable, str(BASE_DIR / "find_people.py"), "--limit", str(params.get("limit", 15))]
    country = params.get("country")
    category = params.get("category")
    if country and country != "ALL":
        cmd.extend(["--country", country])
    if category and category != "ALL":
        cmd.extend(["--category", category])

    logs: list[str] = []
    try:
        process = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert process.stdout is not None
        for line in process.stdout:
            if clean := line.strip():
                logs = (logs + [clean])[-100:]
                with SessionLocal() as db:
                    job = db.get(JobRun, job_id)
                    job.progress = {"logs": logs}
                    db.commit()
        code = process.wait(timeout=1800)
        with SessionLocal() as db:
            job = db.get(JobRun, job_id)
            job.status = "COMPLETED" if code == 0 else "FAILED"
            job.error = None if code == 0 else f"Process exited with code {code}"
            job.progress = {"logs": logs, "exit_code": code}
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
        return {"status": "completed" if code == 0 else "failed", "job_id": job_id}
    except Exception as exc:
        with SessionLocal() as db:
            job = db.get(JobRun, job_id)
            if job:
                job.status = "FAILED"
                job.error = f"{type(exc).__name__}: {str(exc)[:500]}"
                job.progress = {"logs": logs}
                job.finished_at = datetime.now(timezone.utc)
                db.commit()
        raise
