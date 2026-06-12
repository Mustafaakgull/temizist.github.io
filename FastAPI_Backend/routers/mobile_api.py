from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from database.database import get_db
from database.models import Machine, Session, User
from schemas.schemas import StartSessionRequest, EndSessionRequest, SessionResponse

router = APIRouter(prefix="/api/mobile", tags=["Mobile"])

@router.post("/start-session", response_model=SessionResponse)
async def start_session(req: StartSessionRequest, db: AsyncSession = Depends(get_db)):
    # Check if machine exists, if not, auto-create it for seamless n8n integration
    machine = await db.get(Machine, req.machine_id)
    if not machine:
        machine = Machine(id=req.machine_id, location="Auto Provisioned", status="IDLE")
        db.add(machine)
        await db.commit()
        await db.refresh(machine)
        
    # Self-healing: auto-close any existing active sessions for this machine or user
    stale_sessions_query = await db.execute(
        select(Session).where(
            (Session.user_id == req.user_id) | (Session.machine_id == req.machine_id)
        ).where(Session.is_active == True)
    )
    stale_sessions = stale_sessions_query.scalars().all()
    for s in stale_sessions:
        s.is_active = False
        s.end_time = datetime.utcnow()
    
    # Force reset machine to IDLE to clear any stuck BUSY statuses
    machine.status = "IDLE"
    await db.commit()

    # Check if user exists, if not, auto-create it
    user = await db.get(User, req.user_id)
    if not user:
        user = User(id=req.user_id, username=f"user_{req.user_id}", email=f"user_{req.user_id}@temizist.com", total_points=0)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Update machine status
    machine.status = "BUSY"
    
    waste = (req.waste_type or "plastic").lower()
    if waste not in ("plastic", "paper"):
        waste = "plastic"

    new_session = Session(
        user_id=req.user_id,
        machine_id=req.machine_id,
        waste_type=waste,
        plastic_bottle_count=0,
        paper_count=0,
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return SessionResponse(
        session_id=new_session.id,
        user_id=new_session.user_id,
        machine_id=new_session.machine_id,
        status="success",
        message="Session started successfully",
        total_earned_points=0,
        waste_type=new_session.waste_type,
        plastic_bottle_count=0,
        paper_count=0,
    )

@router.post("/end-session", response_model=SessionResponse)
async def end_session(req: EndSessionRequest, db: AsyncSession = Depends(get_db)):
    # Get session
    session_record = await db.get(Session, req.session_id)
    if not session_record or not session_record.is_active:
        raise HTTPException(status_code=404, detail="Active session not found")

    # Update session
    session_record.is_active = False
    session_record.end_time = datetime.utcnow()
    
    # Get associated machine and set to IDLE
    machine = await db.get(Machine, session_record.machine_id)
    if machine:
        machine.status = "IDLE"

    # Add earned points to user total
    user = await db.get(User, session_record.user_id)
    if user:
        user.total_points += session_record.total_earned_points

    await db.commit()
    await db.refresh(session_record)

    return SessionResponse(
        session_id=session_record.id,
        user_id=session_record.user_id,
        machine_id=session_record.machine_id,
        status="success",
        message=f"Session ended. Total points earned: {session_record.total_earned_points}",
        total_earned_points=session_record.total_earned_points,
        waste_type=session_record.waste_type,
        plastic_bottle_count=session_record.plastic_bottle_count or 0,
        paper_count=session_record.paper_count or 0,
    )

@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    session_record = await db.get(Session, session_id)
    if not session_record:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return SessionResponse(
        session_id=session_record.id,
        user_id=session_record.user_id,
        machine_id=session_record.machine_id,
        status="active" if session_record.is_active else "ended",
        message="Session details retrieved",
        total_earned_points=session_record.total_earned_points,
        waste_type=session_record.waste_type,
        plastic_bottle_count=session_record.plastic_bottle_count or 0,
        paper_count=session_record.paper_count or 0,
    )

