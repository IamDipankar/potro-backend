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

dotenv.load_dotenv()

templates = Jinja2Templates(directory="pages")

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


async def set_refresh_token_cookie(resp: Response, data: dict) -> Response:
    resp.set_cookie(
        key="refresh_token",
        value=await oAuthentication.create_refresh_token(data),
        max_age=oAuthentication.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,  ### !!! Danger: recheck before production
        # secure=True,  ### !!! Danger: recheck before production
        samesite="strict", ### !!! Danger: recheck before production
        path='/authentication/refresh'
    )
    return resp

async def send_login(user_id):
    data = {
        "id": user_id,
        "role": "user"
    }

    resp = await set_refresh_token_cookie(resp, data)
    for name, value in resp.headers.items():
        if name.lower() == 'set-cookie':
            print(f"Set-Cookie: {value}")
    print("=" * 50)

    return {
        "access_token": await oAuthentication.create_access_token(data),
        "token_type": "Bearer"
    }
## dropping due to samesite none and not secure

async def generate_user_id(email: str, db: AsyncSession = Depends(get_db)) -> str:
    base_id = email.split('@')[0]
    while await db.get(User, base_id):
        base_id += "." + str(int.from_bytes(os.urandom(2), 'big'))
    
    return base_id

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
    print("Login called")
    user = await db.get(User, request.username.lower())
    if not user or not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    return await send_login(user.id)

@router.post('/refresh')
async def refresh_token(resp: Response, request: Request, db: AsyncSession = Depends(get_db)):
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials'
    )
    token = request.cookies.get("refresh_token")
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
        "role": "user"
    }


    resp = await set_refresh_token_cookie(resp, data)

    return {
        "access_token": await oAuthentication.create_access_token(data),
        # "refresh_token": await oAuth.create_refresh_token(data),
        "token_type": "Bearer"
    }

@router.get("/login/google")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback/google")
async def google_auth(request: Request, resp: Response, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        # token contains access_token, id_token, etc.
        userinfo = token.get("userinfo")
        # If userinfo not present, fetch explicitly:
        if not userinfo:
            userinfo = await oauth.google.parse_id_token(request, token)
        if not userinfo:
            raise HTTPException(status_code=400, detail="Failed to obtain user info")

        # Check if user with this Google sub exists
        google_login = await db.execute(
            select(GoogleUsers).where(GoogleUsers.sub == int(userinfo["sub"]))
        )

        google_login = google_login.scalars().first()
        if google_login:
            user = await db.get(User, google_login.user_id)
            if user:
                return await send_login(user.id)
            else:
                name = userinfo.get("name")
                email = userinfo.get("email")
                suggested_id = await generate_user_id(userinfo["email"], db)

                resp.set_cookie("oauth_signup_key", 
                                value= await oAuthentication.create_access_token({
                                                                                "signature": os.getenv("SIGNATURE"),
                                                                                "sub": userinfo["sub"],
                                                                                "email": email,
                                                                                }), 
                                max_age=300, 
                                httponly=True, 
                                samesite="strict", 
                                path="/authentication/oauth_signup")

                return templates.TemplateResponse("oauthSignup.html", {
                                                        "request": request,
                                                        "name": name,
                                                        "suggested_id": suggested_id
                                                    })

    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {e.error}") from e
    return RedirectResponse(url="/")


@router.post("/oauth_signup")
async def oauth_signup(request: Request, data: schema.OAuthSignup, resp: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("oauth_signup_key")
    if not token:
        raise HTTPException(status_code=401, detail="Missing or expired signup token")

    payload = oAuthentication.decode_jwt(token)
    if payload is None or payload.get("signature") != os.getenv("SIGNATURE"):
        raise HTTPException(status_code=401, detail="Invalid signup token")

    if payload.get("sub") is None or payload.get("email") is None:
        raise HTTPException(status_code=401, detail="Invalid signup token")

    if await db.get(User, data.user_id.lower()):
        raise HTTPException(status_code=400, detail="User ID already exists")

    user = User(id=data.user_id.lower(), name=data.name, password=None, email=payload["email"])
    db.add(user)
    google_user = GoogleUsers(sub=payload["sub"], user_id=user.id)
    db.add(google_user)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from e

    resp.delete_cookie("oauth_signup_key", path="/authentication/oauth_signup")

    return await send_login(user.id)








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