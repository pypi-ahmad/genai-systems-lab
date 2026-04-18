"""SQLAlchemy models for shared API auth and run history."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    """Authenticated API user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sessions: Mapped[list["RunSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    runs: Mapped[list["Run"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RunSession(Base):
    """Persisted session memory across related runs."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    memory_text: Mapped[str] = mapped_column("memory", Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="sessions")
    runs: Mapped[list["Run"]] = relationship(back_populates="session")


class Run(Base):
    """Persisted project execution for a user."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id"), index=True, nullable=True, default=None)
    project: Mapped[str] = mapped_column(String(120), index=True)
    input_text: Mapped[str] = mapped_column("input", Text)
    output_text: Mapped[str] = mapped_column("output", Text)
    memory_text: Mapped[str] = mapped_column("memory", Text, default="[]")
    timeline_text: Mapped[str] = mapped_column("timeline", Text, default="[]")
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column("confidence", Float, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True, default=None)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    # Token / cost accounting per DA-6 (null-tolerant so legacy rows keep working).
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    # The model actually used, which may differ from the requested one when Gemini
    # falls back from pro → flash.  DA-5.
    model_used: Mapped[str | None] = mapped_column(String(120), nullable=True, default=None)

    session: Mapped[RunSession | None] = relationship(back_populates="runs")
    user: Mapped[User] = relationship(back_populates="runs")

    __table_args__ = (
        # /history lists by user, most-recent first.
        Index("ix_runs_user_timestamp", "user_id", "timestamp"),
        # /run/{id} filters on (id, user_id); id is PK so no extra index needed.
        # Per-project drill-downs are cheap if project has a per-timestamp index.
        Index("ix_runs_project_timestamp", "project", "timestamp"),
    )


class OperationalMetric(Base):
    """Durable execution telemetry for project runs."""

    __tablename__ = "operational_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project: Mapped[str] = mapped_column(String(120), index=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column("confidence", Float, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        # /metrics/time filters on (project, timestamp >= cutoff).
        Index("ix_ops_metrics_project_timestamp", "project", "timestamp"),
    )