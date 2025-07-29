from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Boolean
from datetime import datetime, timezone
from uuid import UUID, uuid4


def utcnow():
    return datetime.now(timezone.utc)


class Base(SQLModel):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True
    )

    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=lambda: Column(DateTime(timezone=True), default=utcnow)
    )

    modified_at: datetime = Field(
        default_factory=utcnow,
        sa_column=lambda: Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    )


class SoftDelete(SQLModel):
    is_removed: bool = Field(
        default=False,
        sa_column=lambda: Column(Boolean, nullable=False)
    )
