from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.chat_history import ChatHistory
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatHistoryListResponse
from app.middleware.auth import get_current_user
from app.ai.agent import chat_with_agent

router = APIRouter(prefix="/api/ai", tags=["AI Agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ask the AI agent a question about your data."""

    # Run the agent
    answer = await chat_with_agent(
        question=data.question,
        db=db,
        user_id=current_user.id,
        user_role=current_user.role,
    )

    # Save to chat history
    history_entry = ChatHistory(
        user_id=current_user.id,
        question=data.question,
        answer=answer,
    )
    db.add(history_entry)
    await db.flush()
    await db.refresh(history_entry)

    return ChatResponse(
        question=data.question,
        answer=answer,
        created_at=history_entry.created_at or datetime.now(timezone.utc),
    )


@router.get("/history", response_model=ChatHistoryListResponse)
async def get_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for the current user."""
    query = select(ChatHistory).where(ChatHistory.user_id == current_user.id)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.order_by(ChatHistory.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    conversations = result.scalars().all()

    return ChatHistoryListResponse(
        conversations=[ChatHistoryResponse.model_validate(c) for c in conversations],
        total=total,
    )
