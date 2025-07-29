from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from core.base import Base, SoftDelete
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class UserDashboard(Base, SoftDelete, table=True):
    user_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(
            PG_UUID(as_uuid=True),  
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    index_name: str = Field(nullable=False)
    index_value: str = Field(nullable=False)
    last_update: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class User(Base, SoftDelete, table=True):
    email: str = Field(index=True, nullable=False, unique=True)
    password: str = Field(nullable=False)
    name: Optional[str]
    role: str = Field(default="") #superadmin, admin

