"""
OpenAI Integration Service for TaxiWatch
Handles chat interactions and AI-powered analysis
"""
from openai import OpenAI
import os
from typing import List, Dict, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


class ChatService:
    """Service for AI chat interactions."""

    SYSTEM_PROMPT = """You are an AI assistant for TaxiWatch, a fleet management system.

Your role is to help fleet managers and dispatchers with:
- Vehicle status inquiries
- Driver information
- Trip and route optimization
- Incident reporting and analysis
- Real-time fleet monitoring assistance
- Performance metrics interpretation

Be professional, concise, and helpful. When users ask about specific vehicles, drivers, or trips,
acknowledge that you can help them access that information through the system.

If you don't have specific data, guide users on how to find it in the TaxiWatch dashboard.

Use the provided FAQs to answer common questions when applicable.
"""

    @staticmethod
    async def load_faqs(db: AsyncSession) -> str:
        """
        Load active FAQs from database and format for context.

        Args:
            db: Database session

        Returns:
            Formatted FAQ string
        """
        try:
            from ..models.faq import FAQ

            result = await db.execute(
                select(FAQ).where(FAQ.is_active == True).order_by(FAQ.priority.desc())
            )
            faqs = result.scalars().all()

            if not faqs:
                return ""

            faq_text = "\n\nFrequently Asked Questions:\n"
            for faq in faqs:
                faq_text += f"\nQ: {faq.question}\nA: {faq.answer}\n"

            return faq_text

        except Exception as e:
            logger.error(f"Error loading FAQs: {e}")
            return ""

    @staticmethod
    def get_response(
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict] = None
    ) -> str:
        """
        Get AI response for user message.
        
        Args:
            message: User's message
            conversation_history: Previous messages in conversation
            context: Additional context (vehicle data, stats, etc.)
        
        Returns:
            AI-generated response
        """
        try:
            # Build messages array
            messages = [{"role": "system", "content": ChatService.SYSTEM_PROMPT}]
            
            # Add conversation history if available
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add context if available
            if context:
                context_text = ChatService._format_context(context)
                messages.append({
                    "role": "system",
                    "content": f"Current fleet context:\n{context_text}"
                })
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback response
            return ChatService._get_fallback_response(message)
    
    @staticmethod
    def _format_context(context: Dict) -> str:
        """Format context data into readable text."""
        parts = []
        
        if "total_vehicles" in context:
            parts.append(f"Total vehicles in fleet: {context['total_vehicles']}")
        
        if "active_vehicles" in context:
            parts.append(f"Currently active: {context['active_vehicles']}")
        
        if "total_trips" in context:
            parts.append(f"Trips today: {context['total_trips']}")
        
        if "alerts" in context:
            parts.append(f"Active alerts: {context['alerts']}")
        
        return "\n".join(parts) if parts else "No additional context available"
    
    @staticmethod
    def _get_fallback_response(message: str) -> str:
        """Provide fallback response when OpenAI is unavailable."""
        message_lower = message.lower()
        
        # Simple keyword-based responses
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "Hello! I'm the TaxiWatch AI assistant. How can I help you manage your fleet today?"
        
        elif any(word in message_lower for word in ["vehicle", "taxi", "car"]):
            return "I can help you with vehicle information. You can view all vehicles in the Vehicles section, or ask me about specific vehicle status, location, or maintenance."
        
        elif any(word in message_lower for word in ["driver", "drivers"]):
            return "I can assist with driver-related queries. Would you like to know about driver performance, assignments, or availability?"
        
        elif any(word in message_lower for word in ["trip", "trips", "route"]):
            return "For trip information, I can help you analyze routes, view trip history, or optimize future trips. What would you like to know?"
        
        elif any(word in message_lower for word in ["alert", "incident", "problem"]):
            return "I can help you review alerts and incidents. Check the dashboard for active alerts, or let me know if you need details about specific incidents."
        
        elif any(word in message_lower for word in ["status", "overview", "summary"]):
            return "You can view your fleet status on the main dashboard. It shows active vehicles, current trips, and any alerts that need attention."
        
        else:
            return """I'm the TaxiWatch AI assistant. I can help you with:

• Vehicle status and location
• Driver information and performance
• Trip history and analytics
• Incident reports and alerts
• Fleet optimization suggestions

What would you like to know?"""


class VisionService:
    """Service for AI vision analysis (future implementation)."""
    
    @staticmethod
    def analyze_frame(image_data: bytes, prompt: str = "") -> Dict:
        """
        Analyze video frame for incidents.
        
        Args:
            image_data: Image bytes
            prompt: Custom analysis prompt
        
        Returns:
            Analysis results
        """
        # TODO: Implement OpenAI Vision API integration
        # This would analyze video frames for:
        # - Accidents
        # - Harsh braking
        # - Driver behavior
        # - Object detection
        
        return {
            "detected": False,
            "confidence": 0.0,
            "description": "Vision analysis not yet implemented"
        }
