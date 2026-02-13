import requests
import time
import random
import argparse
import os
import sys
import subprocess
import github

# Instagram video link
video_link = input("Enter the Instagram video link: ")

# Instagram API endpoint
api_endpoint = "https://i.instagram.com/api/v1/media/{media_id}/view/"

# User agent to mimic a mobile browser
user_agent = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36"

# Function to send a view request
def send_view(media_id):
    headers = {
        "User-Agent": user_agent,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": "sessionid=YOUR_SESSION_ID"
    }
    response = requests.post(api_endpoint.format(media_id=media_id), headers=headers)
    if response.status_code == 200:
        print("View sent successfully")
    else:
        print("Failed to send view")

# Extract media ID from video link
media_id = video_link.split("/")[-2]

# Command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument("--install", action="store_true", help="Install dependencies")
parser.add_argument("--github", action="store_true", help="Push to GitHub")
parser.add_argument("--run", action="store_true", help="Run the project")
args = parser.parse_args()

if args.install:
    subprocess.run(["pip", "install", "-r", "requirements.txt"])
    print("Dependencies installed successfully")
elif args.github:
    try:
        from github import Github
        g = Github("YOUR_GITHUB_TOKEN")
        repo = g.get_repo("your-username/your-repo-name")
        repo.create_file("/code_github", "Initial commit", "This is the initial commit")
        print("Pushed to GitHub successfully")
    except Exception as e:
        print("Failed to push to GitHub: " + str(e))
elif args.run:
    print("Running...")
    while True:
        send_view(media_id)
        time.sleep(1)
