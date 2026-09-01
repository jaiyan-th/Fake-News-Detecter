"""
Groq LLM Client Wrapper with JSON Mode, Retries, and Error Handling
"""

import json
import logging
from typing import Dict, Any, List, Optional
from groq import Groq
from backend.core.config import settings
from backend.core.exceptions import LLMServiceError

logger = logging.getLogger("news_verification.groq_service")


class GroqService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client: Optional[Groq] = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq client successfully initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.warning("GROQ_API_KEY is not set. LLM workflows will operate in fallback mode.")

    def is_available(self) -> bool:
        return self.client is not None

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        Calls Groq ChatCompletion enforcing JSON object response.
        """
        if not self.client:
            raise LLMServiceError("Groq API key is not configured or client is unavailable.")

        selected_model = model or settings.GROQ_MODEL
        for attempt in range(settings.GROQ_MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=settings.GROQ_TIMEOUT_SECONDS
                )
                raw_content = response.choices[0].message.content
                return json.loads(raw_content)
            except json.JSONDecodeError as je:
                logger.warning(f"Groq returned non-JSON output on attempt {attempt+1}: {je}")
                if attempt == settings.GROQ_MAX_RETRIES - 1:
                    raise LLMServiceError(f"Malformed JSON response from LLM: {str(je)}")
            except Exception as e:
                logger.warning(f"Groq API call attempt {attempt+1} failed ({selected_model}): {e}")
                # Try fallback model on final attempt if different
                if attempt == settings.GROQ_MAX_RETRIES - 2 and selected_model != settings.GROQ_REASONING_MODEL:
                    selected_model = settings.GROQ_REASONING_MODEL
                    logger.info(f"Retrying with secondary model {selected_model}")
                if attempt == settings.GROQ_MAX_RETRIES - 1:
                    raise LLMServiceError(f"Groq API failure after {settings.GROQ_MAX_RETRIES} attempts: {str(e)}")

        raise LLMServiceError("Failed to obtain valid LLM response from Groq.")
