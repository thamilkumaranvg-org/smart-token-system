import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_number = Column(String, index=True, nullable=False) # e.g., 'AC-01'
    service_code = Column(String, index=True, nullable=False) # e.g., 'AC', 'CS'
    service_name = Column(String, nullable=False) # e.g., 'Account Creation'
    customer_info = Column(String, nullable=True) # Optional phone/name
    status = Column(String, default="PENDING") # PENDING, SERVING, COMPLETED, MISSED, HOLD
    counter_assigned = Column(Integer, nullable=True) # Which counter is serving this
    office_type = Column(String, index=True, nullable=False, default="BANK")
    customer_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    served_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

class Counter(Base):
    __tablename__ = "counters"

    id = Column(Integer, primary_key=True, index=True)
    counter_number = Column(Integer, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    office_type = Column(String, index=True, nullable=False, default="BANK")
    current_token_id = Column(Integer, ForeignKey("tokens.id"), nullable=True)

    current_token = relationship("Token", foreign_keys=[current_token_id])

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False) # Plain text for prototype/simplicity
    role = Column(String, nullable=False) # admin, agent, tv, customer
    office_type = Column(String, nullable=False) # BANK, ESEVAI, POST_OFFICE, MUNICIPAL
