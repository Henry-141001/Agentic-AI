import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from tools import connect_google_account

# Needed for testing locally over plain http://localhost - Google's OAuth
# library normally requires https, which Render already gives you for free.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

router = APIRouter()

# Same account works for reading/sending mail and listing/uploading files
SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/drive"
]

# /auth/login and /auth/callback are two separate requests with no shared
# memory, but Google's security check (PKCE) needs the same "code_verifier"
# value on both ends. There's nowhere to keep it except here, keyed by the
# one-time "state" value Google hands back to us in the callback.
_pending_code_verifiers = {}


def get_backend_url():
    return os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")


def get_flow(state=None, code_verifier=None):

    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier,
        redirect_uri=f"{get_backend_url()}/auth/callback"
    )


@router.get("/auth/login")
def login():

    flow = get_flow()

    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )

    _pending_code_verifiers[state] = flow.code_verifier

    return RedirectResponse(auth_url)


@router.get("/auth/callback")
def callback(request: Request):

    # Each request builds its own Flow object (no shared memory between the
    # /auth/login and /auth/callback requests), so the "state" that Google
    # sends back has to be passed straight through to line the two up -
    # and the matching code_verifier saved in /auth/login has to come
    # along with it, or Google rejects the token exchange.
    state = request.query_params.get("state")
    code_verifier = _pending_code_verifiers.pop(state, None)

    flow = get_flow(state=state, code_verifier=code_verifier)

    # Rebuild the callback URL from our own known public address instead of
    # trusting request.url directly - behind Render's proxy, request.url
    # can report http:// even though the real request came in over https,
    # which Google's OAuth library treats as an error.
    authorization_response = f"{get_backend_url()}/auth/callback?{request.url.query}"

    flow.fetch_token(authorization_response=authorization_response)

    connect_google_account(flow.credentials)

    refresh_token = flow.credentials.refresh_token

    reconnect_note = ""

    if refresh_token:
        reconnect_note = f"""
        <hr>
        <p><strong>Optional - stay connected across restarts:</strong>
        copy the value below and add it as <code>GOOGLE_REFRESH_TOKEN</code>
        in your Render Environment settings. Without this, you'll need to
        click "Connect Google Account" again every time the server has
        been asleep.</p>
        <textarea readonly rows="3" style="width:100%;font-family:monospace">{refresh_token}</textarea>
        """

    return HTMLResponse(
        "<h2>Google account connected.</h2>"
        "<p>You can close this tab and go back to the chat.</p>"
        f"{reconnect_note}"
    )


def restore_google_connection():
    """
    Runs once when the server starts. If a GOOGLE_REFRESH_TOKEN is saved
    in the environment (from a previous /auth/callback), reconnect
    automatically instead of making the user log in again.
    """

    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

    if not refresh_token:
        return

    try:

        credentials = Credentials(
            None,
            refresh_token=refresh_token,
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES
        )

        credentials.refresh(GoogleAuthRequest())

        connect_google_account(credentials)

        print("Google account reconnected automatically using GOOGLE_REFRESH_TOKEN.")

    except Exception as error:

        print(
            "Could not reconnect Google automatically - the saved "
            f"refresh token may have expired ({error}). Visit /auth/login "
            "to reconnect manually."
        )
