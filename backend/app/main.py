from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import google.generativeai as genai

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

# AI Integration Support structures and endpoints
class AIServiceRouteRequest(BaseModel):
    user_input: str
    office_type: str

OFFICE_SERVICES_INFO = {
    "BANK": [
        {"code": "AC", "name": "Account Opening & KYC", "desc": "Open new account, submit documentations, update address"},
        {"code": "CS", "name": "Cash Transactions", "desc": "Deposit cash, withdraw money, process cheques"},
        {"code": "AD", "name": "Aadhaar & Loans", "desc": "Aadhaar update, loan applications, FD/RD setups"}
    ],
    "ESEVAI": [
        {"code": "RV", "name": "Revenue Certificates", "desc": "Community, Income, Nativity, First Graduate certificates"},
        {"code": "SS", "name": "Pension Schemes", "desc": "Old Age Pension, Destitute Widow, Disability pension"},
        {"code": "LD", "name": "Land & Utilities", "desc": "Patta transfer, Chitta, A-Register, Electricity bills"}
    ],
    "POST_OFFICE": [
        {"code": "MP", "name": "Mails & Parcels", "desc": "Speed Post, Registered Post, domestic/international mail"},
        {"code": "SB", "name": "Savings Bank & Money transfer", "desc": "Post office savings account, IPPB, Money orders"},
        {"code": "INS", "name": "Postal Life Insurance", "desc": "PLI, RPLI, Pradhan Mantri Bima Yojana applications"},
        {"code": "RT", "name": "Retail & Aadhaar", "desc": "Aadhaar services, Passport Seva Seva, stamps purchase"}
    ],
    "MUNICIPAL": [
        {"code": "CR", "name": "Civil Registration", "desc": "Birth certificate, Death certificate, Marriage registration"},
        {"code": "TX", "name": "Taxation & Payments", "desc": "Property tax, professional tax payment, trade licensing dues"},
        {"code": "PL", "name": "Permits & Licenses", "desc": "Building permissions, construction approvals, license renewal"},
        {"code": "UG", "name": "Utilities & Grievances", "desc": "Water connection request, drainage issues, municipal complaints"}
    ]
}

@app.post("/api/ai/route-service")
def ai_route_service(payload: AIServiceRouteRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured on server.")
    
    current_office = payload.office_type.upper().strip()
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    prompt = f"""
You are an intelligent queue receptionist for a multi-center public portal.
The user is currently visiting the {current_office} center.
Your task is to analyze the user's request and match it to the correct service category across any of our centers.

Available Centers and their Service Categories:
{json.dumps(OFFICE_SERVICES_INFO, indent=2)}

Determine if the user's request matches a category in the current center ({current_office}) or if it belongs to a different center.

You must respond ONLY with a JSON object in this exact format:
{{
  "belongs_to_current_center": true_or_false,
  "recommended_center": "BANK_OR_ESEVAI_OR_POST_OFFICE_OR_MUNICIPAL",
  "service_code": "MATCHING_SERVICE_CODE",
  "service_name": "MATCHING_SERVICE_NAME",
  "reasoning": "A very brief explanation of why this service and center are chosen, formatted politely for the customer.",
  "documents": ["Document 1", "Document 2", ...]
}}
"""
    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)
        text_resp = response.text.strip()
        
        # Clean response string to extract JSON (in case model wraps it in markdown)
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
        text_resp = text_resp.strip()
        
        parsed = json.loads(text_resp)
        
        # Ensure fields exist
        if "belongs_to_current_center" not in parsed:
            parsed["belongs_to_current_center"] = (parsed.get("recommended_center") == current_office)
            
        return parsed
    except Exception as e:
        print("Gemini API Error:", e)
        raise HTTPException(status_code=500, detail=f"AI routing failed: {str(e)}")

@app.get("/api/admin/ai-insights")
def get_ai_insights(office_type: str, db: Session = Depends(get_db_dynamic)):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "predicted_wait_time_minutes": 0,
            "efficiency_score": 100,
            "bottleneck_service": "None",
            "recommendation": "Configure GEMINI_API_KEY in .env to enable AI insights and predictions!"
        }
        
    start_of_day = crud.get_start_of_day()
    pending = db.query(models.Token).filter(
        models.Token.status == "PENDING",
        models.Token.office_type == office_type,
        models.Token.created_at >= start_of_day
    ).all()
    active = db.query(models.Token).filter(
        models.Token.status == "SERVING",
        models.Token.office_type == office_type,
        models.Token.created_at >= start_of_day
    ).all()
    completed = db.query(models.Token).filter(
        models.Token.status == "COMPLETED",
        models.Token.office_type == office_type,
        models.Token.created_at >= start_of_day
    ).all()
    counters = db.query(models.Counter).filter(models.Counter.office_type == office_type).all()
    
    # Calculate queue statistics
    pending_by_service = {}
    for t in pending:
        pending_by_service[t.service_name] = pending_by_service.get(t.service_name, 0) + 1
        
    completed_by_service = {}
    for t in completed:
        completed_by_service[t.service_name] = completed_by_service.get(t.service_name, 0) + 1
        
    active_counters_count = len([c for c in counters if c.is_active])
    
    queue_data = {
        "office_type": office_type,
        "active_counters_count": active_counters_count,
        "pending_count": len(pending),
        "active_serving_count": len(active),
        "completed_count": len(completed),
        "pending_by_service": pending_by_service,
        "completed_by_service": completed_by_service
    }
    
    genai.configure(api_key=api_key)
    prompt = f"""
You are an expert AI queue management optimizer.
Analyze this real-time queue snapshot for a {office_type} service center and provide predicted wait times and resource allocation advice.

Queue Data Snapshot:
{json.dumps(queue_data, indent=2)}

You must respond ONLY with a JSON object in this exact format:
{{
  "predicted_wait_time_minutes": PREDICTED_NUMERIC_MINUTES,
  "efficiency_score": ACCURACY_RATING_FROM_1_TO_100,
  "bottleneck_service": "SERVICE_NAME_WITH_THE_MOST_BACKLOG_OR_None",
  "recommendation": "Provide a single highly actionable tip to clear the queue backlog or improve counter assignments based on the snapshot."
}}
"""
    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)
        text_resp = response.text.strip()
        
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
        text_resp = text_resp.strip()
        
        parsed = json.loads(text_resp)
        return parsed
    except Exception as e:
        print("Gemini AI Insights Error:", e)
        return {
            "predicted_wait_time_minutes": len(pending) * 5,  # Fallback: simple heuristic
            "efficiency_score": 85,
            "bottleneck_service": "Unavailable",
            "recommendation": f"AI Insights temporarily offline: {str(e)}"
        }
