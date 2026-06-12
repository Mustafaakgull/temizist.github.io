from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    total_points = Column(Integer, default=0)
    
    sessions = relationship("Session", back_populates="user")

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String)
    status = Column(String, default="IDLE") # IDLE, BUSY
    
    sessions = relationship("Session", back_populates="machine")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_earned_points = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    waste_type = Column(String, default="plastic")  # plastic | paper (QR)
    plastic_bottle_count = Column(Integer, default=0)
    paper_count = Column(Integer, default=0)  # Yeni sistem: Kağıt adet

    user = relationship("User", back_populates="sessions")
    machine = relationship("Machine", back_populates="sessions")
    transactions = relationship("Transaction", back_populates="session")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    waste_type = Column(String) # plastic, paper vs
    amount = Column(Float) # weight or quantity
    earned_points = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="transactions")
