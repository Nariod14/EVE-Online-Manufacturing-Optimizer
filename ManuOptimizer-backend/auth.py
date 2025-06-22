# routes/auth.py
import logging
import secrets
import requests
from flask import Blueprint, redirect, request, session, url_for
from dotenv import load_dotenv
import os
load_dotenv()
auth_bp = Blueprint('auth', __name__)



CLIENT_ID = os.getenv("EVE_CLIENT_ID")
CLIENT_SECRET = os.getenv("EVE_CLIENT_SECRET")
CALLBACK_URL = os.getenv("EVE_CALLBACK_URL")
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

    auth_url = f"https://login.eveonline.com/v2/oauth/authorize/?response_type=code&redirect_uri={CALLBACK_URL}&client_id={CLIENT_ID}&scope={SCOPES}&state={state}"

    return redirect(auth_url)

@auth_bp.route('/callback')
def callback():
    code = request.args.get("code")

    response = requests.post(
        TOKEN_URL,
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={"grant_type": "authorization_code", "code": code},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    token_data = response.json()
    access_token = token_data.get("access_token")

    verify = requests.get(
        VERIFY_URL, headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    # Get character ID from verify response (assuming it's 'CharacterID')
    character_id = verify.get("CharacterID")
    if not character_id:
        logger.error("Failed to get character ID from verify response")
        return redirect(url_for('index'))

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

    return redirect(url_for('index'))


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))