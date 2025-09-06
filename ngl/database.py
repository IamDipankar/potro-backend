from sqlalchemy import ForeignKey, Column, String, Integer
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

SQL_BASE_URL = "sqlite+aiosqlite:///./ngl/database.db"

engine = create_async_engine(SQL_BASE_URL, connect_args={'check_same_thread' : False})

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

# class User(Base):
#     __tablename__ = "user"
#     Name = Column(String)
#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True)
#     bio_data = Column(String)

# class Post(Base):
#     __tablename__ = "posts"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("user.id"), index=True)
#     title = Column(String)
#     content = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True, nullable = False)
    name = Column(String, nullable = False)
    password = Column(String, nullable = False)

    message = relationship("Message", back_populates='user', lazy="selectin")



class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True, nullable = False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable = False)
    content = Column(String, nullable = False)
    time = Column(String, nullable = False)

    user = relationship("User", back_populates='message', lazy="selectin")

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
