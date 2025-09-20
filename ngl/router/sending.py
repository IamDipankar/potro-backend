from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..database import *
from datetime import datetime
from .. import schema
from fastapi.responses import FileResponse
import requests
import firebase_admin as fbad
import asyncio
from firebase_admin import messaging

router = APIRouter(
    prefix="/sending",
    tags=['Sending']
)

# @router.get("/")
# async def send_page():
#     return FileResponse("pages/send.html")

@router.get('/{user_id}', status_code=status.HTTP_302_FOUND, response_model=schema.ShowUserOnly)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id.lower())
    if user:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User does not exist')

@router.post('/{user_id}', status_code=status.HTTP_202_ACCEPTED)
async def add_message(user_id: str, message: str, db: AsyncSession = Depends(get_db)):
    # Getting ip address
    # x_forwarded_for = request.headers.get("X-Forwarded-For")
    # if x_forwarded_for:
    #     client_ip = x_forwarded_for.split(",")[0]  # first IP is real client
    # else:
    #     client_ip = request.client.host

    
    user_id = user_id.lower()
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User does not exist')
    current_time = datetime.now().isoformat()
    message = Message(user_id=user_id, content=message, time=current_time)
    db.add(message)
    await db.commit()
    db.refresh(message)

    if user.fcm_tokens:
        message = messaging.MulticastMessage(
            data={
                "id": str(message.id),
                "time": str(current_time),
                "content": message.content,
            },
            notification = messaging.Notification(
                title = "New Message"
            ),
            tokens = user.fcm_tokens
        )

        response = await messaging.send_each_for_multicast_async(message)
        if response.failure_count > 0:
            user.fcm_tokens = [token for resp, token in zip(response.responses, user.fcm_tokens) if resp.success]
    await db.commit()

    return