"""
REST API routes for the Voltaro dashboard frontend.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import ChargePoint, Session, IdTag, ConnectorStatus
from app.central_system import CentralSystem
from app.connection_manager import is_charge_point_connected


# Pydantic models for API requests/responses
class ChargePointCreate(BaseModel):
    id: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    charge_point_serial_number: Optional[str] = None
    charge_box_serial_number: Optional[str] = None
    firmware_version: Optional[str] = None


class ChargePointResponse(BaseModel):
    id: str
    vendor: Optional[str]
    model: Optional[str]
    status: str
    is_online: bool
    last_seen: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: int
    transaction_id: int
    charge_point_id: str
    connector_id: int
    status: str
    start_timestamp: datetime
    stop_timestamp: Optional[datetime]
    energy_consumed: Optional[float]
    cost: Optional[float]

    class Config:
        from_attributes = True


class RemoteStartRequest(BaseModel):
    id_tag: str
    connector_id: Optional[int] = None


class RemoteStopRequest(BaseModel):
    transaction_id: int


class DashboardStats(BaseModel):
    total_charge_points: int
    online_charge_points: int
    active_sessions: int
    total_energy_consumed: float
    total_fees_collected: float


# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Create router
router = APIRouter(prefix="/api", tags=["voltaro-api"])


@router.get("/charge-points", response_model=List[ChargePointResponse])
async def get_charge_points(db: AsyncSession = Depends(get_db)):
    """Get all charge points with their current status."""
    try:
        result = await db.execute(
            select(ChargePoint).order_by(ChargePoint.created_at.desc())
        )
        charge_points = result.scalars().all()

        # Update connection status from in-memory connections
        for cp in charge_points:
            cp.is_online = is_charge_point_connected(cp.id)

        return charge_points
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch charge points: {str(e)}"
        )


@router.post("/charge-points", response_model=ChargePointResponse)
async def create_charge_point(
    charge_point: ChargePointCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new charge point."""
    try:
        # Check if charge point already exists
        existing = await db.get(ChargePoint, charge_point.id)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Charge point with ID '{charge_point.id}' already exists",
            )

        # Create new charge point
        new_cp = ChargePoint(
            id=charge_point.id,
            vendor=charge_point.vendor,
            model=charge_point.model,
            charge_point_serial_number=charge_point.charge_point_serial_number,
            charge_box_serial_number=charge_point.charge_box_serial_number,
            firmware_version=charge_point.firmware_version,
            status="Unknown",
            is_online=False,
            boot_status="Pending",
        )

        db.add(new_cp)
        await db.commit()
        await db.refresh(new_cp)

        return new_cp
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create charge point: {str(e)}"
        )


@router.get("/charge-points/{charge_point_id}", response_model=ChargePointResponse)
async def get_charge_point(charge_point_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific charge point by ID."""
    try:
        charge_point = await db.get(ChargePoint, charge_point_id)
        if not charge_point:
            raise HTTPException(status_code=404, detail="Charge point not found")

        # Update connection status
        charge_point.is_online = is_charge_point_connected(charge_point_id)

        return charge_point
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch charge point: {str(e)}"
        )


@router.post("/charge-points/{charge_point_id}/start-transaction")
async def remote_start_transaction(charge_point_id: str, request: RemoteStartRequest):
    """Start a charging transaction remotely."""
    try:
        result = await CentralSystem.remote_start_transaction(
            charge_point_id=charge_point_id,
            id_tag=request.id_tag,
            connector_id=request.connector_id,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Remote start failed")
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start transaction: {str(e)}"
        )


@router.post("/charge-points/{charge_point_id}/stop-transaction")
async def remote_stop_transaction(charge_point_id: str, request: RemoteStopRequest):
    """Stop a charging transaction remotely."""
    try:
        result = await CentralSystem.remote_stop_transaction(
            charge_point_id=charge_point_id, transaction_id=request.transaction_id
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Remote stop failed")
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop transaction: {str(e)}"
        )


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    limit: int = 50,
    charge_point_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get recent charging sessions."""
    try:
        query = select(Session).order_by(desc(Session.start_timestamp)).limit(limit)

        if charge_point_id:
            query = query.where(Session.charge_point_id == charge_point_id)

        result = await db.execute(query)
        sessions = result.scalars().all()

        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch sessions: {str(e)}"
        )


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    try:
        # Count total charge points
        cp_result = await db.execute(select(ChargePoint))
        all_charge_points = cp_result.scalars().all()
        total_charge_points = len(all_charge_points)

        # Count online charge points (check in-memory connections)
        online_count = 0
        for cp in all_charge_points:
            if is_charge_point_connected(cp.id):
                online_count += 1

        # Count active sessions
        active_sessions_result = await db.execute(
            select(Session).where(Session.status == "Active")
        )
        active_sessions = len(active_sessions_result.scalars().all())

        # Calculate total energy and fees from completed sessions
        completed_sessions_result = await db.execute(
            select(Session).where(Session.status == "Completed")
        )
        completed_sessions = completed_sessions_result.scalars().all()

        total_energy = sum(
            session.energy_consumed or 0 for session in completed_sessions
        )
        total_fees = sum(session.cost or 0 for session in completed_sessions)

        return DashboardStats(
            total_charge_points=total_charge_points,
            online_charge_points=online_count,
            active_sessions=active_sessions,
            total_energy_consumed=total_energy,
            total_fees_collected=total_fees,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch dashboard stats: {str(e)}"
        )


@router.get("/id-tags", response_model=List[dict])
async def get_id_tags(db: AsyncSession = Depends(get_db)):
    """Get all ID tags for transaction authorization."""
    try:
        result = await db.execute(
            select(IdTag)
            .where(IdTag.status == "Accepted")
            .order_by(IdTag.created_at.desc())
        )
        id_tags = result.scalars().all()

        return [
            {
                "id": tag.id,
                "tag": tag.tag,
                "user_name": tag.user_name,
                "user_email": tag.user_email,
                "status": tag.status,
            }
            for tag in id_tags
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch ID tags: {str(e)}"
        )


@router.post("/id-tags")
async def create_id_tag(
    tag: str,
    user_name: Optional[str] = None,
    user_email: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new ID tag for testing purposes."""
    try:
        # Check if tag already exists
        existing = await db.execute(select(IdTag).where(IdTag.tag == tag))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="ID tag already exists")

        new_tag = IdTag(
            tag=tag, user_name=user_name, user_email=user_email, status="Accepted"
        )

        db.add(new_tag)
        await db.commit()
        await db.refresh(new_tag)

        return {
            "id": new_tag.id,
            "tag": new_tag.tag,
            "user_name": new_tag.user_name,
            "user_email": new_tag.user_email,
            "status": new_tag.status,
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create ID tag: {str(e)}"
        )

