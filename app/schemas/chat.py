from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        examples=["Which department has the highest average salary?"],
    )


class ChatResponse(BaseModel):
    question: str
    answer: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    id: int
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryListResponse(BaseModel):
    conversations: List[ChatHistoryResponse]
    total: int
