from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..database import *
from datetime import datetime
from .. import schema
from fastapi.responses import FileResponse
import requests
import firebase_admin as fbad
import asyncio
from firebase_admin import messaging
from ..timer import *
from time import sleep

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

# @router.post('/{user_id}', status_code=status.HTTP_202_ACCEPTED)
# async def add_message(user_id: str, message: str, db: AsyncSession = Depends(get_db)):
#     # Getting ip address
#     # Checkpoint
#     x_forwarded_for = request.headers.get("X-Forwarded-For")
#     if x_forwarded_for:
#         client_ip = x_forwarded_for.split(",")[0]  # first IP is real client
#     else:
#         client_ip = request.client.host

#     # checkpoint
#     user_id = user_id.lower()
#     # checkpoint
#     user = await db.get(User, user_id)
#     # checkpoint
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User does not exist')
#     current_time = datetime.now().isoformat()
#     # checkpoint
#     message = Message(user_id=user_id, content=message, time=current_time)
#     db.add(message)
#     # checkpoint
#     await db.commit()
#     # checkpoint
#     db.refresh(message)
#     # checkpoint

#     if user.fcm_tokens:
#         message = messaging.MulticastMessage(
#             data={
#                 "id": str(message.id),
#                 "time": str(current_time),
#                 "content": message.content,
#             },
#             notification = messaging.Notification(
#                 title = "New Message"
#             ),
#             tokens = user.fcm_tokens
#         )

#         response = await messaging.send_each_for_multicast_async(message)
#         if response.failure_count > 0:
#             user.fcm_tokens = [token for resp, token in zip(response.responses, user.fcm_tokens) if resp.success]
#     await db.commit()
#     # checkpoint

#     return


@router.post('/{user_id}', status_code=status.HTTP_202_ACCEPTED)
async def add_message(user_id: str, message: str, request: Request, db: AsyncSession = Depends(get_db)):
    t = CheckTimer("add_message")

    # Getting ip address
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0]  # first IP is real client
    else:
        client_ip = request.client.host
    t.cp("resolved client_ip")

    user_id = user_id.lower()
    t.cp("normalized user_id")

    user = await db.get(User, user_id)
    t.cp("db.get(User)")

    if user is None:
        t.cp("user not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User does not exist')

    current_time = datetime.now().isoformat()
    msg = Message(user_id=user_id, content=message, time=current_time)
    db.add(msg)
    t.cp("db.add(message)")

    # sleep(1)
    # t.cp("simulated delay")

    # await asyncio.sleep(1)
    # t.cp("simulated async delay")

    # await db.commit()
    # t.cp("db.commit() after insert")

    # await db.refresh(msg)
    # t.cp("db.refresh(message)")

    if user.fcm_tokens:
        multicast = messaging.MulticastMessage(
            data={
                "id": str(user_id),
                "time": str(current_time),
                "content": message,
            },
            notification=messaging.Notification(title="New Message"),
            tokens=user.fcm_tokens
        )
        t.cp("prepared FCM multicast")
        # async send
        response = await messaging.send_each_for_multicast_async(multicast)
        t.cp("FCM Response Time")

        if response.failure_count > 0:
            user.fcm_tokens = [token for resp, token in zip(response.responses, user.fcm_tokens) if resp.success]
            t.cp("filtered bad FCM tokens")
    else:
        t.cp("no FCM tokens")

    await db.commit()
    t.cp("final db.commit()")

    return 