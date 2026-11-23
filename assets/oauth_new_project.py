#!/usr/bin/env python3
"""Generate OAuth token for new Google Cloud project."""
import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pickle

# Configuration
CLIENT_SECRET_FILE = "client_secret4.json"
TOKEN_FILE = "token4.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload"
]

def main():
    print("🔐 Generating OAuth token for new project...")
    print(f"Client secret: {CLIENT_SECRET_FILE}")
    print(f"Token output: {TOKEN_FILE}")
    
    # Check if token already exists
    if os.path.exists(TOKEN_FILE):
        print(f"Token already exists: {TOKEN_FILE}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save token
    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())
    
    print(f"\n✅ Token saved to: {TOKEN_FILE}")
    print("You can now use this token for YouTube API operations.")

if __name__ == "__main__":
    main()
