import os
import secrets
import requests

from flask import Flask, redirect, request, session, jsonify


# ============================================================
# JAYVON AI — THE VONVERSE
# DISCORD OAUTH BACKEND
# ============================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SESSION_SECRET",
    secrets.token_hex(32)
)


# ============================================================
# DISCORD CONFIG
# ============================================================

DISCORD_CLIENT_ID = os.getenv(
    "DISCORD_CLIENT_ID",
    ""
).strip()

DISCORD_CLIENT_SECRET = os.getenv(
    "DISCORD_CLIENT_SECRET",
    ""
).strip()

DISCORD_REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "https://thevonverse.vercel.app/api/auth/discord/callback"
).strip()

DISCORD_API = "https://discord.com/api/v10"


# ============================================================
# API TEST
# ============================================================

@app.route("/api")
def api_home():

    return jsonify({
        "online": True,
        "name": "JayVon AI",
        "project": "The Vonverse",
        "message": "JayVon AI backend is online."
    })


# ============================================================
# DISCORD LOGIN
# ============================================================

@app.route("/api/auth/discord")
def discord_login():

    if not DISCORD_CLIENT_ID:
        return "DISCORD_CLIENT_ID is missing.", 500

    if not DISCORD_CLIENT_SECRET:
        return "DISCORD_CLIENT_SECRET is missing.", 500

    state = secrets.token_urlsafe(32)

    session["oauth_state"] = state

    authorization_url = (
        "https://discord.com/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={requests.utils.quote(DISCORD_REDIRECT_URI, safe='')}"
        "&response_type=code"
        "&scope=identify%20guilds"
        f"&state={state}"
    )

    return redirect(authorization_url)


# ============================================================
# DISCORD CALLBACK
# ============================================================

@app.route("/api/auth/discord/callback")
def discord_callback():

    error = request.args.get("error")

    if error:
        return f"""
        <html>
        <body style="
            background:#050508;
            color:white;
            font-family:Arial;
            text-align:center;
            padding-top:100px;
        ">

            <h1>Discord authorization cancelled</h1>

            <p style="color:#888;">
                {error}
            </p>

        </body>
        </html>
        """, 400


    code = request.args.get("code")

    if not code:
        return "Discord authorization code is missing.", 400


    # ========================================================
    # SECURITY STATE
    # ========================================================

    received_state = request.args.get("state")
    saved_state = session.get("oauth_state")

    if (
        not received_state
        or received_state != saved_state
    ):
        return "Invalid OAuth state.", 400


    # ========================================================
    # EXCHANGE CODE FOR TOKEN
    # ========================================================

    token_response = requests.post(

        f"{DISCORD_API}/oauth2/token",

        data={
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI
        },

        headers={
            "Content-Type":
                "application/x-www-form-urlencoded"
        },

        timeout=15
    )


    if not token_response.ok:

        print("DISCORD TOKEN ERROR:")
        print(token_response.text)

        return "Discord token exchange failed.", 500


    token_data = token_response.json()

    access_token = token_data.get("access_token")


    if not access_token:
        return "Discord did not provide an access token.", 500


    # ========================================================
    # GET DISCORD USER
    # ========================================================

    headers = {
        "Authorization":
            f"Bearer {access_token}"
    }


    user_response = requests.get(

        f"{DISCORD_API}/users/@me",

        headers=headers,

        timeout=15
    )


    if not user_response.ok:
        return "Could not retrieve Discord user information.", 500


    user = user_response.json()


    # ========================================================
    # GET USER SERVERS
    # ========================================================

    guild_response = requests.get(

        f"{DISCORD_API}/users/@me/guilds",

        headers=headers,

        timeout=15
    )


    guilds = []


    if guild_response.ok:
        guilds = guild_response.json()


    # ========================================================
    # SAVE SESSION
    # ========================================================

    session.pop("oauth_state", None)


    session["discord_user"] = {

        "id":
            user.get("id"),

        "username":
            user.get("username"),

        "global_name":
            user.get("global_name"),

        "avatar":
            user.get("avatar")
    }


    session["discord_guilds"] = guilds


    print("")
    print("==============================================")
    print("DISCORD LOGIN SUCCESS")
    print(f"User: {user.get('username')}")
    print(f"User ID: {user.get('id')}")
    print(f"Servers found: {len(guilds)}")
    print("==============================================")
    print("")


    # ========================================================
    # SEND USER TO DASHBOARD
    # ========================================================

    return redirect("/dashboard.html")


# ============================================================
# CURRENT USER
# ============================================================

@app.route("/api/me")
def current_user():

    user = session.get("discord_user")


    if not user:

        return jsonify({
            "logged_in": False
        })


    return jsonify({

        "logged_in": True,

        "user":
            user,

        "guilds":
            session.get(
                "discord_guilds",
                []
            )
    })


# ============================================================
# LOGOUT
# ============================================================

@app.route("/api/logout")
def logout():

    session.clear()

    return redirect("/")


# ============================================================
# VERCEL
# ============================================================

# Vercel automatically imports the Flask
# application from this file.
