from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StartSessionRequest(BaseModel):
    user_id: str
    machine_id: int
    waste_type: str = "plastic"  # plastic | paper from QR

class EndSessionRequest(BaseModel):
    session_id: int

class SessionResponse(BaseModel):
    session_id: int
    user_id: str
    machine_id: int
    status: str
    message: str
    total_earned_points: Optional[int] = 0
    waste_type: Optional[str] = "plastic"
    plastic_bottle_count: Optional[int] = 0
    paper_count: Optional[int] = 0

class WeightRequest(BaseModel):
    session_id: int
    weight_grams: float

class PlasticPassedRequest(BaseModel):
    session_id: int

class PaperPassedRequest(BaseModel):
    session_id: int

class PiActionResponse(BaseModel):
    status: str
    action: str
    message: Optional[str] = None
    session_id: Optional[int] = None
    waste_type: Optional[str] = None
    plastic_bottle_count: Optional[int] = None
    paper_count: Optional[int] = None
