import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Allows optional spaces — validates raw LLM output before normalization
TURKISH_PLATE_PATTERN = re.compile(r"^\d{2}\s?[A-Z]{1,3}\s?\d{2,4}$")


class PlateRecognizer:
    def __init__(self, litellm_base_url: str, model: str, api_key: str = ""):
        self.litellm_base_url = litellm_base_url
        self.model = model
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.litellm_base_url,
                timeout=settings.litellm_timeout,
                headers=headers,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _call_litellm(self, image_b64: str) -> str:
        client = await self._get_client()
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Read the license plate text in this image. "
                                    "Return ONLY the plate text, nothing else."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                },
                            },
                        ],
                    }
                ],
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    def _sanitize_llm_output(self, raw_text: str) -> str:
        """Strip LLM artifacts: quotes, markdown, explanation text."""
        text = raw_text.strip().strip("\"'`")
        # Take only the first line (LLM sometimes adds explanations)
        text = text.split("\n")[0].strip()
        # Remove non-alphanumeric except spaces
        text = re.sub(r"[^A-Za-z0-9\s]", "", text)
        # Uppercase and limit length
        text = text.upper()[: settings.max_plate_length]
        return text

    def _compute_confidence(self, text: str) -> float:
        cleaned = text.replace(" ", "").upper()
        if TURKISH_PLATE_PATTERN.match(cleaned):
            return settings.high_confidence_threshold
        if re.match(r"^\d{2}", cleaned) and len(cleaned) >= 6:
            return settings.medium_confidence_threshold
        return settings.low_confidence_threshold

    async def recognize(self, image_b64: str) -> dict:
        raw_text = await self._call_litellm(image_b64)
        plate_text = self._sanitize_llm_output(raw_text)

        if raw_text != plate_text:
            logger.info("Sanitized LLM output: %r -> %r", raw_text, plate_text)

        confidence = self._compute_confidence(plate_text)
        format_valid = bool(TURKISH_PLATE_PATTERN.match(plate_text.replace(" ", "").upper()))

        return {
            "plate_text": plate_text,
            "confidence": round(confidence, 2),
            "format_valid": format_valid,
        }
