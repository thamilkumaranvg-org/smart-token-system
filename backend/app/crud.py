import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from . import models, schemas

def get_start_of_day():
    now = datetime.datetime.utcnow()
    return datetime.datetime(now.year, now.month, now.day, 0, 0, 0)

def generate_token_number(db: Session, service_code: str, office_type: str) -> str:
    start_of_day = get_start_of_day()
    
    # Count tokens created today for this specific service code and office
    count = db.query(func.count(models.Token.id)).filter(
        models.Token.service_code == service_code,
        models.Token.office_type == office_type,
        models.Token.created_at >= start_of_day
    ).scalar()
    
    next_num = (count or 0) + 1
    return f"{service_code}-{next_num:02d}"

def create_token(db: Session, token_in: schemas.TokenCreate, office_type: str) -> models.Token:
    if token_in.customer_email:
        # Check for active token (PENDING, SERVING, or HOLD) for this user in this office
        active_token = db.query(models.Token).filter(
            models.Token.office_type == office_type,
            models.Token.customer_email == token_in.customer_email,
            models.Token.status.in_(["PENDING", "SERVING", "HOLD"])
        ).first()
        if active_token:
            raise ValueError("You already have an active token in this center.")

    token_number = generate_token_number(db, token_in.service_code, office_type)
    
    db_token = models.Token(
        token_number=token_number,
        service_code=token_in.service_code,
        service_name=token_in.service_name,
        customer_info=token_in.customer_info,
        office_type=office_type,
        customer_email=token_in.customer_email,
        status="PENDING"
    )
    
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def get_token(db: Session, token_id: int) -> Optional[models.Token]:
    return db.query(models.Token).filter(models.Token.id == token_id).first()

def get_pending_tokens(db: Session, office_type: str) -> List[models.Token]:
    start_of_day = get_start_of_day()
    return db.query(models.Token).filter(
        models.Token.status == "PENDING",
        models.Token.office_type == office_type,
        models.Token.created_at >= start_of_day
    ).order_by(models.Token.created_at.asc()).all()

def call_next_token(db: Session, counter_number: int, office_type: str, service_codes: List[str] = None) -> Optional[models.Token]:
    start_of_day = get_start_of_day()
    
    # Auto-complete any active tokens on this counter for this office
    active_current = db.query(models.Token).filter(
        models.Token.counter_assigned == counter_number,
        models.Token.status == "SERVING",
        models.Token.office_type == office_type,
        models.Token.created_at >= start_of_day
    ).first()
    if active_current:
        active_current.status = "COMPLETED"
        active_current.completed_at = datetime.datetime.utcnow()
        # Redact customer mobile number for privacy once served
        active_current.customer_info = None
    
    query = db.query(models.Token).filter(
        models.Token.status == "PENDING",
        models.Token.office_type == office_type,
        models.Token.created_at >= start_of_day
    )
    
    if service_codes:
        query = query.filter(models.Token.service_code.in_(service_codes))
        
    next_token = query.order_by(models.Token.created_at.asc()).first()
    
    if next_token:
        next_token.status = "SERVING"
        next_token.counter_assigned = counter_number
        next_token.served_at = datetime.datetime.utcnow()
        
        # Link to counter in db
        counter = db.query(models.Counter).filter(
            models.Counter.counter_number == counter_number,
            models.Counter.office_type == office_type
        ).first()
        if counter:
            counter.current_token_id = next_token.id
            
        db.commit()
        db.refresh(next_token)
        
    return next_token

def update_token_status(db: Session, token_id: int, status: str) -> Optional[models.Token]:
    db_token = get_token(db, token_id)
    if db_token:
        db_token.status = status
        if status in ["COMPLETED", "MISSED"]:
            db_token.completed_at = datetime.datetime.utcnow()
            # Also clear the counter association if active
            counter = db.query(models.Counter).filter(
                models.Counter.current_token_id == token_id
            ).first()
            if counter:
                counter.current_token_id = None
            # Redact customer mobile number for privacy once served
            db_token.customer_info = None
        db.commit()
        db.refresh(db_token)
    return db_token

def get_active_tokens(db: Session, office_type: str) -> List[models.Token]:
    start_of_day = get_start_of_day()
    return db.query(models.Token).filter(
        models.Token.status == "SERVING",
        models.Token.office_type == office_type,
        models.Token.created_at >= start_of_day
    ).all()

def get_admin_metrics(db: Session, office_type: str):
    start_of_day = get_start_of_day()
    
    total = db.query(func.count(models.Token.id)).filter(models.Token.office_type == office_type, models.Token.created_at >= start_of_day).scalar() or 0
    completed = db.query(func.count(models.Token.id)).filter(models.Token.status == "COMPLETED", models.Token.office_type == office_type, models.Token.created_at >= start_of_day).scalar() or 0
    missed = db.query(func.count(models.Token.id)).filter(models.Token.status == "MISSED", models.Token.office_type == office_type, models.Token.created_at >= start_of_day).scalar() or 0
    serving = db.query(func.count(models.Token.id)).filter(models.Token.status == "SERVING", models.Token.office_type == office_type, models.Token.created_at >= start_of_day).scalar() or 0
    pending = db.query(func.count(models.Token.id)).filter(models.Token.status == "PENDING", models.Token.office_type == office_type, models.Token.created_at >= start_of_day).scalar() or 0
    
    completed_tokens = db.query(models.Token).filter(
        models.Token.status == "COMPLETED",
        models.Token.office_type == office_type,
        models.Token.created_at >= start_of_day,
        models.Token.served_at.isnot(None)
    ).all()
    
    avg_wait_sec = 0
    if completed_tokens:
        total_wait = sum((t.served_at - t.created_at).total_seconds() for t in completed_tokens)
        avg_wait_sec = total_wait / len(completed_tokens)
        
    return {
        "total_tokens": total,
        "completed_count": completed,
        "missed_count": missed,
        "serving_count": serving,
        "pending_count": pending,
        "avg_wait_minutes": round(avg_wait_sec / 60, 1)
    }

def get_counters(db: Session, office_type: str) -> List[models.Counter]:
    counters = db.query(models.Counter).filter(models.Counter.office_type == office_type).order_by(models.Counter.counter_number.asc()).all()
    # Seed default counters (1, 2, 3) for this center if none exist
    if not counters:
        for num in [1, 2, 3]:
            new_c = models.Counter(counter_number=num, is_active=True, office_type=office_type)
            db.add(new_c)
        db.commit()
        counters = db.query(models.Counter).filter(models.Counter.office_type == office_type).order_by(models.Counter.counter_number.asc()).all()
    return counters

def create_counter(db: Session, counter_number: int, office_type: str) -> models.Counter:
    # Check if exists in this office
    existing = db.query(models.Counter).filter(
        models.Counter.counter_number == counter_number,
        models.Counter.office_type == office_type
    ).first()
    if existing:
        return existing
        
    db_counter = models.Counter(counter_number=counter_number, is_active=True, office_type=office_type)
    db.add(db_counter)
    db.commit()
    db.refresh(db_counter)
    return db_counter

def update_counter_status(db: Session, counter_id: int, is_active: bool) -> Optional[models.Counter]:
    counter = db.query(models.Counter).filter(models.Counter.id == counter_id).first()
    if counter:
        counter.is_active = is_active
        db.commit()
        db.refresh(counter)
    return counter

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user_in: schemas.UserCreate, role: str = "customer") -> models.User:
    from .database import get_db_session
    
    # Create the user in the primary center database
    db_user = models.User(
        email=user_in.email,
        password=user_in.password,
        role=role,
        office_type=user_in.office_type
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # If customer, replicate account credentials to the other 3 databases for unified login
    if role == "customer":
        offices = ["BANK", "ESEVAI", "POST_OFFICE", "MUNICIPAL"]
        for office in offices:
            if office != user_in.office_type:
                other_db = get_db_session(office)
                try:
                    existing = other_db.query(models.User).filter(models.User.email == user_in.email).first()
                    if not existing:
                        new_user = models.User(
                            email=user_in.email,
                            password=user_in.password,
                            role=role,
                            office_type=office
                        )
                        other_db.add(new_user)
                        other_db.commit()
                except Exception as e:
                    other_db.rollback()
                    print(f"[REPLICATION WARNING] Failed to seed user to {office}:", e)
                finally:
                    other_db.close()
                    
    return db_user

def authenticate_user(db: Session, login_in: schemas.UserLogin) -> Optional[models.User]:
    user = get_user_by_email(db, login_in.email)
    # Match password
    if user and user.password == login_in.password:
        # Customers can log into any center
        if user.role == "customer":
            return user
        # For staff and TV, verify the office type matches
        if user.office_type == login_in.office_type or user.office_type == "ALL":
            return user
    return None

def seed_users(db: Session, office_type: str):
    passwords = {
        "BANK": {"admin": "AdminOfBank", "agent": "AgentOfBank", "tv": "TelevisionOfBank"},
        "ESEVAI": {"admin": "AdminOfesevai01", "agent": "AgentOfEsevai", "tv": "TelevisionOfEsevai"},
        "POST_OFFICE": {"admin": "AdminOfPostOffice", "agent": "AgentOfPostOffice", "tv": "TelevisionOfPostOffice"},
        "MUNICIPAL": {"admin": "AdminOfMunicipal", "agent": "AgentOfMunicipal", "tv": "TelevisionOfMunicipal"}
    }
    
    if office_type not in passwords:
        return
        
    office_clean = office_type.replace("_", "")
    if office_type == "POST_OFFICE":
        office_clean = "PostOffice"
    elif office_type == "ESEVAI":
        office_clean = "Esevai"
    elif office_type == "MUNICIPAL":
        office_clean = "Municipal"
    elif office_type == "BANK":
        office_clean = "Bank"
        
    admin_email = f"AdminOf{office_clean}@gmail.com"
    agent_email = f"AgentOf{office_clean}@gmail.com"
    tv_email = f"TelevisionOf{office_clean}@gmail.com"
    
    # Check and seed Admin
    if not db.query(models.User).filter(models.User.email == admin_email).first():
        db.add(models.User(email=admin_email, password=passwords[office_type]["admin"], role="admin", office_type=office_type))
        
    # Check and seed Agent
    if not db.query(models.User).filter(models.User.email == agent_email).first():
        db.add(models.User(email=agent_email, password=passwords[office_type]["agent"], role="agent", office_type=office_type))
        
    # Check and seed TV
    if not db.query(models.User).filter(models.User.email == tv_email).first():
        db.add(models.User(email=tv_email, password=passwords[office_type]["tv"], role="tv", office_type=office_type))
        
    db.commit()

