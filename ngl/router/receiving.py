from fastapi import APIRouter, Depends, HTTPException, status
from ..database import *
from .. import schema, oAuthentication
from sqlalchemy import update, select, delete, func, desc

router = APIRouter(
    prefix="/recieving",
    tags=['Receiving']
)

@router.get('/inbox', response_model=schema.Inbox, status_code=status.HTTP_200_OK)
async def get_messages_list(
    current_user: schema.UserID = Depends(oAuthentication.get_current_user),
    skip: int | None = None,
    limit: int = 100,
    last_seen_id: int | None = None,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, current_user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Cannot find such user'
        )

    # Count total messages for the user
    total_count = await db.scalar(
        select(func.count(Message.id)).where(Message.user_id == current_user.id)
    )

    # Count unread messages
    unread_count = await db.scalar(
        select(func.count(Message.id)).where(
            Message.user_id == current_user.id,
            Message.unread == True
        )
    )

    # Base query
    query = (
        select(Message)
        .where(Message.user_id == current_user.id)
        .order_by(desc(Message.id))
    )

    if limit > 0:
        query = query.limit(limit)

    if skip is not None:  
        # Use OFFSET-based pagination
        query = query.offset(skip)
    elif last_seen_id is not None:  
        # Use keyset-based pagination
        query = query.where(Message.id < last_seen_id)

    result = await db.execute(query)
    messages = result.scalars().all()

    return schema.Inbox(
        message_count=total_count,
        unread_count=unread_count,
        messages=messages
    )



# @router.get('/get_message/{id}', response_model=schema.Message)
# async def get_message(id: int, db: AsyncSession = Depends(get_db), current_user: schema.UserID = Depends(oAuthentication.get_current_user)):
#     # Atomically mark as read and return the row
#     stmt = (
#         update(Message)
#         .where(Message.id == id, Message.user_id == current_user.id)
#         # Only write if it was unread; avoids needless writes
#         .where(Message.unread.is_(True))
#         .values(unread=False)
#         .returning(Message)
#     )
#     res = await db.execute(stmt)
#     row = res.scalar_one_or_none()

#     if row is None:
#         # Could be: not found, not owned, or already read.
#         # If you want to still return the message even if already read:
#         # do a SELECT fallback.
#         sel = select(Message).where(
#             Message.id == id, Message.user_id == current_user.id
#         )
#         row = (await db.execute(sel)).scalar_one_or_none()
#         if row is None:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        
#     await db.commit()
#     return row  ## TODO: revise

@router.delete('/delete_message/{id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_message(id: int, db: AsyncSession = Depends(get_db), current_user: schema.UserID = Depends(oAuthentication.get_current_user)):
    stmt = (
        delete(Message)
        .where(Message.id == id, Message.user_id == current_user.id)
    )
    await db.execute(stmt)
    await db.commit()
    return

@router.patch('/mark_unread/{id}', status_code=status.HTTP_202_ACCEPTED)
async def mark_as_unread(id: int, db: AsyncSession = Depends(get_db), current_user: schema.UserID = Depends(oAuthentication.get_current_user)):
    stmt = (
        update(Message)
        .where(Message.id == id, Message.user_id == current_user.id)
        .values(unread=True)
    )
    await db.execute(stmt)
    await db.commit()
    return

@router.patch('/mark_read/{id}', status_code=status.HTTP_202_ACCEPTED)
async def mark_as_read(id: int, db: AsyncSession = Depends(get_db), current_user: schema.UserID = Depends(oAuthentication.get_current_user)):
    stmt = (
        update(Message)
        .where(Message.id == id, Message.user_id == current_user.id)
        .values(unread=False)
    )
    await db.execute(stmt)
    await db.commit()
    return