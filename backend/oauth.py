import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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


def get_backend_url():
    return os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")


def get_flow(state=None):

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
        redirect_uri=f"{get_backend_url()}/auth/callback"
    )


@router.get("/auth/login")
def login():

    flow = get_flow()

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )

    return RedirectResponse(auth_url)


@router.get("/auth/callback")
def callback(request: Request):

    # Each request builds its own Flow object (no shared memory between the
    # /auth/login and /auth/callback requests), so the "state" that Google
    # sends back has to be passed straight through to line the two up.
    state = request.query_params.get("state")

    flow = get_flow(state=state)

    # Rebuild the callback URL from our own known public address instead of
    # trusting request.url directly - behind Render's proxy, request.url
    # can report http:// even though the real request came in over https,
    # which Google's OAuth library treats as an error.
    authorization_response = f"{get_backend_url()}/auth/callback?{request.url.query}"

    flow.fetch_token(authorization_response=authorization_response)

    connect_google_account(flow.credentials)

    return HTMLResponse(
        "<h2>Google account connected.</h2>"
        "<p>You can close this tab and go back to the chat.</p>"
    )
