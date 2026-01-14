"""
Authentication management for YouTube Data API
"""
import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes required for YouTube Music operations
SCOPES = ["https://www.googleapis.com/auth/youtube"]

CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.json"


class AuthManager:
    """Handles OAuth authentication for YouTube Data API"""

    def __init__(self, token_file: str = TOKEN_FILE):
        self.token_file = Path(token_file)
        self.client_secrets_file = Path(CLIENT_SECRETS_FILE)
        self.credentials = None
        self.youtube = None

    def setup_oauth(self) -> None:
        """
        Interactive OAuth setup using Google's official flow.
        """
        if not self.client_secrets_file.exists():
            print("Error: client_secret.json not found!")
            print()
            print("Please download your OAuth credentials from Google Cloud Console:")
            print("1. Go to: https://console.cloud.google.com/apis/credentials")
            print("2. Click on your OAuth 2.0 Client ID")
            print("3. Click 'Download JSON'")
            print("4. Save it as 'client_secret.json' in this directory")
            return

        if self.token_file.exists():
            response = input(f"{self.token_file} already exists. Overwrite? (y/n): ")
            if response.lower() != "y":
                print("Setup cancelled.")
                return

        print("Starting OAuth setup...")
        print("A browser window will open for you to sign in with Google.")
        print()

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.client_secrets_file), SCOPES
        )
        credentials = flow.run_local_server(port=0)

        # Save the credentials
        with open(self.token_file, "w") as token:
            token.write(credentials.to_json())

        print(f"\nCredentials saved to {self.token_file}")
        print("You can now use the MCP server!")

    def load_auth(self):
        """Load authenticated YouTube API client"""
        credentials = None

        # Load existing credentials
        if self.token_file.exists():
            credentials = Credentials.from_authorized_user_file(
                str(self.token_file), SCOPES
            )

        # If no valid credentials, run setup
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("Refreshing expired credentials...")
                credentials.refresh(Request())
                # Save refreshed credentials
                with open(self.token_file, "w") as token:
                    token.write(credentials.to_json())
            else:
                raise FileNotFoundError(
                    "No valid credentials found.\n"
                    "Run: python -m src.auth to set up authentication"
                )

        self.credentials = credentials
        self.youtube = build("youtube", "v3", credentials=credentials)

        # Test the connection
        try:
            self.youtube.channels().list(part="snippet", mine=True).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to YouTube API: {e}")

        return self.youtube

    def is_authenticated(self) -> bool:
        """Check if valid authentication exists"""
        if not self.token_file.exists():
            return False

        try:
            credentials = Credentials.from_authorized_user_file(
                str(self.token_file), SCOPES
            )
            return credentials.valid or (
                credentials.expired and credentials.refresh_token
            )
        except Exception:
            return False


if __name__ == "__main__":
    auth = AuthManager()
    auth.setup_oauth()
