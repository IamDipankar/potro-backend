from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..database import *
from datetime import datetime
from .. import schema
from fastapi.responses import FileResponse
import requests

router = APIRouter(
    prefix="/sending",
    tags=['Sending']
)

@router.get("/")
async def send_page():
    return FileResponse("pages/send.html")

@router.get('/{user_id}', status_code=status.HTTP_200_OK, response_model=schema.ShowUserOnly)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id.lower())
    if user:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User does not exist')

@router.post('/{user_id}', status_code=status.HTTP_201_CREATED)
async def add_message(user_id: str, message: str, db: AsyncSession = Depends(get_db)):
    # Getting ip address
    # x_forwarded_for = request.headers.get("X-Forwarded-For")
    # if x_forwarded_for:
    #     client_ip = x_forwarded_for.split(",")[0]  # first IP is real client
    # else:
    #     client_ip = request.client.host

    
    user_id = user_id.lower()
    if await db.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User does not exist')
    current_time = datetime.now().isoformat()
    message = Message(user_id=user_id, content=message, time=current_time)
    db.add(message)
    await db.commit()
    return {'detail': 'Success'}