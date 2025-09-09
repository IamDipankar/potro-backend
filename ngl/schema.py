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

class Inbox(BaseModel):
    id: str
    message_count : int
    unread_count : int
    messages: List[MessageInboxItem]


class Signup(BaseModel):
    id: str
    name: str
    password : str

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
    token: str