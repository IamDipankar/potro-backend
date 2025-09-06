from fastapi import APIRouter, Depends, HTTPException, status
from ..database import *
from datetime import datetime
from .. import schema

router = APIRouter(
    prefix="/sending",
    tags=['Sending']
)


@router.get('/{user_id}', status_code=status.HTTP_200_OK, response_model=schema.ShowUserOnly)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id.lower())
    if user:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User does not exist')

@router.post('/{user_id}', status_code=status.HTTP_201_CREATED, response_model=schema.ShortCommunication)
async def add_message(user_id: str, message: str, db: AsyncSession = Depends(get_db)):
    user_id = user_id.lower()
    if await db.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User does not exist')
    current_time = datetime.now().isoformat()
    message = Message(user_id=user_id, content=message, time=current_time)
    db.add(message)
    await db.commit()
    return {'detail': 'Success'}