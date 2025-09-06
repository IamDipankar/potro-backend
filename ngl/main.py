from fastapi import FastAPI
from contextlib import asynccontextmanager

from .database import *
from . import router, schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: (optional) cleanup


app = FastAPI(lifespan=lifespan)


@app.get("/", tags=["root"], response_model=schema.CommunicationMessage)
async def health_check():
    return {"detail": "Welcome to the messaging API"}


app.include_router(router.sending.router)
app.include_router(router.authentication.router)
app.include_router(router.receiving.router)


