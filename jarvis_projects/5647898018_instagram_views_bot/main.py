import requests
import time
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Instagram video link
video_link = 'YOUR_VIDEO_LINK'

# Instagram account credentials
username = 'YOUR_USERNAME'
password = 'YOUR_PASSWORD'

# Set up Chrome driver
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
driver = webdriver.Chrome(options=options)

# Login to Instagram
def login():
    driver.get('https://www.instagram.com/accounts/login/')
    try:
        username_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
        password_input = driver.find_element(By.NAME, 'password')
        username_input.send_keys(username)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
    except TimeoutException:
        print('Login failed')
        return False
    return True

# Increase video views
def increase_views():
    driver.get(video_link)
    try:
        video = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'video')))
        for i in range(1000000):
            driver.execute_script('arguments[0].play()', video)
            time.sleep(1)
            driver.execute_script('arguments[0].pause()', video)
            print(f'View {i+1} increased')
    except TimeoutException:
        print('Failed to increase views')

# Main function
def main():
    if login():
        increase_views()
    else:
        print('Login failed')

if __name__ == '__main__':
    main()