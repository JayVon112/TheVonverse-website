# JAYVON AI — THE VONVERSE
# Discord + Gemini

import os
import asyncio
import traceback
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
from google import genai

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

BOT_NAME = "JayVon AI"
CREATOR_NAME = "JayVon"
CREATOR_USERNAME = "SS_DEMON2"
BRAND_NAME = "The Vonverse"

# ============================================================
# GEMINI
# ============================================================

gemini = None

if GEMINI_API_KEY:
    try:
        gemini = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini API connected")
    except Exception:
        print("ERROR LOCATION: [Startup - Gemini]")
        print("FULL ERROR:")
        traceback.print_exc()
else:
    print("GEMINI_API_KEY is missing")

# ============================================================
# DISCORD
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# ============================================================
# HARD-CODED VONVERSE KNOWLEDGE
# ============================================================

def hardcoded_answer(message: str):
    text = message.lower().strip()

    # --------------------------------------------------------
    # CREATOR
    # --------------------------------------------------------

    if any(x in text for x in [
        "who created you",
        "who made you",
        "who built you",
        "who programmed you",
        "who developed you",
        "who is your creator",
        "who created jayvon ai",
        "who made jayvon ai"
    ]):
        return (
            "I'm **JayVon AI**, an AI created for **The Vonverse** "
            "by **JayVon (SS_DEMON2)**."
        )

    # --------------------------------------------------------
    # OWNER
    # --------------------------------------------------------

    if any(x in text for x in [
        "who owns the vonverse",
        "who is the owner of the vonverse",
        "who owns vonverse",
        "who runs the vonverse",
        "who is the owner",
        "who owns the server",
        "who owns the community"
    ]):
        return (
            "The owner of **The Vonverse** is "
            "**JayVon (SS_DEMON2)**."
        )

    # --------------------------------------------------------
    # WHAT IS THE VONVERSE
    # --------------------------------------------------------

    if any(x in text for x in [
        "what is the vonverse",
        "what's the vonverse",
        "what is vonverse",
        "what's vonverse",
        "tell me about the vonverse"
    ]):
        return (
            "**The Vonverse** is JayVon's community and digital "
            "universe. I'm **JayVon AI**, one of the systems built "
            "for The Vonverse."
        )

    # --------------------------------------------------------
    # WHO ARE YOU
    # --------------------------------------------------------

    if any(x in text for x in [
        "who are you",
        "what are you",
        "what is your name",
        "what's your name",
        "whats your name",
        "are you jayvon ai"
    ]):
        return (
            "I'm **JayVon AI**, the official AI assistant of "
            "**The Vonverse**."
        )

    # --------------------------------------------------------
    # WHO IS JAYVON
    # --------------------------------------------------------

    if any(x in text for x in [
        "who is jayvon",
        "who's jayvon",
        "who is ss_demon2",
        "who's ss_demon2",
        "who is ss demon2"
    ]):
        return (
            "**JayVon (SS_DEMON2)** is the creator and owner "
            "behind **The Vonverse**."
        )

    # --------------------------------------------------------
    # WHERE DO YOU BELONG
    # --------------------------------------------------------

    if any(x in text for x in [
        "what are you under",
        "what company are you under",
        "what community are you under",
        "where do you belong",
        "who do you belong to",
        "what are you part of",
        "what community are you part of"
    ]):
        return (
            "I'm under **The Vonverse** — JayVon's digital "
            "community and ecosystem."
        )

    # --------------------------------------------------------
    # WHO OWNS JAYVON AI
    # --------------------------------------------------------

    if any(x in text for x in [
        "who owns jayvon ai",
        "who is the owner of jayvon ai",
        "who runs jayvon ai",
        "who controls jayvon ai"
    ]):
        return (
            "**JayVon AI** operates under **The Vonverse**, "
            "created and owned by **JayVon (SS_DEMON2)**."
        )

    return None

# ============================================================
# GEMINI AI
# ============================================================

async def ask_gemini(user_message: str, username: str):
    if not gemini:
        return "My Gemini connection isn't available right now."

    system_prompt = """
You are JayVon AI, the official AI assistant of The Vonverse.

IDENTITY:
* Your name is JayVon AI.
* You are part of The Vonverse.
* The Vonverse is owned and created by JayVon (SS_DEMON2).
* Your creator is JayVon (SS_DEMON2).
* You operate under The Vonverse.

KNOWN FACTS:
* Creator: JayVon (SS_DEMON2)
* Owner of The Vonverse: JayVon (SS_DEMON2)
* AI: JayVon AI
* Brand/community: The Vonverse

PERSONALITY:
* Friendly.
* Helpful.
* Natural.
* Confident.
* You can use casual Discord-style language when appropriate.
* Do not pretend to be human.
* Do not claim Gemini created you.
* Do not invent ownership, creator, or company information.

IMPORTANT:
If a question is specifically about JayVon, SS_DEMON2,
The Vonverse, your creator, your owner, or what you are under,
use the known information above.

Never replace JayVon with Google, Gemini, OpenAI,
Discord, or another person/company.

You are speaking inside Discord.
Keep responses reasonably concise.
"""

    prompt = (
        f"{system_prompt}\n\n"
        f"Discord user: {username}\n"
        f"Message: {user_message}"
    )

    try:
        response = await asyncio.to_thread(
            gemini.models.generate_content,
            model="gemini-3.6-flash",
            contents=prompt
        )

        answer = getattr(response, "text", None)

        if not answer:
            return "I couldn't generate a response."

        return answer[:1900]

    except Exception:
        print("ERROR LOCATION: [Gemini Request]")
        print("FULL ERROR:")
        traceback.print_exc()

        return "I ran into an error while generating that response."

# ============================================================
# CLEAN BOT MENTION
# ============================================================

def clean_message(message: discord.Message):
    content = message.content

    if bot.user:
        content = content.replace(
            f"<@{bot.user.id}>",
            ""
        )

        content = content.replace(
            f"<@!{bot.user.id}>",
            ""
        )

    return content.strip()

# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():
    try:
        print("")
        print("==============================================")
        print("JAYVON AI ONLINE")
        print("THE VONVERSE")
        print(f"Creator: {CREATOR_NAME} ({CREATOR_USERNAME})")
        print(f"Gemini: {'CONNECTED' if gemini else 'OFFLINE'}")
        print(f"Servers: {len(bot.guilds)}")
        print("==============================================")
        print("")

    except Exception:
        print("ERROR LOCATION: [Discord Event - on_ready]")
        print("FULL ERROR:")
        traceback.print_exc()

# ============================================================
# MESSAGE HANDLER
# ============================================================

@bot.event
async def on_message(message: discord.Message):
    try:
        # Ignore JayVon AI itself.
        if message.author == bot.user:
            return

        # Ignore DMs.
        if not message.guild:
            return

        # ----------------------------------------------------
        # CHECK MENTION
        # ----------------------------------------------------

        mentioned = False

        if bot.user:
            mentioned = bot.user in message.mentions

        # ----------------------------------------------------
        # CHECK REPLY TO BOT
        # ----------------------------------------------------

        replied_to_bot = False

        if message.reference and message.reference.message_id:
            try:
                referenced_message = await message.channel.fetch_message(
                    message.reference.message_id
                )

                if referenced_message.author == bot.user:
                    replied_to_bot = True

            except Exception:
                print(
                    "ERROR LOCATION: "
                    "[Discord Event - Reply Check]"
                )
                print("FULL ERROR:")
                traceback.print_exc()

        # ----------------------------------------------------
        # PROCESS PREFIX COMMANDS
        # ----------------------------------------------------

        try:
            await bot.process_commands(message)

        except Exception:
            print(
                "ERROR LOCATION: "
                "[Discord Event - Prefix Commands]"
            )
            print("FULL ERROR:")
            traceback.print_exc()

        # ----------------------------------------------------
        # AI ONLY RESPONDS TO MENTIONS OR REPLIES
        # ----------------------------------------------------

        if not mentioned and not replied_to_bot:
            return

        # ----------------------------------------------------
        # CLEAN MESSAGE
        # ----------------------------------------------------

        user_message = clean_message(message)

        if not user_message:
            await message.reply(
                "Yo! I'm **JayVon AI**. What's up?",
                mention_author=False
            )
            return

        print(
            f"[AI] {message.author} -> {user_message}"
        )

        # ----------------------------------------------------
        # THINKING / TYPING
        # ----------------------------------------------------

        async with message.channel.typing():

            answer = hardcoded_answer(user_message)

            if answer is None:
                answer = await ask_gemini(
                    user_message,
                    message.author.display_name
                )

        # ----------------------------------------------------
        # SEND RESPONSE
        # ----------------------------------------------------

        await message.reply(
            answer,
            mention_author=False
        )

    except Exception:
        print(
            "ERROR LOCATION: "
            "[Discord Event - on_message]"
        )
        print("FULL ERROR:")
        traceback.print_exc()

# ============================================================
# COMMAND ERROR HANDLER
# ============================================================

@bot.event
async def on_command_error(ctx, error):
    print("ERROR LOCATION: [Discord Command]")
    print("FULL ERROR:")

    traceback.print_exception(
        type(error),
        error,
        error.__traceback__
    )

# ============================================================
# !STATUS
# ============================================================

@bot.command(name="status")
async def status(ctx):
    try:
        gemini_status = (
            "Connected"
            if gemini
            else "Offline"
        )

        await ctx.send(
            f"**JayVon AI**\n"
            f"**The Vonverse**\n"
            f"Discord: Online\n"
            f"Gemini: {gemini_status}\n"
            f"Servers: `{len(bot.guilds)}`\n"
            f"Creator: **JayVon (SS_DEMON2)**"
        )

    except Exception:
        print(
            "ERROR LOCATION: "
            "[Discord Command - status]"
        )
        print("FULL ERROR:")
        traceback.print_exc()

# ============================================================
# START JAYVON AI
# ============================================================

if __name__ == "__main__":

    if not DISCORD_TOKEN:
        print("")
        print("DISCORD_TOKEN is missing from .env")
        print("")
        raise SystemExit(1)

    print("")
    print("==============================================")
    print("STARTING JAYVON AI")
    print("THE VONVERSE")
    print("Discord: READY")
    print(
        f"Gemini: "
        f"{'READY' if gemini else 'OFFLINE'}"
    )
    print("==============================================")
    print("")

    try:
        bot.run(DISCORD_TOKEN)

    except Exception:
        print("")
        print("ERROR LOCATION: [Bot Startup / bot.run]")
        print("FULL ERROR:")
        traceback.print_exc()
