from fastapi import APIRouter, Depends, HTTPException, status
from ..database import *
from .. import schema, oAuth
from sqlalchemy import update, select

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
    return messages ## updated


@router.get('/get_message/{id}', response_model=schema.Message)
async def get_message(id: int, db: AsyncSession = Depends(get_db), current_user: schema.UserID = Depends(oAuth.get_current_user)):
    # Atomically mark as read and return the row
    stmt = (
        update(Message)
        .where(Message.id == id, Message.user_id == current_user.id)
        # Only write if it was unread; avoids needless writes
        .where(Message.unread.is_(True))
        .values(unread=False)
        .returning(Message)
    )
    res = await db.execute(stmt)
    row = res.scalar_one_or_none()

    if row is None:
        # Could be: not found, not owned, or already read.
        # If you want to still return the message even if already read:
        # do a SELECT fallback.
        sel = select(Message).where(
            Message.id == id, Message.user_id == current_user.id
        )
        row = (await db.execute(sel)).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        
    await db.commit()
    return row