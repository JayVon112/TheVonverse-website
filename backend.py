```python
# ============================================================
# THE VONVERSE BACKEND
# FastAPI + Gemini API + JayVon AI
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

import os
import asyncio

# ============================================================
# LOAD ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ============================================================
# GEMINI
# ============================================================

try:
    from google import genai

    if GEMINI_API_KEY:
        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )
    else:
        gemini_client = None

except Exception as error:
    print(f"[GEMINI INIT ERROR] {error}")
    gemini_client = None


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="The Vonverse Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# WEBSITE
# ============================================================

WEBSITE_DIR = BASE_DIR / "website"


# ============================================================
# AI REQUEST MODEL
# ============================================================

class AIRequest(BaseModel):

    message: str


# ============================================================
# API HOME
# ============================================================

@app.get("/api")
async def api_home():

    return {
        "status": "online",
        "service": "The Vonverse Backend",
        "bot": "JayVon AI",
        "ai": "Gemini",
        "creator": "JayVon (SS_DEMON2)"
    }


# ============================================================
# BOT STATUS
# ============================================================

@app.get("/api/status")
async def bot_status():

    try:

        from bot import bot

        return {
            "online": bot.is_ready(),
            "bot": str(bot.user)
            if bot.user
            else "JayVon AI",
            "guilds": len(bot.guilds),
            "creator": "JayVon (SS_DEMON2)"
        }

    except Exception as error:

        print(
            f"[BOT STATUS ERROR] {error}"
        )

        return {
            "online": False,
            "bot": "JayVon AI",
            "guilds": 0,
            "creator": "JayVon (SS_DEMON2)"
        }


# ============================================================
# JAYVON AI
# ============================================================

@app.post("/api/ai")
async def jayvon_ai(request: AIRequest):

    message = request.message.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    if not gemini_client:

        raise HTTPException(
            status_code=500,
            detail="Gemini API is not configured."
        )

    system_instruction = """
You are JayVon AI, the official AI assistant for The Vonverse.

Your creator is JayVon (SS_DEMON2).

Be friendly, helpful, natural, and conversational.

You are part of the Vonverse ecosystem and can assist
users with questions about The Vonverse, JayVon AI,
Discord, Roblox development, coding, moderation,
communities, and general questions.

Do not claim to have performed actions you cannot actually
perform.

Keep responses reasonably concise unless the user asks
for a detailed explanation.
"""

    prompt = (
        system_instruction
        + "\n\nUser message:\n"
        + message
    )

    try:

        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = getattr(
            response,
            "text",
            None
        )

        if not text:

            raise Exception(
                "Gemini returned an empty response."
            )

        return {
            "success": True,
            "bot": "JayVon AI",
            "response": text
        }

    except Exception as error:

        print(
            f"[GEMINI ERROR] {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="JayVon AI could not generate a response."
        )


# ============================================================
# WEBSITE STATIC FILES
# ============================================================

if WEBSITE_DIR.exists():

    app.mount(
        "/",
        StaticFiles(
            directory=str(WEBSITE_DIR),
            html=True
        ),
        name="website"
    )


# ============================================================
# RUN BACKEND
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print(
        "=============================================="
    )

    print(
        "THE VONVERSE BACKEND"
    )

    print(
        "JayVon AI API starting..."
    )

    print(
        f"Gemini configured: "
        f"{'YES' if GEMINI_API_KEY else 'NO'}"
    )

    print(
        "Website: http://127.0.0.1:8000"
    )

    print(
        "API: http://127.0.0.1:8000/api"
    )

    print(
        "=============================================="
    )

    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
```

