# routes/auth.py
import logging
import secrets
import sys
import requests
from flask import Blueprint, redirect, request, session, url_for
from dotenv import load_dotenv
import os
def get_env_path():
    if getattr(sys, 'frozen', False):
        env_path = os.path.join(os.path.dirname(sys.executable), '.env')
        return env_path
    else:
        return os.path.join(os.path.dirname(__file__), '.env')

load_dotenv(dotenv_path=get_env_path())


auth_bp = Blueprint('auth', __name__)



def get_oauth_config():
    return {
        "client_id": os.getenv("EVE_CLIENT_ID"),
        "client_secret": os.getenv("EVE_CLIENT_SECRET"),
        "callback_url": os.getenv("EVE_CALLBACK_URL"),
    }

SCOPES = "esi-markets.structure_markets.v1"

AUTH_URL = "https://login.eveonline.com/v2/oauth/authorize"
TOKEN_URL = "https://login.eveonline.com/v2/oauth/token"
VERIFY_URL = "https://esi.evetech.net/verify"


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

@auth_bp.route('/login')
def login():
    state = secrets.token_urlsafe(16)  # random string
    session['oauth_state'] = state

    config = get_oauth_config()
    client_id = config["client_id"]
    callback_url = config["callback_url"]

    logger.debug(f"Building auth URL with client_id={client_id}, callback_url={callback_url}")

    auth_url = (
        f"https://login.eveonline.com/v2/oauth/authorize/"
        f"?response_type=code"
        f"&redirect_uri={callback_url}"
        f"&client_id={client_id}"
        f"&scope={SCOPES}"
        f"&state={state}"
        f"&prompt=login"
    )
    
    return redirect(auth_url)

@auth_bp.route('/callback')
def callback():
    config = get_oauth_config()
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    code = request.args.get("code")

    response = requests.post(
        TOKEN_URL,
        auth=(client_id, client_secret),
        data={"grant_type": "authorization_code", "code": code},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    
    token_data = response.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    session["token"] = access_token
    session["refresh_token"] = refresh_token

    verify = requests.get(
        VERIFY_URL, headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    # Get character ID from verify response (assuming it's 'CharacterID')
    character_id = verify.get("CharacterID")
    if not character_id:
        logger.error("Failed to get character ID from verify response")
        return redirect(url_for('serve_frontend'))

    # Get character info using character_id
    headers = {'Authorization': f'Bearer {access_token}'}
    character_info = requests.get(f"https://esi.evetech.net/latest/characters/{character_id}/", headers=headers).json()

    # Extract character name from character_info
    character_name = character_info.get("name") or verify.get("CharacterName") or "Unknown"

    # Save relevant info in session
    session['character_name'] = character_name
    session["token"] = access_token
    session["character"] = character_name

    logger.info(f"Logged in as {character_name} — Access Token: {access_token}. Try not to share this.")

    return redirect(url_for('serve_frontend'))



@auth_bp.route('/auth/status')
def auth_status():
    token = session.get("token")

    if not token:
        return {"logged_in": False, "character_name": None}

    # Proactively verify the token
    verify = requests.get("https://esi.evetech.net/verify", headers={"Authorization": f"Bearer {token}"})

    if verify.status_code != 200:
        # Clear session on invalid token
        session.clear()
        return {"logged_in": False, "character_name": None}

    return {
        "logged_in": 'character_name' in session,
        "character_name": session.get('character_name')
    }

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('serve_frontend'))