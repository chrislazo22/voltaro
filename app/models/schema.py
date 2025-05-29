"""
Database models for OCPP backend.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ChargePoint(Base):
    """
    Represents an EV charging station (charge point).
    """

    __tablename__ = "charge_points"

    id: Mapped[str] = mapped_column(
        String(50), primary_key=True
    )  # Charge point identifier

    # Required BootNotification fields
    vendor: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # chargePointVendor (max 20)
    model: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # chargePointModel (max 20)

    # Optional BootNotification fields
    charge_point_serial_number: Mapped[Optional[str]] = mapped_column(
        String(25)
    )  # max 25
    charge_box_serial_number: Mapped[Optional[str]] = mapped_column(
        String(25)
    )  # max 25
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50))  # max 50
    iccid: Mapped[Optional[str]] = mapped_column(String(20))  # max 20
    imsi: Mapped[Optional[str]] = mapped_column(String(20))  # max 20
    meter_type: Mapped[Optional[str]] = mapped_column(String(25))  # max 25
    meter_serial_number: Mapped[Optional[str]] = mapped_column(String(25))  # max 25

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default="Unknown"
    )  # Available, Occupied, Faulted, etc.
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)

    # Boot notification data
    boot_reason: Mapped[Optional[str]] = mapped_column(String(50))
    boot_status: Mapped[Optional[str]] = mapped_column(
        String(10), default="Accepted"
    )  # Accepted, Pending, Rejected

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="charge_point"
    )


class IdTag(Base):
    """
    Represents an RFID tag or other identifier for authorization.
    """

    __tablename__ = "id_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )  # The actual tag value
    status: Mapped[str] = mapped_column(
        String(20), default="Accepted"
    )  # Accepted, Blocked, Expired, Invalid

    # Optional user information
    user_name: Mapped[Optional[str]] = mapped_column(String(100))
    user_email: Mapped[Optional[str]] = mapped_column(String(100))

    # Expiry and limits
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    parent_id_tag: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # For hierarchical tags

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="id_tag")


class Session(Base):
    """
    Represents a charging session from start to stop.
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    # Foreign keys
    charge_point_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("charge_points.id")
    )
    id_tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("id_tags.id"))

    # Session details
    connector_id: Mapped[int] = mapped_column(
        Integer
    )  # Which connector on the charge point
    meter_start: Mapped[int] = mapped_column(Integer)  # Starting meter value in Wh
    meter_stop: Mapped[Optional[int]] = mapped_column(
        Integer
    )  # Ending meter value in Wh

    # Timestamps
    start_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    stop_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Session status
    status: Mapped[str] = mapped_column(
        String(20), default="Active"
    )  # Active, Completed, Stopped
    stop_reason: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # Local, Remote, EmergencyStop, etc.

    # Energy and cost (calculated fields)
    energy_consumed: Mapped[Optional[float]] = mapped_column(Float)  # kWh
    cost: Mapped[Optional[float]] = mapped_column(Float)  # Total cost

    # Additional data
    reservation_id: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow
    )

    # Relationships
    charge_point: Mapped["ChargePoint"] = relationship(
        "ChargePoint", back_populates="sessions"
    )
    id_tag: Mapped["IdTag"] = relationship("IdTag", back_populates="sessions")
    meter_values: Mapped[list["MeterValue"]] = relationship(
        "MeterValue", back_populates="session"
    )


class MeterValue(Base):
    """
    Represents meter readings during a charging session.
    """

    __tablename__ = "meter_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"))

    # Meter data
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    value: Mapped[float] = mapped_column(Float)  # The actual meter reading
    unit: Mapped[str] = mapped_column(String(10), default="Wh")  # Wh, kWh, A, V, etc.
    measurand: Mapped[str] = mapped_column(
        String(50), default="Energy.Active.Import.Register"
    )
    phase: Mapped[Optional[str]] = mapped_column(String(10))  # L1, L2, L3, N
    location: Mapped[str] = mapped_column(
        String(20), default="Outlet"
    )  # Cable, EV, Inlet, Outlet
    context: Mapped[str] = mapped_column(
        String(20), default="Sample.Periodic"
    )  # Sample.Clock, Sample.Periodic, etc.

    # Additional OCPP fields
    format: Mapped[str] = mapped_column(String(10), default="Raw")  # Raw, SignedData

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="meter_values")


class ConnectorStatus(Base):
    """
    Represents the current and historical status of charge point connectors.
    """

    __tablename__ = "connector_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    charge_point_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("charge_points.id")
    )

    # Required StatusNotification fields
    connector_id: Mapped[int] = mapped_column(
        Integer
    )  # 0 for charge point, >0 for connectors
    status: Mapped[str] = mapped_column(
        String(20)
    )  # Available, Preparing, Charging, etc.
    error_code: Mapped[str] = mapped_column(String(30))  # NoError, InternalError, etc.

    # Optional StatusNotification fields
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    info: Mapped[Optional[str]] = mapped_column(String(50))  # Additional information
    vendor_id: Mapped[Optional[str]] = mapped_column(String(255))  # Vendor identifier
    vendor_error_code: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # Vendor-specific error

    # Tracking fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    charge_point: Mapped["ChargePoint"] = relationship("ChargePoint")
