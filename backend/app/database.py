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
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        db_exists = True
    except Exception as e:
        print(f"[INFO] Direct connection to DATABASE_URL failed: {e}. Attempting to create database if local...")
        
    if not db_exists:
        try:
            # Parse DATABASE_URL to get host, user, password, port, and db_name
            parsed = urllib.parse.urlparse(DATABASE_URL)
            db_name = parsed.path.lstrip('/')
            
            # Construct a base URL connecting to the default 'postgres' database
            base_parsed = parsed._replace(path='/postgres')
            base_url = urllib.parse.urlunparse(base_parsed)
            
            conn = psycopg2.connect(base_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(f"CREATE DATABASE {db_name}")
                print(f"[INFO] Created database: {db_name}")
            
            cursor.close()
            conn.close()
        except Exception as ex:
            print("[DATABASE STARTUP WARNING] Could not verify/create database:", ex)
            
    # 2. Connect to the database and create the schemas
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        for office, schema_name in OFFICE_SCHEMAS.items():
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            print(f"[INFO] Created/verified schema: {schema_name}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print("[DATABASE STARTUP WARNING] Could not verify/create schemas:", e)

# Run creation check immediately on import
create_db_and_schemas_if_not_exist()

# Build SQLAlchemy engines and SessionLocal managers for each center schema
engines = {}
session_factories = {}

for office, schema in OFFICE_SCHEMAS.items():
    # Pass connect_args options to set the search path to the specific schema
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

