
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from backend/.env")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def get_session():
    with Session(engine) as session:
        yield session


def test_database_connection():
    with engine.connect() as connection:
        return connection.execute(text("SELECT 1")).scalar_one()
