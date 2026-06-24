from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class DisputeLetter(Base):
    __tablename__ = "dispute_letters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    bureau: Mapped[str] = mapped_column(String(50), nullable=False)  # "Equifax", "Experian", or "TransUnion"
    letter_content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)  # "draft", "mailed", "accepted", "rejected"
    mail_tracking_id: Mapped[str] = mapped_column(String(100), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    dispute_items: Mapped[list["DisputeItem"]] = relationship("DisputeItem", back_populates="dispute_letter")

class DisputeItem(Base):
    __tablename__ = "dispute_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    dispute_letter_id: Mapped[int] = mapped_column(ForeignKey("dispute_letters.id", ondelete="SET NULL"), nullable=True)
    credit_report_id: Mapped[str] = mapped_column(ForeignKey("credit_reports.id", ondelete="CASCADE"), nullable=True)
    bureau: Mapped[str] = mapped_column(String(50), nullable=False)  # 'Equifax', 'Experian', 'TransUnion'
    creditor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_number: Mapped[str] = mapped_column(String(100), nullable=True)
    balance: Mapped[float] = mapped_column(Float, nullable=True)
    negative_type: Mapped[str] = mapped_column(String(100), nullable=True)  # 'late_payment', 'collection', 'charge_off'
    dispute_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # 'pending', 'deleted', 'verified' (or 'negative', 'disputed', etc.)
    disputed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    dispute_letter: Mapped["DisputeLetter"] = relationship("DisputeLetter", back_populates="dispute_items")
    credit_report: Mapped["CreditReport"] = relationship("CreditReport", back_populates="dispute_items")
