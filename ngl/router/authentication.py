from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from ..database import *
from .. import schema, oAuth
from ..hashing import Hash

router = APIRouter(
    prefix="/authentication",
    tags = ["Authentication"]
)

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

    resp.set_cookie(
        key = "refresh_token",
        value = await oAuth.create_refresh_token(data),
        max_age = oAuth.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        httponly = True,
        # secure=True,
        samesite="strict",
        path='/authentication/refresh'
    )

    return { 
        "access_token" : await oAuth.create_access_token(data),
        "refresh_token" : await oAuth.create_refresh_token(data),
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


    resp.set_cookie(
        key = "refresh_token",
        value = await oAuth.create_refresh_token(data),
        max_age = oAuth.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        httponly = True,
        # secure=True,
        samesite="strict",
        path='/authentication/refresh'
    )

    return{ 
        "access_token" : await oAuth.create_access_token(data),
        "refresh_token" : await oAuth.create_refresh_token(data),
        "token_type" : "bearer"
    }