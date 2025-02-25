from typing import Dict, List
from Backend.ai_services.nlp_service.nlp_service import NLPService
from Backend.core.config import settings
from Backend.utils.cache_utils import cache_response
from Backend.utils.logging_utils import get_logger
import aiohttp

logger = get_logger(__name__)

class EmotionService:
    def __init__(self):
        self.nlp_service = NLPService()
        self.api_key = settings.EMOTION_API_KEY
        self.base_url = settings.EMOTION_API_BASE_URL
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
        return self.session

    @cache_response(ttl=3600)
    async def analyze_emotion(self, text: str) -> Dict:
        """Analyze the emotional content of text using external API."""
        try:
            session = await self._get_session()
            async with session.post(f"{self.base_url}/emotion", json={"text": text}) as response:
                response.raise_for_status()
                result = await response.json()
                emotion_result = {
                    "emotion": result["emotion"],
                    "confidence": float(result["confidence"])
                }
            
            # Get additional sentiment context
            sentiment = await self.nlp_service.analyze_sentiment(text)
            
            return {
                **emotion_result,
                "sentiment": sentiment["sentiment"],
                "sentiment_confidence": sentiment["confidence"]
            }
        except Exception as e:
            logger.error(f"Error analyzing emotion: {str(e)}")
            raise

    @cache_response(ttl=3600)
    async def get_emotional_context(self, text: str) -> Dict:
        """Get comprehensive emotional analysis including sentiment and key phrases."""
        try:
            emotion = await self.analyze_emotion(text)
            keywords = await self.nlp_service.extract_keywords(text)
            
            return {
                "emotion": emotion,
                "key_phrases": keywords,
                "intensity": "high" if emotion["confidence"] > 0.8 else "medium" if emotion["confidence"] > 0.5 else "low"
            }
        except Exception as e:
            logger.error(f"Error getting emotional context: {str(e)}")
            raise

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()