"""
api_sidecar.py — Optional FastAPI sidecar for webhook and API endpoints.
Run with: uvicorn api_sidecar:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import json
import os

from database import get_db, get_engine, init_db, StudySession, EngagementLog, User

app = FastAPI(
    title="Focus Flow API",
    description="API endpoints for the Student Engagement Monitoring System",
    version="1.0.0",
)

_allowed_origins = os.getenv("API_ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
ALLOWED_ORIGINS = [o.strip() for o in _allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup():
    engine = get_engine()
    init_db(engine)


# ─── Auth ────────────────────────────────────────────────────────────────────
async def verify_api_key(authorization: str = Header(None)):
    """Simple API key verification. In production, validate against DB."""
    expected_key = os.getenv("FOCUS_FLOW_API_KEY", "").strip()
    if not expected_key:
        raise HTTPException(status_code=503, detail="API key is not configured on server")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid API key")
    provided = authorization.split("Bearer ", 1)[1].strip()
    if provided != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return provided


# ─── Models ──────────────────────────────────────────────────────────────────
class WebhookPayload(BaseModel):
    event_type: str
    timestamp: Optional[str] = None
    session_id: Optional[int] = None
    user_id: Optional[int] = None
    data: Optional[dict] = None


class SessionResponse(BaseModel):
    id: int
    name: str
    tag: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    avg_engagement: float
    peak_engagement: float
    total_distractions: int


class LogResponse(BaseModel):
    id: int
    timestamp: Optional[str]
    engagement_score: float
    ear_value: float
    gaze_score: float
    head_pitch: float
    head_yaw: float
    is_distracted: bool
    is_spoof: bool


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/sessions", response_model=list[SessionResponse])
async def list_sessions(user_id: Optional[int] = None,
                        status: Optional[str] = None,
                        api_key: str = Depends(verify_api_key)):
    """List all sessions, optionally filtered by user_id and status."""
    db = next(get_db())
    query = db.query(StudySession)
    if user_id:
        query = query.filter(StudySession.user_id == user_id)
    if status:
        query = query.filter(StudySession.status == status)
    sessions = query.order_by(StudySession.start_time.desc()).limit(100).all()

    return [
        SessionResponse(
            id=s.id, name=s.name, tag=s.tag, status=s.status,
            start_time=s.start_time.isoformat() if s.start_time else None,
            end_time=s.end_time.isoformat() if s.end_time else None,
            avg_engagement=s.avg_engagement, peak_engagement=s.peak_engagement,
            total_distractions=s.total_distractions,
        ) for s in sessions
    ]


@app.get("/api/sessions/{session_id}/logs", response_model=list[LogResponse])
async def get_logs(session_id: int, api_key: str = Depends(verify_api_key)):
    """Get engagement logs for a specific session."""
    db = next(get_db())
    logs = (db.query(EngagementLog)
            .filter(EngagementLog.session_id == session_id)
            .order_by(EngagementLog.timestamp)
            .limit(5000)
            .all())

    if not logs:
        raise HTTPException(status_code=404, detail="No logs found for this session")

    return [
        LogResponse(
            id=l.id,
            timestamp=l.timestamp.isoformat() if l.timestamp else None,
            engagement_score=l.engagement_score,
            ear_value=l.ear_value,
            gaze_score=l.gaze_score,
            head_pitch=l.head_pitch,
            head_yaw=l.head_yaw,
            is_distracted=l.is_distracted,
            is_spoof=l.is_spoof,
        ) for l in logs
    ]


@app.post("/api/webhook/{webhook_id}")
async def receive_webhook(webhook_id: str, payload: WebhookPayload):
    """Receive engagement events via webhook."""
    # In production, validate webhook_id against stored keys
    print(f"[Webhook {webhook_id}] {payload.event_type}: {payload.data}")
    return {
        "received": True,
        "webhook_id": webhook_id,
        "event_type": payload.event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get overall platform statistics."""
    db = next(get_db())
    total_users = db.query(User).count()
    total_sessions = db.query(StudySession).count()
    completed = db.query(StudySession).filter(StudySession.status == "completed").count()
    total_logs = db.query(EngagementLog).count()

    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "completed_sessions": completed,
        "total_engagement_logs": total_logs,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
