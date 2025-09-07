from importlib.resources import path
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from ..database import *
from .. import schema, oAuth
from ..hashing import Hash

router = APIRouter(
    prefix="/authentication",
    tags = ["Authentication"]
)


async def set_refresh_token_cookie(resp: Response, data: dict) -> Response:
    resp.set_cookie(
        key="refresh_token",
        value=await oAuth.create_refresh_token(data),
        max_age=oAuth.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,  ### !!! Danger: recheck before production
        secure=True,  ### !!! Danger: recheck before production
        # samesite="strict", ### !!! Danger: recheck before production
        path='/authentication/refresh'
    )
    return resp

@router.post('/signup', response_model=schema.ShowUserOnly, status_code=status.HTTP_201_CREATED)
async def create_user(request: schema.Signup, db: AsyncSession = Depends(get_db)):
    if await db.get(User, request.id.lower()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User id already exists')
    user = User(id=request.id.lower(), name=request.name, password=Hash.bcrypt(request.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post('/login', status_code=status.HTTP_202_ACCEPTED)
async def login(resp : Response, request: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, request.username.lower())
    if not user or not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    data = {
        "id" : user.id,
        "role" : "user"
    }

    resp = await set_refresh_token_cookie(resp, data)

    return {
        "access_token": await oAuth.create_access_token(data),
        # "refresh_token": await oAuth.create_refresh_token(data),
        "token_type" : "bearer"
    }

@router.post('/refresh')
async def refresh_token(resp: Response, request: Request, db: AsyncSession = Depends(get_db)):
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials'
    )
    token = request.cookies.get("refresh_token")
    if not token:
        raise exception

    payload = await oAuth.verify_jwt(token, exception, secret_key=oAuth.REFRESH_TOKEN_SECRET_KEY)

    user = await db.get(User, payload.id.lower())
    if not user:
        raise exception
    
    data = {
        "id" : user.id,
        "role" : "user"
    }


    resp = await set_refresh_token_cookie(resp, data)

    return {
        "access_token": await oAuth.create_access_token(data),
        # "refresh_token": await oAuth.create_refresh_token(data),
        "token_type": "bearer"
    }







# from fastapi import FastAPI, Request, HTTPException, status, Depends
# from starlette.responses import JSONResponse
# from urllib.parse import urlparse

# ALLOWED_ORIGIN_SET = {
#     "https://your-frontend-domain.com",
#     # dev only:
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     "http://localhost:5500",
# }

# def check_origin(request: Request):
#     # Only gate state-changing requests; allow GET if you want it public.
#     if request.method in {"POST","PUT","PATCH","DELETE"}:
#         origin = request.headers.get("origin")
#         referer = request.headers.get("referer")
#         # browsers send at least one of these; non-browsers often don’t.
#         candidate = None
#         if origin:
#             candidate = origin
#         elif referer:
#             r = urlparse(referer)
#             candidate = f"{r.scheme}://{r.netloc}"

#         if not candidate or candidate not in ALLOWED_ORIGIN_SET:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin not allowed")

#         # If you use cookies, also verify a CSRF token:
#         csrf_header = request.headers.get("x-csrf-token")
#         csrf_cookie = request.cookies.get("csrf-token")
#         if csrf_cookie is None or csrf_header != csrf_cookie:
#             raise HTTPException(status_code=403, detail="CSRF check failed")

# app = FastAPI()

# # Keep your existing CORSMiddleware but tighten it for prod:
# from fastapi.middleware.cors import CORSMiddleware

# ALLOWED_ORIGINS = [
#     "https://your-frontend-domain.com",
#     # dev only:
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     "http://localhost:5500",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=ALLOWED_ORIGINS,
#     allow_credentials=True,  # only if you actually use cookies
#     allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
#     allow_headers=["*"],
#     max_age=3600,  # cache preflight
# )

# # Example of protecting a route:
# from fastapi import APIRouter
# router = APIRouter()

# @router.post("/update", dependencies=[Depends(check_origin)])
# def update(...):
#     ...

# app.include_router(router)
