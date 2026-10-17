import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    sender_id: uuid.UUID
    body: str
    created_at: datetime


class ConversationOut(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    post_title: str
    other_user_id: uuid.UUID
    other_display_name: str
    last_message: MessageOut | None
    created_at: datetime
