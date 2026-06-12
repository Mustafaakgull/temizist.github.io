from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.database import get_db
from database.models import Session, Transaction
from schemas.schemas import PiActionResponse, WeightRequest, PlasticPassedRequest, PaperPassedRequest
from services.ai_inference import process_image_mock
from services.point_calculator import calculate_points_by_item, calculate_points_by_weight

router = APIRouter(prefix="/api/pi", tags=["Raspberry Pi"])


@router.get("/active-session/{machine_id}", response_model=PiActionResponse)
async def get_active_session(machine_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Session).where(
            Session.machine_id == machine_id,
            Session.is_active == True,
        )
    )
    active_session = result.scalars().first()
    if active_session:
        return PiActionResponse(
            status="active",
            action="start_session",
            message=f"Active session. Type: {active_session.waste_type}",
            session_id=active_session.id,
            waste_type=active_session.waste_type or "plastic",
            plastic_bottle_count=active_session.plastic_bottle_count or 0,

            paper_count=active_session.paper_count or 0,
        )
    return PiActionResponse(
        status="idle",
        action="do_nothing",
        message="No active session for this machine.",
    )


@router.post("/detect", response_model=PiActionResponse)
async def detect_waste(
    session_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    session_record = await db.get(Session, session_id)
    if not session_record or not session_record.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive session")

    image_bytes = await file.read()
    waste_type = await process_image_mock(image_bytes)
    session_kind = (session_record.waste_type or "plastic").lower()

    if waste_type == "plastic":
        if session_kind != "plastic":
            return PiActionResponse(
                status="reject",
                action="do_nothing",
                message="Plastik tespit edildi ancak aktif oturum kağıt QR ile açıldı.",
                session_id=session_id,
            )
        return PiActionResponse(
            status="plastic",
            action="run_conveyor",
            message="Plastik onaylandı. Bant çalıştır; şişe geçince sayaç artırılacak.",
            session_id=session_id,
            waste_type="plastic",
            plastic_bottle_count=session_record.plastic_bottle_count or 0,
        )

    if waste_type == "paper":
        if session_kind != "paper":
            return PiActionResponse(
                status="reject",
                action="do_nothing",
                message="Kağıt tespit edildi ancak aktif oturum plastik QR ile açıldı.",
                session_id=session_id,
            )
        return PiActionResponse(
            status="paper",
            action="open_doors",
            message="Kağıt onaylandı. Kapaklar açılıyor.",
            session_id=session_id,
            waste_type="paper",
        )

    return PiActionResponse(
        status="reject",
        action="do_nothing",
        message="Unknown or rejected item.",
        session_id=session_id,
    )


@router.post("/plastic-passed", response_model=PiActionResponse)
async def plastic_bottle_passed(
    req: PlasticPassedRequest, db: AsyncSession = Depends(get_db)
):
    """Şişe sensöre çok yakın geçti — session şişe sayısı +1 ve puan."""
    session_record = await db.get(Session, req.session_id)
    if not session_record or not session_record.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive session")

    if (session_record.waste_type or "plastic").lower() != "plastic":
        raise HTTPException(status_code=400, detail="Active session is not plastic")

    points = calculate_points_by_item("plastic")
    transaction = Transaction(
        session_id=req.session_id,
        waste_type="plastic",
        amount=1.0,
        earned_points=points,
    )
    db.add(transaction)
    session_record.plastic_bottle_count = (session_record.plastic_bottle_count or 0) + 1
    session_record.total_earned_points += points
    await db.commit()
    await db.refresh(session_record)

    return PiActionResponse(
        status="success",
        action="bottle_counted",
        message=f"Şişe sayıldı. Toplam: {session_record.plastic_bottle_count}",
        session_id=req.session_id,
        waste_type="plastic",
        plastic_bottle_count=session_record.plastic_bottle_count,
    )


@router.post("/paper-passed", response_model=PiActionResponse)
async def paper_item_passed(
    req: PaperPassedRequest, db: AsyncSession = Depends(get_db)
):
    """Kağıt parçası algılandı — session toplam ağırlığı yerine adet başına puan ver."""
    session_record = await db.get(Session, req.session_id)
    if not session_record or not session_record.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive session")

    if (session_record.waste_type or "paper").lower() != "paper":
        raise HTTPException(status_code=400, detail="Active session is not paper")

    points = calculate_points_by_item("paper")
    transaction = Transaction(
        session_id=req.session_id,
        waste_type="paper",
        amount=1.0,  # 1 adet kağıt
        earned_points=points,
    )
    db.add(transaction)
    
    # Paper için aslında weight kaydediyorduk, ama adet üzerinden gidiyoruz. 
    # Şişe sayısı yerine puanı doğrudan toplam puana ekleyelim.
    session_record.total_earned_points += points
    session_record.paper_count = (session_record.paper_count or 0) + 1
    await db.commit()
    await db.refresh(session_record)

    return PiActionResponse(
        status="success",
        action="paper_counted",
        message=f"Kağıt sayıldı. +{points} Puan. Toplam Puan: {session_record.total_earned_points}",
        session_id=req.session_id,
        waste_type="paper",
        paper_count=session_record.paper_count,
    )

