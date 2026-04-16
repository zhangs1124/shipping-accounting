import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
APP_ENV = os.getenv("APP_ENV", "development")

# 強制所有環境統一使用主要資料庫，讓線上資料直接作為測試
SQLALCHEMY_DATABASE_URL = "sqlite:///./shipping.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Enable WAL mode and other optimizations
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute("PRAGMA busy_timeout = 5000")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



from utils.audit_logger import register_audit_events
register_audit_events(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

