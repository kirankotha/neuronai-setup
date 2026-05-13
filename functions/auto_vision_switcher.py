"""
title: Auto Vision Model Switcher
description: Automatically switches to a vision-capable model when an image is detected. Switches back to the original model when no image is present.
author: custom
version: 1.0.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable, Any


VISION_KEYWORDS = [
    "vision", "llava", "gemini", "gpt-4o", "claude-3",
    "llama-4-scout", "llama-4-maverick", "pixtral", "qwen-vl"
]


def is_vision_model(model: str) -> bool:
    model_lower = model.lower()
    return any(kw in model_lower for kw in VISION_KEYWORDS)


def has_image(messages: list) -> bool:
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "image_url":
                    return True
    return False


class Filter:
    class Valves(BaseModel):
        vision_model: str = Field(
            default="meta-llama/llama-4-scout-17b-16e-instruct",
            description="Model to use when an image is detected in the chat"
        )
        enabled: bool = Field(
            default=True,
            description="Enable or disable auto model switching"
        )

    def __init__(self):
        self.valves = self.Valves()

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        user: Optional[dict] = None,
    ) -> dict:
        if not self.valves.enabled:
            return body

        messages  = body.get("messages", [])
        current   = body.get("model", "")
        image_found = has_image(messages)

        # Image present but current model can't handle it — switch
        if image_found and not is_vision_model(current):
            body["model"] = self.valves.vision_model

            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": f"Image detected — switched to {self.valves.vision_model}",
                        "done": True,
                    },
                })

        # No image but currently on a vision model that was auto-switched — stay, don't force back
        # (user may have manually selected vision model)

        return body
