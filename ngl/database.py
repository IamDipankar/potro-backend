from sqlalchemy import ForeignKey, Column, String, Integer, Boolean, BigInteger, select
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# PostgreSQL configuration from environment variables
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
IS_INTERNAL = os.getenv("IS_INTERNAL", "False") == "True"
# URL encode the password to handle special characters
encoded_password = quote_plus(DATABASE_PASSWORD)

# For Render PostgreSQL, construct URL without SSL in string (SSL handled in connect_args)
DATABASE_URL = f"postgresql+asyncpg://{DATABASE_USER}:{encoded_password}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# Engine configuration for remote PostgreSQL (like Render)
engine = create_async_engine(
    DATABASE_URL, 
    # echo=True, ## Danger / revise
    echo = False,
    # SSL configuration for Render PostgreSQL
    connect_args={
        "ssl": "require"
    },
    # Connection pool settings for remote database
    pool_size=80,
    max_overflow=0,
    pool_pre_ping=False,  # Validate connections before use  ## Danger / revise
    pool_recycle=3600,   # Recycle connections every hour
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True, nullable = False)
    name = Column(String, nullable = True)
    password = Column(String, nullable = True)  # Nullable for OAuth users
    email = Column(String(50), unique=True, index=False, nullable = True)  # Nullable for non-OAuth users

    messages = relationship("Message", back_populates='user', lazy="selectin")
    


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True, nullable = False)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable = False)
    content = Column(String, nullable = False)
    time = Column(String, nullable = False)
    unread = Column(Boolean, default=True)  # True for unread, False for read

    user = relationship("User", back_populates='messages', lazy="selectin")

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


class GoogleUsers(Base):
    __tablename__ = "google_users"
    sub = Column(String(25), unique=True, index=True, nullable = False, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=False, nullable = False)

    user = relationship("User", lazy="selectin")
