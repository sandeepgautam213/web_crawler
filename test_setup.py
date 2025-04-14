from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd

# Optional: Headless mode if you don't want to open a browser window
options = Options()
options.add_argument("--headless")  # Remove this line if you want to see the browser

# Use Service object correctly
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Now the rest of your code works fine
driver.get("https://www.example.com")
soup = BeautifulSoup(driver.page_source, 'html.parser')
print(soup.title.text)
driver.quit()
