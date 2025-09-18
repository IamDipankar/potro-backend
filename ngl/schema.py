from pydantic import BaseModel
from typing import List


class CommunicationMessage(BaseModel):
    detail : str
    health: str = "Good"

class ShortCommunication(BaseModel):
    detail : str

class ShowUserOnly(BaseModel):
    id: str
    name : str

class MessageInboxItem(BaseModel):
    id : int
    time : str
    unread : bool

    class Config:
        from_attributes = True

class MessageItem(BaseModel):
    id : int
    time : str
    unread : bool
    content : str

    class Config:
        from_attributes = True

class Inbox(BaseModel):
    message_count : int
    unread_count : int
    messages: List[MessageItem]

    class Config:
        from_attributes = True


class Signup(BaseModel):
    id: str
    name: str | None = None
    password : str
    email : str | None = None

class UserID(BaseModel):
    id : str

class FullMessage(BaseModel):
    time: str
    user: UserID
    content: str
    unread: bool

class Message(BaseModel):
    time: str
    content: str

class RefreshToken(BaseModel):
    refresh_token: str | None = None

class OAuthSignup(BaseModel):
    user_id: str
    name: str

class Password(BaseModel):
    user_id: str
    password: str