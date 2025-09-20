from importlib.resources import path
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, FileResponse
from ..database import *
from .. import schema, oAuthentication
from ..hashing import Hash
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi.templating import Jinja2Templates
import dotenv
import warnings
import time
from ..oAuthentication import get_current_user

dotenv.load_dotenv()

router = APIRouter(
    prefix="/authentication",
    tags = ["Authentication"]
)

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid email profile",
        # You can add "prompt": "consent" here during dev if you want to re-prompt each time
    },
)

templates = Jinja2Templates(directory="pages")


async def set_refresh_token(resp: Response, data: dict):
    token = await oAuthentication.create_refresh_token(data)
    # resp.set_cookie(
    #     key="refresh_token",
    #     value=token,
    #     max_age=oAuthentication.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
    #     httponly=True,  ### !!! Danger: recheck before production
    #     secure=True if os.getenv("IS_PRODUCTION") == "True" else False,  ### !!! Danger: recheck before production
    #     samesite="strict", ### !!! Danger: recheck before production
    #     path='/authentication/refresh'
    # )
    return token

async def send_login(user_id, resp: Response = None, status_code: int = status.HTTP_202_ACCEPTED):
    data = {
        "id": user_id,
        # "role": "user"
    }

    refresh_token = await set_refresh_token(resp, data)
    for name, value in resp.headers.items():
        if name.lower() == 'set-cookie':
            print(f"Set-Cookie: {value}")
    print("=" * 50)

    resp.status_code = status_code

    return {
        "access_token": await oAuthentication.create_access_token(data),
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }
## dropping due to samesite none and not secure

async def generate_user_id(email: str, db: AsyncSession = Depends(get_db)) -> str:
    base_id = email.split('@')[0]
    while await db.get(User, base_id):
        base_id += "." + str(int.from_bytes(os.urandom(2), 'big'))
    
    return base_id

@router.post('/signup', status_code=status.HTTP_201_CREATED)
async def create_user(request: schema.Signup, response: Response, db: AsyncSession = Depends(get_db)):
    if await db.get(User, request.id.lower()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User id already exists')
    if request.email and request.email.strip() == "":
        request.email = None
    if request.name and request.name.strip() == "":
        request.name = None
    user = User(id=request.id.lower(), name=request.name, password=Hash.bcrypt(request.password), email=request.email, fcm_tokens = [request.fcm_token] if request.fcm_token else None)
    db.add(user)
    await db.commit()
    # await db.refresh(user)
    return await send_login(request.id, response, status_code=status.HTTP_201_CREATED)


@router.patch('/login', status_code=status.HTTP_202_ACCEPTED)
async def login(resp : Response, request: schema.Login , db: AsyncSession = Depends(get_db)):
    print("Login called")
    user = await db.get(User, request.user_id.lower())
    if not user or not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    
    payload = await send_login(user.id, resp)
    payload["username"] = user.name
    if fcm_token := request.fcm_token:
        if user.fcm_tokens is None:
            user.fcm_tokens = [fcm_token]
        elif fcm_token not in user.fcm_tokens:
            user.fcm_tokens = user.fcm_tokens + [fcm_token]
        await db.commit()
    return payload

@router.post('/refresh', status_code=status.HTTP_200_OK)
async def refresh_token(resp: Response, request: Request, body: schema.RefreshToken, db: AsyncSession = Depends(get_db)):
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials'
    )
    token = body.refresh_token or request.cookies.get("refresh_token")
    if not token:
        print("No refresh token cookie")
        print("Cookies are:")
        print(request.cookies)
        raise exception

    payload = await oAuthentication.verify_jwt(token, exception, secret_key=oAuthentication.REFRESH_TOKEN_SECRET_KEY)

    user = await db.get(User, payload.id.lower())
    if not user:
        print("Refresh token user not found")
        raise exception
    
    data = {
        "id": user.id,
        # "role": "user"
    }


    refresh_token = await set_refresh_token(resp, data)

    return {
        "access_token": await oAuthentication.create_access_token(data),
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }

# @router.get("/login/google")
# async def google_login(request: Request):
#     redirect_uri = request.url_for("google_auth")
#     return await oauth.google.authorize_redirect(request, redirect_uri)

# @router.get("/callback/google")
# async def google_auth(request: Request, resp: Response, db: AsyncSession = Depends(get_db)):
#     try:
#         token = await oauth.google.authorize_access_token(request)
#         userinfo = token.get("userinfo")
#         if not userinfo:
#             userinfo = await oauth.google.parse_id_token(request, token)
#         if not userinfo:
#             raise HTTPException(status_code=400, detail="Failed to obtain user info")
#         print("Google user info:", userinfo)
#         safe = userinfo.get("email_verified", False) and userinfo.get("aud") == os.getenv("GOOGLE_CLIENT_ID") and userinfo.get("iss") in ['https://accounts.google.com', 'accounts.google.com'] and userinfo.get("exp", 0) > int(time.time())
#         if not safe:
#             raise HTTPException(status_code=400, detail="Unsafe Google login attempt")
        
#         # Check if user with this Google sub exists
#         google_login = await db.execute(
#             select(GoogleUsers).where(GoogleUsers.sub == str(userinfo["sub"]))
#         )

#         google_login = google_login.scalars().first()
#         if google_login:
#             user = await db.get(User, google_login.user_id)
#             if user:
#                 data = await send_login(user.id, resp)
#                 response = templates.TemplateResponse("loginskeleton.html", {
#                     "request": request,
#                     "access_token": data["access_token"],
#                     "token_type": data["token_type"],
#                     "user_id": user.id
#                 })

#                 refresh_token = await set_refresh_token(response, {
#                         "id": user.id,
#                         # "role": "user"
#                     })
                
#                 return response   # TODO: Fix refresh token issue
#             else:
#                 warnings.warn("Google user linked to non-existent user id, Attempting delete")
#                 db.delete(google_login)
#                 await db.commit()
    
#         name = userinfo.get("name")
#         email = userinfo.get("email")
#         suggested_id = await generate_user_id(userinfo["email"], db)
        

#         resp = templates.TemplateResponse("oauthSignup.html", {
#                                                 "request": request,
#                                                 "name": name,
#                                                 "suggested_id": suggested_id,
#                                                 "medium": "google"
#                                                 })
        
#         resp.set_cookie(key="oauth_signup_key",
#                         value=await oAuthentication.create_access_token({
#                                 "signature": os.getenv("SIGNATURE"),
#                                 "sub": userinfo["sub"],
#                                 "email": email,
#                         }, expire_delta_minutes=10),
#                         max_age=600, 
#                         httponly=True, 
#                         secure=True if os.getenv("IS_PRODUCTION") == "True" else False,
#                         samesite="strict", 
#                         path="/authentication/oauth_signup/google")
#         return resp

#     except OAuthError as e:
#         raise HTTPException(status_code=400, detail=f"OAuth error here: {e.error}") from e



# @router.post("/oauth_signup/google")
# async def oauth_signup(request: Request, data: schema.OAuthSignup, resp: Response, db: AsyncSession = Depends(get_db)):
#     print("OAuth signup called with data:", data)
#     token = request.cookies.get("oauth_signup_key")
#     if not token:
#         raise HTTPException(status_code=401, detail="Missing or expired signup token")

#     payload = oAuthentication.decode_jwt(token)
#     print(payload)

#     if payload is None or payload.get("signature") != os.getenv("SIGNATURE"):
#         print("Invalid token signature")
#         raise HTTPException(status_code=401, detail="Invalid signup token")

#     if payload.get("sub") is None or payload.get("email") is None:
#         print("Token missing required fields")
#         raise HTTPException(status_code=401, detail="Invalid signup token")

#     if await db.get(User, data.user_id.lower()):
#         raise HTTPException(status_code=400, detail="User ID already exists")

#     user = User(id=data.user_id.lower(), name=data.name, password=None, email=payload["email"])
#     print("Creating user:", user)
#     db.add(user)
#     google_user = GoogleUsers(sub=payload["sub"], user_id=user.id)
#     db.add(google_user)

#     try:
#         print("Trying to commit to database")
#         await db.commit()
#         print("Commit successful")
#     except Exception as e:
#         print("Database error during OAuth signup:", e)
#         await db.rollback()
#         raise HTTPException(status_code=500, detail="Database error") from e

#     resp.set_cookie("oauth_signup_key", path="/authentication/oauth_signup", max_age=0)

#     return await send_login(user.id, resp)


@router.delete('/delete_account', status_code=status.HTTP_202_ACCEPTED)
async def delete_account(body : schema.Login, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    current_user.id = current_user.id.lower()
    if current_user.id != body.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    current_user = await db.get(User, current_user.id)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id doesn't exists")
    
    if not Hash.verify(body.password, current_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    await db.delete(current_user)
    await db.commit() ## TODO: delete messages too

    return {"detail": "User deleted"}

@router.patch('/logout', status_code=status.HTTP_202_ACCEPTED)
async def logout(data : schema.Logout, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    current_user = await db.get(User, current_user.id)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id doesn't exists")

    if token := data.fcm_token and current_user.fcm_tokens:
        current_user.fcm_tokens = [t for t in (current_user.fcm_tokens) if t != token]
        await db.commit()
        return {"token": "removed"}
    if not data.fcm_token or data.fcm_token.strip() == "":
        return {"token": "not necessary"}
    return {"token": "not found", "alert": "Token not found"}

@router.patch('/update_fcm_token', status_code=status.HTTP_202_ACCEPTED)
async def update_fcm_token(data: schema.UpdateFCMToken, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    current_user = await db.get(User, current_user.id)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id doesn't exists")
    
    if data.previous_token not in (current_user.fcm_tokens or []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Previous token not found")
    current_user.fcm_tokens = [t if t != data.previous_token else data.new_token for t in (current_user.fcm_tokens or [])]
    db.commit()



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