"""
OpenAI Vision API Service for incident detection.
"""

from openai import OpenAI
import os
import base64
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


class VisionService:
    """Service for AI vision analysis using OpenAI Vision API."""

    INCIDENT_DETECTION_PROMPT = """You are an AI safety analyst for TaxiWatch, analyzing taxi camera footage for safety incidents.

Analyze this image and detect any of the following incidents:
- Accidents or collisions
- Harsh braking or sudden stops
- Aggressive or reckless driving
- Driver drowsiness or fatigue
- Driver distraction (phone usage, looking away)
- Traffic violations
- Dangerous road conditions

Respond in JSON format with:
{
  "incident_detected": boolean,
  "incident_type": "ACCIDENT|HARSH_BRAKING|SPEEDING|AGGRESSIVE_DRIVING|DROWSINESS|DISTRACTION|PHONE_USAGE|OTHER",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "confidence": 0-100,
  "description": "detailed description of what you observed",
  "recommendations": "suggested actions"
}

If no incident is detected, set incident_detected to false."""

    @staticmethod
    def analyze_image(
        image_data: bytes,
        prompt: Optional[str] = None,
        detail_level: str = "high"
    ) -> Dict:
        """
        Analyze an image for incidents using OpenAI Vision API.

        Args:
            image_data: Image bytes
            prompt: Custom analysis prompt (optional)
            detail_level: "low" or "high" (affects cost and quality)

        Returns:
            Analysis results dictionary
        """
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # Use custom prompt or default
            analysis_prompt = prompt or VisionService.INCIDENT_DETECTION_PROMPT

            # Call OpenAI Vision API
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # gpt-4o-mini supports vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": detail_level
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.2  # Lower temperature for more consistent analysis
            )

            # Parse response
            result_text = response.choices[0].message.content

            # Try to parse as JSON
            import json
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # If not JSON, create structured response
                result = {
                    "incident_detected": False,
                    "incident_type": "OTHER",
                    "severity": "LOW",
                    "confidence": 50,
                    "description": result_text,
                    "recommendations": "Manual review required"
                }

            logger.info(f"Vision analysis complete: {result.get('incident_detected', False)}")
            return result

        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return VisionService._get_fallback_response()

    @staticmethod
    def analyze_driver_behavior(image_data: bytes) -> Dict:
        """
        Specifically analyze driver behavior.

        Args:
            image_data: Image bytes showing driver

        Returns:
            Driver behavior analysis
        """
        prompt = """Analyze this image of a taxi driver and assess:
1. Alertness level (awake, drowsy, asleep)
2. Attention to road (focused, distracted, looking away)
3. Phone usage (yes/no)
4. Seatbelt usage (yes/no)
5. Any safety concerns

Respond in JSON format with:
{
  "alertness": "ALERT|DROWSY|ASLEEP",
  "attention": "FOCUSED|DISTRACTED|LOOKING_AWAY",
  "phone_usage": boolean,
  "seatbelt": boolean,
  "safety_score": 0-100,
  "concerns": "list of concerns",
  "recommendations": "suggested actions"
}"""

        return VisionService.analyze_image(image_data, prompt=prompt)

    @staticmethod
    def analyze_road_conditions(image_data: bytes) -> Dict:
        """
        Analyze road and traffic conditions.

        Args:
            image_data: Image bytes showing road view

        Returns:
            Road conditions analysis
        """
        prompt = """Analyze this road scene and assess:
1. Traffic density (light, moderate, heavy)
2. Weather conditions
3. Road conditions (clear, wet, icy, damaged)
4. Visibility level
5. Potential hazards

Respond in JSON format with:
{
  "traffic_density": "LIGHT|MODERATE|HEAVY",
  "weather": "CLEAR|RAIN|FOG|SNOW|OTHER",
  "road_condition": "CLEAR|WET|ICY|DAMAGED",
  "visibility": "GOOD|MODERATE|POOR",
  "hazards": ["list of detected hazards"],
  "risk_level": "LOW|MEDIUM|HIGH"
}"""

        return VisionService.analyze_road_conditions(image_data, prompt=prompt)

    @staticmethod
    def batch_analyze(images: List[bytes]) -> List[Dict]:
        """
        Analyze multiple images in batch.

        Args:
            images: List of image bytes

        Returns:
            List of analysis results
        """
        results = []
        for idx, image_data in enumerate(images):
            logger.info(f"Analyzing image {idx + 1}/{len(images)}")
            result = VisionService.analyze_image(image_data)
            results.append(result)

        return results

    @staticmethod
    def _get_fallback_response() -> Dict:
        """Provide fallback response when Vision API is unavailable."""
        return {
            "incident_detected": False,
            "incident_type": "OTHER",
            "severity": "LOW",
            "confidence": 0,
            "description": "Vision analysis unavailable - API error or missing API key",
            "recommendations": "Manual review required",
            "error": "Vision API unavailable"
        }


# Convenience function for quick analysis
def analyze_incident(image_data: bytes) -> Dict:
    """Quick function to analyze an image for incidents."""
    return VisionService.analyze_image(image_data)
