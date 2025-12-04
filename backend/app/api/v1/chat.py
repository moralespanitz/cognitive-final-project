"""
AI Chat API endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ...database import get_db
from ...schemas.chat import ChatMessage, ChatResponse
from ...dependencies import get_current_user
from ...models.user import User
from ...models.vehicle import Vehicle
from ...services.openai_service import ChatService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send message to AI assistant.
    Returns AI-generated response about fleet operations with OpenAI integration.
    """
    # Get current fleet context
    context = {}

    try:
        # Count total vehicles
        total_vehicles_query = select(func.count(Vehicle.id))
        result = await db.execute(total_vehicles_query)
        context["total_vehicles"] = result.scalar()

        # Count active vehicles
        active_vehicles_query = select(func.count(Vehicle.id)).where(Vehicle.status == "ACTIVE")
        result = await db.execute(active_vehicles_query)
        context["active_vehicles"] = result.scalar()

        # Add more context as needed
        context["total_trips"] = 0  # TODO: Get from trips table
        context["alerts"] = 0  # TODO: Get from alerts table

    except Exception as e:
        # If context fetch fails, continue without it
        pass

    # Load FAQs from database
    faq_context = await ChatService.load_faqs(db)

    # Get AI response with context and FAQs
    ai_response = await ChatService.get_response_async(
        message=message.message,
        context=context,
        faq_context=faq_context,
        db=db
    )

    return ChatResponse(
        response=ai_response,
        message=message.message
    )


@router.get("/health")
async def chat_health():
    """Check if chat service is available."""
    return {
        "status": "ok",
        "service": "AI Chat",
        "openai_integration": "pending"
    }
