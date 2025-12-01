"""
AI service for vision analysis using OpenAI.
"""

from openai import OpenAI
from typing import Optional, Dict
from ..config import settings


class AIService:
    """Service for AI-powered incident detection using OpenAI Vision API."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.vision_model = settings.OPENAI_VISION_MODEL

    async def analyze_frame(self, image_base64: str) -> Dict[str, any]:
        """
        Analyze a video frame for incidents.

        Args:
            image_base64: Base64 encoded image

        Returns:
            Dict with incident_detected, type, severity, description, confidence
        """
        try:
            prompt = """
Analyze this image from a taxi camera. Identify any safety concerns or incidents:

- Accidents or collisions
- Harsh braking
- Aggressive driving
- Driver drowsiness or distraction
- Phone usage while driving
- Seatbelt not worn
- Any unusual or dangerous situations

Respond in JSON format:
{
    "incident_detected": true/false,
    "type": "ACCIDENT|HARSH_BRAKING|DROWSINESS|DISTRACTION|PHONE_USAGE|OTHER",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "description": "Brief description",
    "confidence": 0-100
}
"""

            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )

            # Parse response
            result_text = response.choices[0].message.content

            # Try to parse JSON from response
            import json
            try:
                result = json.loads(result_text)
            except:
                # If not valid JSON, return safe default
                result = {
                    "incident_detected": False,
                    "type": "OTHER",
                    "severity": "LOW",
                    "description": "Could not analyze frame",
                    "confidence": 0
                }

            return result

        except Exception as e:
            print(f"AI analysis error: {str(e)}")
            return {
                "incident_detected": False,
                "type": "OTHER",
                "severity": "LOW",
                "description": f"Error: {str(e)}",
                "confidence": 0
            }


# Global instance
ai_service = AIService()
