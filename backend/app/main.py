from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import requests
from dotenv import load_dotenv
import google.generativeai as genai

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(ENV_PATH, override=True)

from . import models, schemas, crud
from .database import engines, get_db_dynamic
from .websocket_manager import manager
from .services.notification_service import send_whatsapp_token_created, send_whatsapp_token_called, send_whatsapp_token_recalled
from .services.telegram_service import send_telegram_token_created, send_telegram_token_called, send_telegram_token_recalled

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

# Mount frontend files (wrapped to allow backend-only instances to run without static directory)
try:
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")
except Exception as e:
    print("Frontend static mounting skipped (running in backend-only container):", e)

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
    
    # Non-blocking WhatsApp & Telegram Notifications
    try:
        if db_token.customer_info:
            send_whatsapp_token_created(db_token.customer_info, db_token.token_number, db_token.service_name, office_type)
            send_telegram_token_created(db_token.customer_info, db_token.token_number, db_token.service_name, office_type)
    except Exception as notify_err:
        print("[NOTIFICATION LOG] Non-blocking dispatch error:", notify_err)
    
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
    
    # Non-blocking WhatsApp & Telegram Notifications on token called
    try:
        if db_token.customer_info:
            send_whatsapp_token_called(db_token.customer_info, db_token.token_number, counter_number, office_type)
            send_telegram_token_called(db_token.customer_info, db_token.token_number, counter_number, office_type)
    except Exception as notify_err:
        print("[NOTIFICATION LOG] Non-blocking dispatch error:", notify_err)
    
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
    
    # Non-blocking Recall Notification
    try:
        if db_token.customer_info:
            send_whatsapp_token_recalled(db_token.customer_info, db_token.token_number, db_token.office_type, status_note="RECALLED")
            send_telegram_token_recalled(db_token.customer_info, db_token.token_number, db_token.office_type, status_note="RECALLED")
    except Exception as notify_err:
        print("[NOTIFICATION LOG] Recall dispatch error:", notify_err)
    
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
    
    # Non-blocking Status Change Notification (MISSED / HOLD / RE-QUEUED)
    if status in ["MISSED", "HOLD", "PENDING"]:
        try:
            if db_token.customer_info:
                status_label = "RE-QUEUED TO LAST" if status == "PENDING" else status
                send_whatsapp_token_recalled(db_token.customer_info, db_token.token_number, db_token.office_type, status_note=status_label)
                send_telegram_token_recalled(db_token.customer_info, db_token.token_number, db_token.office_type, status_note=status_label)
        except Exception as notify_err:
            print("[NOTIFICATION LOG] Status update dispatch error:", notify_err)
    
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

"""
===============================================================================
GROQ CLOUD API SETUP GUIDE & DOCUMENTATION
===============================================================================
To integrate Groq Cloud API for ultra-fast Llama-3 / Mixtral inference:
1. Go to https://console.groq.com/ and sign up or log in.
2. Navigate to "API Keys" in the left sidebar menu.
3. Click "Create API Key", name it (e.g. "smart-token-prod"), and copy the key.
4. Add the key locally in backend/.env:
   GROQ_API_KEY=gsk_your_groq_api_key_here
   (Also add GROQ_API_KEY under Vercel / Render Environment Variables settings).
5. Model used: "llama-3.3-70b-versatile" for AI routing and queue insights,
   with automatic failover to Gemini ("gemini-flash-latest") or rule-based matching.
===============================================================================
"""

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

def call_groq_llm(prompt_text: str) -> Optional[dict]:
    groq_key = os.getenv("GROQ_API_KEY")
    if os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GROQ_API_KEY="):
                        groq_key = line.strip().split("=", 1)[1].strip()
                        break
        except Exception as e:
            print("[GROQ ENV READ ERROR]", e)
            
    if not groq_key or not groq_key.strip():
        print("[GROQ DEBUG] No GROQ_API_KEY found")
        return None
        
    groq_key_clean = groq_key.strip()
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key_clean}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            print("[AI ENGINE] Successfully processed query via Groq Cloud API (Llama-3.3-70B)")
            return json.loads(content)
        else:
            print(f"[GROQ WARNING] Groq API returned status {res.status_code}: {res.text}")
            return None
    except Exception as err:
        print(f"[GROQ ERROR] Failed to query Groq API: {err}")
        return None

def call_gemini_llm(prompt_text: str) -> Optional[dict]:
    load_dotenv(ENV_PATH, override=True)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or not gemini_key.strip():
        return None
    try:
        genai.configure(api_key=gemini_key.strip())
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt_text)
        text_resp = response.text.strip()
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
        print("[AI ENGINE] Successfully processed query via Google Gemini API")
        return json.loads(text_resp.strip())
    except Exception as err:
        print(f"[GEMINI ERROR] Failed to query Gemini API: {err}")
        return None

def fallback_rule_based_routing(user_input: str, current_office: str) -> dict:
    inp = user_input.lower()
    
    # Check Municipal
    if any(k in inp for k in ["birth", "death", "marriage", "civil", "tax", "property tax", "permit", "license", "building", "drainage", "water", "complaint"]):
        rec_center = "MUNICIPAL"
        if any(k in inp for k in ["tax", "property", "dues"]):
            code, name = "TX", "Taxation & Payments"
            docs = ["Property Assessment Number", "Previous Tax Receipt", "Aadhaar Card"]
        elif any(k in inp for k in ["permit", "license", "building", "construction"]):
            code, name = "PL", "Permits & Licenses"
            docs = ["Approved Building Plan", "Land Ownership Proof / Patta", "Applicant ID Proof"]
        elif any(k in inp for k in ["drainage", "water", "utility", "complaint"]):
            code, name = "UG", "Utilities & Grievances"
            docs = ["Water Connection Passbook / Connection ID", "Aadhaar Card", "Written Complaint Form"]
        else:
            code, name = "CR", "Civil Registration"
            docs = ["Hospital Discharge / Birth Note", "Parents' Aadhaar Cards", "Marriage Certificate Copy"]
            
    # Check E-Sevai
    elif any(k in inp for k in ["patta", "chitta", "land", "revenue", "income", "nativity", "community", "first graduate", "pension", "widow", "disability"]):
        rec_center = "ESEVAI"
        if any(k in inp for k in ["pension", "widow", "disability", "old age"]):
            code, name = "SS", "Pension Schemes"
            docs = ["Aadhaar Card", "Bank Account Passbook", "Income Certificate / Medical Certificate"]
        elif any(k in inp for k in ["patta", "chitta", "land", "a-register"]):
            code, name = "LD", "Land & Utilities"
            docs = ["Sale Deed Copy", "Encumbrance Certificate (EC)", "Aadhaar Card"]
        else:
            code, name = "RV", "Revenue Certificates"
            docs = ["Aadhaar Card", "Ration Card / Smart Card", "Passport Size Photograph"]

    # Check Post Office
    elif any(k in inp for k in ["post", "parcel", "speed post", "registered post", "ippb", "money order", "pli", "insurance", "stamps"]):
        rec_center = "POST_OFFICE"
        if any(k in inp for k in ["savings", "ippb", "money order"]):
            code, name = "SB", "Savings Bank & Money transfer"
            docs = ["Post Office Savings Passbook / IPPB Card", "PAN Card", "Aadhaar Card"]
        elif any(k in inp for k in ["pli", "insurance", "life"]):
            code, name = "INS", "Postal Life Insurance"
            docs = ["Policy Document / Proposal Form", "Age Proof (Aadhaar/School Certificate)", "Medical Fitness Certificate"]
        elif any(k in inp for k in ["retail", "passport seva"]):
            code, name = "RT", "Retail & Aadhaar"
            docs = ["Aadhaar Card / Enrollment Slip", "Proof of Identity", "Proof of Address"]
        else:
            code, name = "MP", "Mails & Parcels"
            docs = ["Sender ID Proof (Aadhaar/Voter ID)", "Packed Parcel / Document Envelopes", "Recipient Full Address"]

    # Default to Bank
    else:
        rec_center = "BANK"
        if any(k in inp for k in ["cash", "deposit", "withdraw", "cheque"]):
            code, name = "CS", "Cash Transactions"
            docs = ["Bank Account Passbook", "Cheque Book / Deposit Slip", "PAN Card (for transactions > 50k)"]
        elif any(k in inp for k in ["loan", "fd", "rd", "aadhaar"]):
            code, name = "AD", "Aadhaar & Loans"
            docs = ["Income Proof (ITR / Pay Slips)", "3 Months Bank Statements", "Aadhaar Card & PAN Card"]
        else:
            code, name = "AC", "Account Opening & KYC"
            docs = ["Aadhaar Card", "PAN Card", "2 Passport Size Photos", "Address Proof"]

    belongs = (rec_center == current_office)
    reasoning = f"{name} is provided by the {rec_center.replace('_', ' ')} kiosk."
    if not belongs:
        reasoning += f" Since you are currently at the {current_office.replace('_', ' ')} kiosk, would you like to generate a queue token and transfer to the {rec_center.replace('_', ' ')} office kiosk?"
        
    return {
        "belongs_to_current_center": belongs,
        "recommended_center": rec_center,
        "service_code": code,
        "service_name": name,
        "reasoning": reasoning,
        "documents": docs
    }

@app.post("/api/ai/route-service")
def ai_route_service(payload: AIServiceRouteRequest):
    current_office = payload.office_type.upper().strip()
    
    prompt = f"""
You are an expert AI queue receptionist for a multi-center public portal.
The user is currently visiting the {current_office} kiosk.
User input: "{payload.user_input}"

Available Centers and their Service Categories:
{json.dumps(OFFICE_SERVICES_INFO, indent=2)}

Strictest Rules:
1. Scan ALL available centers first. Match the user's request to the category that fits best semantically.
2. If the request fits a category in a DIFFERENT center better than any category in the current center ({current_office}), you MUST set "belongs_to_current_center" to false and set "recommended_center" to the center that actually handles it.
3. Example: "Birth certificate" or "Marriage registration" is Civil Registration, which belongs to MUNICIPAL. If current_office is BANK, set "belongs_to_current_center" to false and "recommended_center" to "MUNICIPAL".
4. List 3 to 4 specific required documents for the matched service under "documents".
5. Respond ONLY with a JSON object in this exact format:
{{
  "belongs_to_current_center": false,
  "recommended_center": "RECOMMENDED_CENTER_NAME",
  "service_code": "SERVICE_CODE",
  "service_name": "SERVICE_NAME",
  "reasoning": "Civil Registration (Birth Certificate) is provided at the Municipal Corporation Center. Would you like to generate a queue token and transfer to the Municipal Office kiosk?",
  "documents": ["Hospital Discharge / Birth Note", "Parents' Aadhaar Cards", "Marriage Certificate Copy"]
}}
"""
    # 1. Try Groq Cloud API
    parsed = call_groq_llm(prompt)
    if not parsed:
        # 2. Try Gemini API fallback
        parsed = call_gemini_llm(prompt)
        
    if not parsed:
        # 3. Intelligent Rule-Based Fallback
        parsed = fallback_rule_based_routing(payload.user_input, current_office)
        
    # Ensure fields exist
    if "belongs_to_current_center" not in parsed:
        parsed["belongs_to_current_center"] = (parsed.get("recommended_center") == current_office)
        
    return parsed

@app.get("/api/admin/ai-insights")
def get_ai_insights(office_type: str, db: Session = Depends(get_db_dynamic)):
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
    # 1. Try Groq API
    parsed = call_groq_llm(prompt)
    if not parsed:
        # 2. Try Gemini API
        parsed = call_gemini_llm(prompt)
        
    if parsed:
        return parsed
        
    # 3. Dynamic Calculation Fallback
    est_minutes = max(2, (len(pending) * 4) // max(1, active_counters_count))
    bottleneck = "None"
    if pending_by_service:
        bottleneck = max(pending_by_service, key=pending_by_service.get)
        
    return {
        "predicted_wait_time_minutes": est_minutes,
        "efficiency_score": 95 if len(pending) < 5 else 80,
        "bottleneck_service": bottleneck,
        "recommendation": f"Current queue is optimal (~{est_minutes} min wait). Consider adding counters if waiting count exceeds 10."
    }
