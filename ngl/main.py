from fastapi import FastAPI, status, HTTPException, Depends, Request, Response
from contextlib import asynccontextmanager, suppress
from fastapi.middleware.cors import CORSMiddleware

from .database import *
from . import router, schema
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from . import oAuthentication
# from starlette.middleware.sessions import SessionMiddleware
import firebase_admin as fbad

from pathlib import Path
import logging

from .loop_watchdog import loop_watchdog
import asyncio
from .timer import *


# -------------------------
# LOGGING: always visible
# -------------------------
logging.basicConfig(
    level=logging.INFO,  # ensure INFO shows
    format=" [%(name)s] %(message)s \n"
)

checkpoint_logger = logging.getLogger("checkpoint")
if not checkpoint_logger.handlers:
    h = logging.StreamHandler()  # stdout/stderr
    h.setFormatter(logging.Formatter(" [%(name)s] %(message)s \n"))
    checkpoint_logger.addHandler(h)
checkpoint_logger.setLevel(logging.INFO)
checkpoint_logger.propagate = False  # avoid double logs

cred = fbad.credentials.Certificate("serviceAccountKey.json")
fbad.initialize_app(cred)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    - Startup:
        * ensure DB tables exist
        * start loop watchdog
    - Shutdown:
        * stop loop watchdog
    """
    # Start watchdog first so we can see any long startup steps as lag:
    loop = asyncio.get_running_loop()
    try:
        loop.set_debug(True)
        loop.slow_callback_duration = 0.05  # 50ms
    except Exception:
        pass
    watchdog_task = loop.create_task(loop_watchdog(period_ms=20, warn_ms=100))
    checkpoint_logger.info("[lifespan] loop watchdog started")

    # Your original startup step: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    checkpoint_logger.info("[lifespan] database tables ensured")

    try:
        yield
    finally:
        checkpoint_logger.info("[lifespan] shutting down loop watchdog...")
        watchdog_task.cancel()
        with suppress(asyncio.CancelledError):
            await watchdog_task


app = FastAPI(
    lifespan=lifespan,
    docs_url="/SobaiBolo-docs",      # Disable Swagger UI (/docs)
    redoc_url="/SobaiBolo-redoc",     # Disable ReDoc (/redoc)
    openapi_url="/SobaiBolo-openapi.json"    # Disable OpenAPI schema (/openapi.json)
)

# app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "dev-secret-change-me"))
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """
    Per-request total timing (in addition to in-route checkpoints).
    """
    t = CheckTimer(f"{request.method} {request.url.path}")
    try:
        response = await call_next(request)
        return response
    finally:
        t.cp("response_sent")

@app.on_event("startup")
async def _start_watchdog():
    loop = asyncio.get_running_loop()
    loop.set_debug(True)  # optional: asyncio will log slow callbacks
    loop.create_task(loop_watchdog(period_ms=20, warn_ms=100))

templates = Jinja2Templates(directory="pages")

def readint(p):
    try:
        s = Path(p).read_text().strip()
        return None if s in ("", "max") else int(s)
    except FileNotFoundError:
        return None

async def memory_usages():
    limit = readint("/sys/fs/cgroup/memory.max") or readint("/sys/fs/cgroup/memory/memory.limit_in_bytes")
    usage = readint("/sys/fs/cgroup/memory.current") or readint("/sys/fs/cgroup/memory/memory.usage_in_bytes")

    print("cgroup limit bytes:", limit)
    print("cgroup usage bytes:", usage)

    return {
        "Limit (bytes)": limit,
        "Usage (bytes)": usage,
    }

# def titlecase(s: str) -> str:
#     return s.title()
# templates.env.filters["titlecase"] = titlecase
# templates.env.globals["app_name"] = "My FastAPI App"


# CORS settings
# ALLOWED_ORIGINS = [
#     # "https://potro-backend-1.onrender.com",
#     # "*" ### !!! Danger: recheck before production
#     # "localhost:8000",
#     # "http://localhost:8000",
#     # "localhost:3000",
#     # "http://127.0.0.1:8000",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=ALLOWED_ORIGINS,   # or use allow_origin_regex=r"https?://.*\.yourdomain\.com$"
#     allow_credentials=True,          # only if you use cookies/auth
#     allow_methods=["GET","POST"],
#     allow_headers=["*"],
# )


@app.get("/", tags=["root"], status_code=status.HTTP_200_OK)
async def index():
    return

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return

app.include_router(router.sending.router)
app.include_router(router.authentication.router)

app.include_router(router.receiving.router)

# @app.get("/signup")
# async def signup_page():
#     return FileResponse("pages/signup.html")

# @app.get("/login")
# async def login_page():
#     return FileResponse("pages/login.html")

# @app.get("/inbox")
# async def view_messages_page(request : Request, msg_id : int = None, ):
#     if not msg_id:
#         return FileResponse("pages/inbox.html")
#     else:
#         return templates.TemplateResponse("view-message.html", {
#                 "request": request,
#                 "msg_id": msg_id
#             })

@app.get("/memory-usages")
async def get_memory_usages():
    return await memory_usages()

@app.get("/Ads.txt")
async def ads_txt():
    return FileResponse("pages/ads.txt", media_type="text/plain")


@app.get('/{user_id}', status_code=status.HTTP_200_OK, response_model=schema.ShowUserOnly)
async def get_user(user_id: str, request : Request, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id.lower())
    if user:
        return templates.TemplateResponse("send.html", {
                "request": request,
                "user_id": user_id.strip()
            })
    else:
        return FileResponse("pages/404.html", status_code=404)
    


