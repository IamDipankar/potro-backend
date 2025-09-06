from fastapi import APIRouter, Depends, HTTPException, status
from ..database import *
from .. import schema, oAuth

router = APIRouter(
    prefix="/recieving",
    tags=['Receiving']
)

@router.get('/inbox', response_model=schema.Inbox, status_code=status.HTTP_200_OK)
async def get_messages_list(current_user: schema.UserID = Depends(oAuth.get_current_user), skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    if await db.get(User, current_user.id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot find such user')
    # messages = await db.execute(
    #     select(Message).where(Message.user_id == user_id).offset(skip).limit(limit)
    # )
    messages = await db.get(User, current_user.id)
    return messages


@router.get('/get_message/{id}', response_model=schema.Message)
async def get_message(id: int, db: AsyncSession = Depends(get_db), current_user: schema.UserID = Depends(oAuth.get_current_user)):
    message = await db.get(Message, id)
    if message:
        if message.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not authorized to view this message')
        return message
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='You are not authorized to view this message')
