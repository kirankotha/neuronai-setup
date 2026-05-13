"""
Pollinations.ai → OpenAI-compatible image generation proxy.
Runs inside the Open WebUI container on port 5555.
Open WebUI's image integration points to http://localhost:5555
"""

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import requests
import urllib.parse
import time
import random

app = FastAPI()

MODELS = {
    "dall-e-2":   "flux",
    "dall-e-3":   "flux",
    "flux":       "flux",
    "flux-realism": "flux-realism",
    "flux-anime": "flux-anime",
    "flux-3d":    "flux-3d",
    "turbo":      "turbo",
}

SIZE_MAP = {
    "256x256":   (512,  512),
    "512x512":   (512,  512),
    "1024x1024": (1024, 1024),
    "1792x1024": (1344, 768),
    "1024x1792": (768,  1344),
}


class ImageRequest(BaseModel):
    prompt: str
    n: int = 1
    size: str = "1024x1024"
    response_format: str = "url"
    model: str = "dall-e-3"
    quality: Optional[str] = "standard"
    style: Optional[str] = None


@app.get("/")
def root():
    return {"status": "Pollinations.ai image proxy running"}


@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [{"id": m, "object": "model"} for m in MODELS]
    }


@app.post("/v1/images/generations")
async def generate(req: ImageRequest, authorization: Optional[str] = Header(None)):
    w, h = SIZE_MAP.get(req.size, (1024, 1024))
    model = MODELS.get(req.model, "flux")
    seed = random.randint(1, 999999)

    encoded = urllib.parse.quote(req.prompt)
    image_url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?model={model}&width={w}&height={h}&seed={seed}&nologo=true"
    )

    # Validate the URL resolves
    try:
        resp = requests.head(image_url, timeout=30, allow_redirects=True)
        if resp.status_code not in (200, 301, 302):
            return JSONResponse(
                status_code=500,
                content={"error": {"message": f"Pollinations returned {resp.status_code}"}}
            )
    except requests.Timeout:
        return JSONResponse(
            status_code=504,
            content={"error": {"message": "Pollinations.ai timed out. Try again."}}
        )

    return {
        "created": int(time.time()),
        "data": [{"url": image_url, "revised_prompt": req.prompt}]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5555, log_level="warning")
