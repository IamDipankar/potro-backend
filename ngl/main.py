from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from .database import *
from . import router, schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: (optional) cleanup


app = FastAPI(
    lifespan=lifespan,
    docs_url="/SobaiBolo-docs",      # Disable Swagger UI (/docs)
    redoc_url="/SobaiBolo-redoc",     # Disable ReDoc (/redoc)
    openapi_url="/SobaiBolo-openapi.json"    # Disable OpenAPI schema (/openapi.json)
)

# CORS settings
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "https://your-frontend-domain.com",
    "https://potro-backend-1.onrender.com",
    "null",  # DEV ONLY: lets file:// work; remove for production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # or use allow_origin_regex=r"https?://.*\.yourdomain\.com$"
    allow_credentials=True,          # only if you use cookies/auth
    allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"], response_model=schema.CommunicationMessage)
async def health_check():
    return {"detail": "Welcome to the messaging API"}


app.include_router(router.sending.router)
app.include_router(router.authentication.router)

app.include_router(router.receiving.router)

