import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class CreditReport(Base):
    __tablename__ = "credit_reports"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="parsed", nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=True)

    client: Mapped["Client"] = relationship("Client", back_populates="credit_reports")
    dispute_items: Mapped[list["DisputeItem"]] = relationship(
        "DisputeItem", 
        back_populates="credit_report", 
        cascade="all, delete-orphan"
    )
