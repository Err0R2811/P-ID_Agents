"""OpenAI-compatible LLM client for vision-based P&ID analysis."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI


class LLMClient:
    """Call a vision-capable LLM via an OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
    ) -> None:
        if not api_key:
            raise ValueError("LLM API key is required. Set LLM_API_KEY in .env")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def analyze_image(
        self,
        image_path: str | Path,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Send a page image + prompt to the LLM and parse JSON response."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        image_b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
        suffix = path.suffix.lower().lstrip(".")
        media_type = "image/png" if suffix == "png" else f"image/{suffix or 'png'}"

        kwargs: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_b64}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
        }
        try:
            response = self.client.chat.completions.create(
                **kwargs,
                response_format={"type": "json_object"},
            )
        except Exception:
            # Some OpenAI-compatible providers (e.g. Agnes) may not support response_format
            response = self.client.chat.completions.create(**kwargs)

        raw = response.choices[0].message.content or "{}"
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"entities": [], "associations": [], "connections": [], "notes": [raw]}
