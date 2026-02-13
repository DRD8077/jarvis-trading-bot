import requests
import time
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import subprocess
import argparse

# Set up Chrome driver
options = Options()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Increase video views
def increase_views(video_link, num_views):
    driver.get(video_link)
    try:
        video = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'video')))
        for i in range(num_views):
            driver.execute_script('arguments[0].play()', video)
            time.sleep(1)
            driver.execute_script('arguments[0].pause()', video)
            print(f'View {i+1} increased')
    except TimeoutException:
        print('Failed to increase views')

# Push to GitHub
def push_to_github():
    try:
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', 'Updated code'])
        subprocess.run(['git', 'push'])
        print('Code pushed to GitHub successfully')
    except Exception as e:
        print(f'Failed to push code to GitHub: {e}')

# Install dependencies
def install_dependencies():
    try:
        subprocess.run(['pip', 'install', '-r', 'requirements.txt'])
        print('Dependencies installed successfully')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Instagram View Increaser')
    parser.add_argument('--video_link', type=str, help='Instagram video link')
    parser.add_argument('--num_views', type=int, default=1000000, help='Number of views to increase')
    args = parser.parse_args()
    increase_views(args.video_link, args.num_views)
