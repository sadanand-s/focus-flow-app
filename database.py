"""
database.py — SQLAlchemy database layer with configurable engine.
Supports SQLite (default) and PostgreSQL/Supabase.
"""
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import (create_engine, Column, Integer, String, Float,
                        DateTime, Boolean, ForeignKey, Text, JSON, inspect, text)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship


Base = declarative_base()


# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")
    training_samples = relationship("TrainingData", back_populates="user", cascade="all, delete-orphan")


class StudySession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), default="Study Session")
    tag = Column(String(100), default="General")
    status = Column(String(20), default="active")  # active | completed
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    avg_engagement = Column(Float, default=0.0)
    peak_engagement = Column(Float, default=0.0)
    total_distractions = Column(Integer, default=0)
    spoof_detected = Column(Boolean, default=False)
    is_ground_truth = Column(Boolean, default=False)
    summary_text = Column(Text, nullable=True)

    user = relationship("User", back_populates="sessions")
    logs = relationship("EngagementLog", back_populates="session", cascade="all, delete-orphan")


class EngagementLog(Base):
    __tablename__ = "engagement_logs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ear_value = Column(Float, default=0.0)
    head_pitch = Column(Float, default=0.0)
    head_yaw = Column(Float, default=0.0)
    head_roll = Column(Float, default=0.0)
    gaze_score = Column(Float, default=1.0)
    expression_score = Column(Float, default=1.0)
    presence_score = Column(Float, default=1.0)
    engagement_score = Column(Float, default=0.0)
    is_distracted = Column(Boolean, default=False)
    is_spoof = Column(Boolean, default=False)

    session = relationship("StudySession", back_populates="logs")


class UserSetting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    troll_mode = Column(Boolean, default=True)
    nudge_only = Column(Boolean, default=False)
    theme = Column(String(20), default="Dark")
    nudge_sensitivity = Column(String(10), default="Medium")
    notification_sound = Column(Boolean, default=True)
    webcam_source = Column(Integer, default=0)
    export_preference = Column(String(10), default="Both")
    bot_training_enabled = Column(Boolean, default=False)
    
    # Extra settings (JSON blob for accent_color, app_name, etc.)
    profile_avatar = Column(Text, nullable=True)  # Base64
    extra_config = Column(JSON, default=dict)

    user = relationship("User", back_populates="settings")


class TrainingData(Base):
    __tablename__ = "training_data"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    feature_vector = Column(Text)  # JSON array of [ear, pitch, yaw, roll, gaze, expression]
    label = Column(Integer)  # 0 = distracted, 1 = focused
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="training_samples")


# ─── Engine Management ────────────────────────────────────────────────────────

_engine_cache = {}


def get_engine(db_url=None):
    """Get or create a SQLAlchemy engine. Caches engines by URL."""
    if db_url is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///focus_flow.db")

    # Supabase/Heroku fix
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    if db_url not in _engine_cache:
        connect_args = {}
        if "sqlite" in db_url:
            connect_args = {"check_same_thread": False}
        _engine_cache[db_url] = create_engine(db_url, connect_args=connect_args,
                                               pool_pre_ping=True)
    return _engine_cache[db_url]


def get_session_factory(engine=None):
    """Create a sessionmaker for the given engine."""
    if engine is None:
        engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Default Session Factory
SessionLocal = get_session_factory()


def init_db(engine=None):
    """Create all tables and perform minor migrations."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    # Minor migrations for SQLite
    try:
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("settings")]
        
        with engine.connect() as conn:
            if "profile_avatar" not in columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN profile_avatar TEXT"))
            if "extra_config" not in columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN extra_config JSON"))
            conn.commit()
    except Exception as e:
        # If it fails (e.g. column already exists or table doesn't exist), just ignore
        pass


def migrate_db(new_url: str) -> tuple:
    """
    Attempt to connect to a new database and create the schema.
    Returns (success: bool, message: str)
    """
    try:
        engine = get_engine(new_url)
        Base.metadata.create_all(bind=engine)
        # Verify tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected = {"users", "sessions", "engagement_logs", "settings", "training_data"}
        if expected.issubset(set(tables)):
            return True, f"Connected! Tables found: {', '.join(tables)}"
        return True, f"Connected with partial schema. Tables: {', '.join(tables)}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def get_db(db_url=None):
    """Get a database session (generator)."""
    engine = get_engine(db_url)
    Session = get_session_factory(engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


# ─── Helper Functions ─────────────────────────────────────────────────────────

def get_user_sessions(db, user_id: int, status: Optional[str] = None):
    """Get all sessions for a user, optionally filtered by status."""
    query = db.query(StudySession).filter(StudySession.user_id == user_id)
    if status:
        query = query.filter(StudySession.status == status)
    return query.order_by(StudySession.start_time.desc()).all()


def get_session_logs(db, session_id: int):
    """Get all engagement logs for a session."""
    return (db.query(EngagementLog)
            .filter(EngagementLog.session_id == session_id)
            .order_by(EngagementLog.timestamp)
            .all())


def save_engagement_log(db, session_id: int, metrics: dict):
    """Save a single engagement log entry."""
    log = EngagementLog(
        session_id=session_id,
        ear_value=metrics.get("ear", 0.0),
        head_pitch=metrics.get("pitch", 0.0),
        head_yaw=metrics.get("yaw", 0.0),
        head_roll=metrics.get("roll", 0.0),
        gaze_score=metrics.get("gaze_score", 1.0),
        expression_score=metrics.get("expression_score", 1.0),
        presence_score=metrics.get("presence_score", 1.0),
        engagement_score=metrics.get("engagement_score", 0.0),
        is_distracted=metrics.get("is_distracted", False),
        is_spoof=metrics.get("is_spoof", False),
    )
    db.add(log)
    db.commit()
    return log


def get_training_data(db, user_id: int):
    """Get all training data for a user."""
    return (db.query(TrainingData)
            .filter(TrainingData.user_id == user_id)
            .order_by(TrainingData.timestamp)
            .all())
