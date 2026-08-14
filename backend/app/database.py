import os
import psycopg2
import urllib.parse
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import Request
from dotenv import load_dotenv

load_dotenv()

# We get DATABASE_URL from .env (e.g. Supabase connection string)
# Default is a local postgres database named smart_token_db
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:nambatha@localhost:5432/smart_token_db")

# Fallback BASE_PG_URL for connection/schema setup if DATABASE_URL is not set or to check connection
BASE_PG_URL = os.getenv("BASE_DATABASE_URL", "postgresql://postgres:nambatha@localhost:5432/postgres")

# Mappings of schemas instead of databases
OFFICE_SCHEMAS = {
    "BANK": "bank",
    "ESEVAI": "esevai",
    "POST_OFFICE": "post_office",
    "MUNICIPAL": "municipal"
}

# Auto create database and schemas in postgres on startup if they do not exist
def create_db_and_schemas_if_not_exist():
    # 1. Check if the main database exists/is connectable
    db_exists = False
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=2)
        conn.close()
        db_exists = True
    except Exception as e:
        print(f"[INFO] Direct connection to DATABASE_URL failed: {e}.")
        raise e
        
    # 2. Connect to the database and create the schemas
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=2)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        for office, schema_name in OFFICE_SCHEMAS.items():
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            print(f"[INFO] Created/verified schema: {schema_name}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print("[DATABASE STARTUP WARNING] Could not verify/create schemas:", e)

# Build SQLAlchemy engines and SessionLocal managers for each center schema
engines = {}
session_factories = {}

is_sqlite = "sqlite" in DATABASE_URL

if not is_sqlite:
    try:
        if "postgresql" in DATABASE_URL:
            create_db_and_schemas_if_not_exist()
    except Exception as err:
        print("[DATABASE NOTICE] Remote Postgres connection unavailable. Switching to local SQLite database.")
        is_sqlite = True

if is_sqlite:
    SQLITE_URL = "sqlite:///./smart_token_local.db"
    for office, schema in OFFICE_SCHEMAS.items():
        engines[office] = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
        session_factories[office] = sessionmaker(autocommit=False, autoflush=False, bind=engines[office])
else:
    for office, schema in OFFICE_SCHEMAS.items():
        engines[office] = create_engine(
            DATABASE_URL, 
            connect_args={"options": f"-c search_path={schema}"}
        )
        session_factories[office] = sessionmaker(autocommit=False, autoflush=False, bind=engines[office])

Base = declarative_base()

# Helper to open connection to a specific center database/schema
def get_db_session(office_type: str):
    office = str(office_type).upper().strip()
    if office not in session_factories:
        office = "BANK"
    return session_factories[office]()

# Dynamic dependency resolver for FastAPI routes
async def get_db_dynamic(request: Request):
    # Parse office_type from query parameters
    office_type = request.query_params.get("office_type")
    
    # Fallback to query body if json is parsed
    if not office_type:
        try:
            body = await request.json()
            office_type = body.get("office_type")
        except Exception:
            pass
            
    if not office_type:
        office_type = "BANK"
        
    db = get_db_session(office_type)
    try:
        yield db
    finally:
        db.close()

