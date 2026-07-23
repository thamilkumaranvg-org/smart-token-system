from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os

from . import models, schemas, crud
from .database import engines, get_db_dynamic
from .websocket_manager import manager

# Create database tables for all engines
try:
    for office, engine_obj in engines.items():
        models.Base.metadata.create_all(bind=engine_obj)

    # Database startup migrations and seeding for all 4 databases
    from .database import get_db_session
    from sqlalchemy import text
    for office in ["BANK", "ESEVAI", "POST_OFFICE", "MUNICIPAL"]:
        db = get_db_session(office)
        try:
            # Migrate tokens table to add office_type
            try:
                db.execute(text("SELECT office_type FROM tokens LIMIT 1"))
            except Exception:
                db.rollback()
                try:
                    db.execute(text("ALTER TABLE tokens ADD COLUMN office_type VARCHAR DEFAULT 'BANK'"))
                    db.commit()
                    print(f"Successfully migrated: Added office_type to tokens in {office}")
                except Exception as e:
                    db.rollback()
                    print(f"Migration warning (tokens) for {office}:", e)

            # Migrate tokens table to add customer_email
            try:
                db.execute(text("SELECT customer_email FROM tokens LIMIT 1"))
            except Exception:
                db.rollback()
                try:
                    db.execute(text("ALTER TABLE tokens ADD COLUMN customer_email VARCHAR"))
                    db.commit()
                    print(f"Successfully migrated: Added customer_email to tokens in {office}")
                except Exception as e:
                    db.rollback()
                    print(f"Migration warning (customer_email) for {office}:", e)
                    
            # Migrate counters table
            try:
                db.execute(text("SELECT office_type FROM counters LIMIT 1"))
            except Exception:
                db.rollback()
                try:
                    db.execute(text("ALTER TABLE counters ADD COLUMN office_type VARCHAR DEFAULT 'BANK'"))
                    db.execute(text("ALTER TABLE counters DROP CONSTRAINT IF EXISTS counters_counter_number_key"))
                    db.commit()
                    print(f"Successfully migrated: Added office_type to counters in {office} and removed constraint")
                except Exception as e:
                    db.rollback()
                    print(f"Migration warning (counters) for {office}:", e)
        
            # Drop the unique index that was created for counter_number
            try:
                db.execute(text("DROP INDEX IF EXISTS ix_counters_counter_number CASCADE"))
                db.commit()
            except Exception as e:
                db.rollback()
        
            # Seed users
            crud.seed_users(db, office)
        finally:
            db.close()
except Exception as startup_err:
    print("\n========================================================")
    print("[DATABASE STARTUP WARNING] Could not initialize database:")
    print(startup_err)
    print("The server will start, but database operations will fail.")
    print("Please verify your DATABASE_URL in backend/.env")
    print("========================================================\n")

app = FastAPI(title="Smart Token Queue Management API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend files
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Global in-memory office type configuration
active_office_type = os.getenv("OFFICE_TYPE", "BANK")

@app.post("/api/auth/login")
def auth_login(login_in: schemas.UserLogin, db: Session = Depends(get_db_dynamic)):
    user = crud.authenticate_user(db, login_in)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password for this center")
    return {
        "status": "success",
        "email": user.email,
        "role": user.role,
        "office_type": login_in.office_type if user.role == "customer" else user.office_type,
        "token": f"session_token_{user.role}_{user.email}"
    }

@app.post("/api/auth/signup")
def auth_signup(user_in: schemas.UserCreate, db: Session = Depends(get_db_dynamic)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, user_in, role="customer")
    return {
        "status": "success",
        "email": user.email,
        "role": user.role,
        "office_type": user.office_type,
        "token": f"session_token_customer_{user.email}"
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Token Queue Management API"}

@app.post("/api/tokens/generate", response_model=schemas.Token)
async def generate_token(office_type: str, token_in: schemas.TokenCreate, db: Session = Depends(get_db_dynamic)):
    try:
        db_token = crud.create_token(db=db, token_in=token_in, office_type=office_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Broadcast new token to all clients
    await manager.broadcast_json({
        "type": "NEW_TOKEN",
        "office_type": office_type,
        "data": schemas.Token.model_validate(db_token).model_dump(mode='json')
    })
    
    return db_token

@app.get("/api/tokens/active", response_model=Optional[schemas.Token])
def get_user_active_token(office_type: str, email: str, db: Session = Depends(get_db_dynamic)):
    token = db.query(models.Token).filter(
        models.Token.office_type == office_type,
        models.Token.customer_email == email,
        models.Token.status.in_(["PENDING", "SERVING", "HOLD"])
    ).first()
    return token

@app.post("/api/tokens/call-next", response_model=schemas.Token)
async def call_next_token(counter_number: int, office_type: str, service_codes: List[str] = None, db: Session = Depends(get_db_dynamic)):
    db_token = crud.call_next_token(db=db, counter_number=counter_number, office_type=office_type, service_codes=service_codes)
    if not db_token:
        raise HTTPException(status_code=404, detail="No pending tokens found")
        
    # Broadcast token call to all clients
    await manager.broadcast_json({
        "type": "CALL_TOKEN",
        "office_type": office_type,
        "data": schemas.Token.model_validate(db_token).model_dump(mode='json')
    })
    
    return db_token

@app.post("/api/tokens/{token_id}/recall", response_model=schemas.Token)
async def recall_token(token_id: int, office_type: str, db: Session = Depends(get_db_dynamic)):
    db_token = crud.get_token(db=db, token_id=token_id)
    if not db_token or db_token.status != "SERVING":
        raise HTTPException(status_code=404, detail="Token not currently active or not found")
        
    # Broadcast recall token call to all clients
    await manager.broadcast_json({
        "type": "CALL_TOKEN",
        "office_type": db_token.office_type,
        "data": schemas.Token.model_validate(db_token).model_dump(mode='json')
    })
    
    return db_token

@app.put("/api/tokens/{token_id}/status", response_model=schemas.Token)
async def update_status(token_id: int, status: str, office_type: str, db: Session = Depends(get_db_dynamic)):
    valid_statuses = ["PENDING", "SERVING", "COMPLETED", "MISSED", "HOLD"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    db_token = crud.update_token_status(db=db, token_id=token_id, status=status)
    if not db_token:
        raise HTTPException(status_code=404, detail="Token not found")
        
    # Broadcast status update
    await manager.broadcast_json({
        "type": "UPDATE_STATUS",
        "office_type": db_token.office_type,
        "data": schemas.Token.model_validate(db_token).model_dump(mode='json')
    })
    
    return db_token

@app.get("/api/queues/status")
def get_queue_status(office_type: str, db: Session = Depends(get_db_dynamic)):
    pending = crud.get_pending_tokens(db, office_type)
    active = crud.get_active_tokens(db, office_type)
    return {
        "pending_count": len(pending),
        "active_counters": len(set(t.counter_assigned for t in active if t.counter_assigned)),
        "active_tokens": [schemas.Token.model_validate(t).model_dump(mode='json') for t in active],
        "pending_tokens": [schemas.Token.model_validate(t).model_dump(mode='json') for t in pending]
    }

@app.get("/api/admin/metrics")
def get_admin_metrics(office_type: str, db: Session = Depends(get_db_dynamic)):
    return crud.get_admin_metrics(db, office_type)

@app.get("/api/counters", response_model=List[schemas.Counter])
def get_counters(office_type: str, db: Session = Depends(get_db_dynamic)):
    return crud.get_counters(db, office_type)

@app.post("/api/counters", response_model=schemas.Counter)
async def create_counter(counter_number: int, office_type: str, db: Session = Depends(get_db_dynamic)):
    db_counter = crud.create_counter(db, counter_number, office_type)
    await manager.broadcast_json({
        "type": "UPDATE_COUNTERS",
        "office_type": office_type
    })
    return db_counter

@app.put("/api/counters/{counter_id}/status", response_model=schemas.Counter)
async def update_counter_status(counter_id: int, is_active: bool, office_type: str, db: Session = Depends(get_db_dynamic)):
    db_counter = crud.update_counter_status(db, counter_id, is_active)
    if not db_counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    await manager.broadcast_json({
        "type": "UPDATE_COUNTERS",
        "office_type": db_counter.office_type
    })
    return db_counter

@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't really expect clients to send much to this socket,
            # but we need to keep it open to receive disconnects
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
