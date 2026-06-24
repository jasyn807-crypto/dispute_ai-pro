from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class NegativeItemSchema(BaseModel):
    id: str
    creditor: str
    amount: float
    bureau: str
    status: str

    model_config = ConfigDict(from_attributes=True)

class ParserUploadResponse(BaseModel):
    report_id: str
    negative_items: List[NegativeItemSchema]

class ReportResponse(BaseModel):
    report_id: str
    filename: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
