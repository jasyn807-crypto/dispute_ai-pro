from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Boolean, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserRole(str, PyEnum):
    AGENCY = "agency"
    CLIENT = "client"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # "agency" or "client"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # One-to-one relationships
    agency_profile: Mapped["Agency"] = relationship(
        "Agency", 
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
    client_profile: Mapped["Client"] = relationship(
        "Client", 
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
