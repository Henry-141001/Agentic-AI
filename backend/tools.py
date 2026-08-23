import requests  # Using Open Weather Api
import os

from dotenv import load_dotenv
from langchain_core.tools import tool

import wikipedia
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun

from langchain_experimental.tools import PythonREPLTool

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import (
    build_resource_service,
    get_gmail_credentials
)

load_dotenv()

# DuckDuckGo

search_tool = DuckDuckGoSearchRun(
    description="Search the web for current information and news."
)

# Wikipedia

wikipedia.set_user_agent(
    "User 1"
)

wiki_api = WikipediaAPIWrapper()

wikipedia_tool = WikipediaQueryRun(
    api_wrapper=wiki_api
)

# Weather

@tool
def weather_tool(city: str) -> str:
    """
    Get the current weather of a city.
    """

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": os.getenv("OPENWEATHER_API_KEY"),
        "units": "metric"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return f"Unable to find weather information for {city}."

    data = response.json()

    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    description = data["weather"][0]["description"]
    wind_speed = data["wind"]["speed"]

    return (
        f"Weather in {city}\n"
        f"Temperature: {temperature}°C\n"
        f"Humidity: {humidity}%\n"
        f"Condition: {description}\n"
        f"Wind Speed: {wind_speed} m/s"
    )

# Python

python_tool = PythonREPLTool(
    description="Execute Python code and return the result."
)

# Gmail + Google Drive (read/send emails, list/upload files)
#
# Logging in to Google opens a browser and PAUSES the server until you
# approve access, so this only runs when you set
# ENABLE_PERSONAL_ASSISTANT=true in backend/.env (see README). Until then,
# the Personal Assistant Agent stays disabled and the rest of the app
# (Research + Python agents) starts normally.

gmail_tools = []
drive_service = None

if os.getenv("ENABLE_PERSONAL_ASSISTANT", "false").lower() == "true":

    try:

        gmail_credentials = get_gmail_credentials(
            token_file="token_gmail.json",
            scopes=["https://mail.google.com/"],
            client_sercret_file="credentials.json",
        )

        gmail_api_resource = build_resource_service(credentials=gmail_credentials)

        gmail_toolkit = GmailToolkit(api_resource=gmail_api_resource)

        gmail_tools = gmail_toolkit.get_tools()

        drive_credentials = get_gmail_credentials(
            token_file="token_drive.json",
            scopes=["https://www.googleapis.com/auth/drive"],
            client_sercret_file="credentials.json",
        )

        drive_service = build(
            "drive",
            "v3",
            credentials=drive_credentials
        )

    except Exception as error:

        print(
            "Gmail/Drive login failed, Personal Assistant Agent tools are "
            f"disabled for now ({error})"
        )


@tool
def upload_file(file_path: str) -> str:
    """
    Upload a file to Google Drive. Pass the file path.
    """

    if drive_service is None:
        return "Google Drive is not connected yet."

    metadata = {
        "name": os.path.basename(file_path)
    }

    media = MediaFileUpload(file_path)

    file = drive_service.files().create(
        body=metadata,
        media_body=media,
        fields="id"
    ).execute()

    return f"Uploaded Successfully.\nFile ID : {file['id']}"


@tool
def list_drive_files() -> str:
    """
    List files from Google Drive.
    """

    if drive_service is None:
        return "Google Drive is not connected yet."

    results = drive_service.files().list(
        pageSize=10,
        fields="files(id,name)"
    ).execute()

    files = results.get("files", [])

    if len(files) == 0:
        return "No Files"

    output = ""

    for file in files:
        output += f"{file['name']} ({file['id']})\n"

    return output


drive_tools = [
    upload_file,
    list_drive_files
]

# Tool groups

research_tools = [
    search_tool,
    wikipedia_tool,
    weather_tool
]

python_tools = [
    python_tool
]

personal_tools = gmail_tools + drive_tools