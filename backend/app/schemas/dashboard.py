"""
Pydantic schemas for dashboard endpoints.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional


class OverviewStats(BaseModel):
    total_clients: int
    active_clients: int
    total_disputes: int
    active_disputes: int
    resolved_disputes: int
    success_rate: float
    letters_generated: int
    letters_mailed: int
    estimated_monthly_revenue: float


class PipelineStage(BaseModel):
    status: str
    count: int


class PipelineResponse(BaseModel):
    pipeline: List[PipelineStage]
    total: int


class DisputeMetrics(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_negative_type: Dict[str, int]
    success_rate: float
    avg_resolution_days: Optional[float] = None
