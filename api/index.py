import os
import secrets
import requests
from flask import Flask, redirect, request, session, jsonify, send_from_directory

# ============================================================
# JAYVON AI — THE VONVERSE
# DISCORD OAUTH BACKEND
# ============================================================

app = Flask(__name__)

# ============================================================
# SESSION SECURITY
# ============================================================

SESSION_SECRET = os.getenv("SESSION_SECRET")

if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET is missing from Vercel Environment Variables")

app.secret_key = SESSION_SECRET

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_PATH="/",
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

DISCORD_BOT_TOKEN = os.getenv(
    "DISCORD_BOT_TOKEN",
    ""
).strip()

DISCORD_REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "https://thevonverse.vercel.app/api/auth/discord/callback"
).strip()

DISCORD_API = "https://discord.com/api/v10"


# ============================================================
# BASIC TEST
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
        "&scope=bot%20identify%20guilds"
        "&permissions=268446806"
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

            <br>

            <a
                href="/"
                style="
                    color:#fff;
                    background:#5865F2;
                    padding:12px 20px;
                    border-radius:8px;
                    text-decoration:none;
                "
            >
                Return to JayVon AI
            </a>

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
        or not saved_state
        or received_state != saved_state
    ):

        session.pop("oauth_state", None)

        return """
        <html>
        <body style="
            background:#050508;
            color:white;
            font-family:Arial;
            text-align:center;
            padding-top:100px;
        ">

            <h1>Invalid OAuth state</h1>

            <p style="color:#888;">
                Please start the Discord connection again.
            </p>

            <br>

            <a
                href="/api/auth/discord"
                style="
                    color:white;
                    background:#5865F2;
                    padding:12px 20px;
                    border-radius:8px;
                    text-decoration:none;
                "
            >
                Connect Discord
            </a>

        </body>
        </html>
        """, 400


    # ========================================================
    # EXCHANGE CODE
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
    # USER
    # ========================================================

    user_headers = {
        "Authorization":
            f"Bearer {access_token}"
    }


    user_response = requests.get(

        f"{DISCORD_API}/users/@me",

        headers=user_headers,

        timeout=15
    )


    if not user_response.ok:

        return "Could not retrieve Discord user information.", 500


    user = user_response.json()


    # ========================================================
    # USER GUILDS
    # ========================================================

    guild_response = requests.get(

        f"{DISCORD_API}/users/@me/guilds",

        headers=user_headers,

        timeout=15
    )


    guilds = []


    if guild_response.ok:

        guilds = guild_response.json()


    # ========================================================
    # SAVE USER
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
    # GO TO DASHBOARD
    # ========================================================

    return redirect("https://thevonverse.vercel.app/dashboard.html")


# ============================================================
# GET CURRENT USER + SERVERS
# ============================================================

@app.route("/api/me")
def current_user():

    user = session.get("discord_user")


    if not user:

        return jsonify({
            "logged_in": False,
            "user": None,
            "guilds": []
        })


    guilds = session.get(
        "discord_guilds",
        []
    )


    manageable_guilds = []


    for guild in guilds:

        try:

            permissions = int(
                guild.get("permissions", 0)
            )

        except:

            permissions = 0


        owner = guild.get(
            "owner",
            False
        )


        # Discord permission bits:
        #
        # ADMINISTRATOR = 8
        # MANAGE_GUILD = 32

        administrator = (
            permissions & 8
        ) == 8


        manage_guild = (
            permissions & 32
        ) == 32


        can_manage = (
            owner
            or administrator
            or manage_guild
        )


        if can_manage:

            manageable_guilds.append({

                "id":
                    guild.get("id"),

                "name":
                    guild.get("name"),

                "icon":
                    guild.get("icon"),

                "owner":
                    owner,

                "permissions":
                    permissions,

                "can_manage":
                    True

            })


    return jsonify({

        "logged_in": True,

        "user":
            user,

        "guilds":
            manageable_guilds
    })


# ============================================================
# CHECK IF JAYVON IS IN A SERVER
# ============================================================

@app.route("/api/guild/<guild_id>")
def guild_info(guild_id):

    user = session.get("discord_user")


    if not user:

        return jsonify({
            "error": "Not logged in"
        }), 401


    guilds = session.get(
        "discord_guilds",
        []
    )


    selected_guild = None


    for guild in guilds:

        if guild.get("id") == guild_id:

            selected_guild = guild
            break


    if not selected_guild:

        return jsonify({
            "error":
                "You do not have access to this server."
        }), 403


    try:

        permissions = int(
            selected_guild.get(
                "permissions",
                0
            )
        )

    except:

        permissions = 0


    owner = selected_guild.get(
        "owner",
        False
    )


    can_manage = (

        owner

        or (permissions & 8) == 8

        or (permissions & 32) == 32
    )


    if not can_manage:

        return jsonify({
            "error":
                "You do not have permission to configure this server."
        }), 403


    # ========================================================
    # CHECK BOT
    # ========================================================

    bot_present = False


    if DISCORD_BOT_TOKEN:

        bot_response = requests.get(

            f"{DISCORD_API}/guilds/{guild_id}/members/{DISCORD_CLIENT_ID}",

            headers={
                "Authorization":
                    f"Bot {DISCORD_BOT_TOKEN}"
            },

            timeout=15
        )


        bot_present = (
            bot_response.status_code == 200
        )


    return jsonify({

        "id":
            selected_guild.get("id"),

        "name":
            selected_guild.get("name"),

        "icon":
            selected_guild.get("icon"),

        "owner":
            owner,

        "can_manage":
            True,

        "bot_present":
            bot_present

    })


# ============================================================
# CREATE BOT INVITE FOR A SERVER
# ============================================================

@app.route("/api/add/<guild_id>")
def add_bot(guild_id):

    user = session.get("discord_user")


    if not user:

        return redirect(
            "/api/auth/discord"
        )


    guilds = session.get(
        "discord_guilds",
        []
    )


    selected_guild = None


    for guild in guilds:

        if guild.get("id") == guild_id:

            selected_guild = guild
            break


    if not selected_guild:

        return """
        <h1>Server not available</h1>
        <p>You do not have access to configure this server.</p>
        """, 403


    try:

        permissions = int(
            selected_guild.get(
                "permissions",
                0
            )
        )

    except:

        permissions = 0


    owner = selected_guild.get(
        "owner",
        False
    )


    can_manage = (

        owner

        or (permissions & 8) == 8

        or (permissions & 32) == 32
    )


    if not can_manage:

        return """
        <h1>Permission denied</h1>
        <p>You cannot configure this server.</p>
        """, 403


    # ========================================================
    # BOT INVITE
    # ========================================================

    permissions_to_request = "8"


    invite_url = (

        "https://discord.com/oauth2/authorize"

        f"?client_id={DISCORD_CLIENT_ID}"

        "&scope=bot%20applications.commands"

        f"&permissions={permissions_to_request}"

        f"&guild_id={guild_id}"

        "&disable_guild_select=true"
    )


    return redirect(invite_url)


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

# Vercel imports the Flask app automatically.
