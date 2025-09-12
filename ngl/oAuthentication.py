from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from . import schema
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

import dotenv
import os
dotenv.load_dotenv()

SECRET_KEY = str(os.getenv("SECRET_KEY"))
REFRESH_TOKEN_SECRET_KEY = str(os.getenv("REFRESH_TOKEN_SECRET_KEY"))

if SECRET_KEY in [None, "None"] or REFRESH_TOKEN_SECRET_KEY in [None, "None"]:
    raise ValueError("Key not available")
else:
    print("Keys loaded")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "2"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days default

async def create_access_token(data: dict, expire_delta_minutes: float | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes= expire_delta_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    jwt_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return jwt_token

async def create_refresh_token(data : dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    jwt_token = jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    return jwt_token

async def verify_jwt(token: str, exception: HTTPException, secret_key : str = SECRET_KEY):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        if not payload.get("id") or not payload.get("role"):
            print("here1")
            raise exception
        return schema.UserID(id=payload['id'])
    except JWTError as e:
        print("here2")
        print("JWT verification failed with error: \n", e)
        raise exception
    
password_bearer = OAuth2PasswordBearer(tokenUrl="/authentication/login")

async def get_current_user(token: dict = Depends(password_bearer)):
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )

    return await verify_jwt(token, exception)

def decode_jwt(token: str, secret_key: str = SECRET_KEY, algorithms: list = [ALGORITHM]):
    try:
        payload = jwt.decode(token, secret_key, algorithms=algorithms)
        return payload
    except JWTError as e:
        print("JWT decoding failed with error: \n", e)
        return None 