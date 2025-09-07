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

class MessageTimeOnly(BaseModel):
    id : int
    time : str

class Inbox(BaseModel):
    id: str
    messages: List[MessageTimeOnly]


class Signup(BaseModel):
    id: str
    name: str
    password : str

class UserID(BaseModel):
    id : str

class Message(BaseModel):
    time: str
    user: UserID
    content: str

class RefreshToken(BaseModel):
    token: str