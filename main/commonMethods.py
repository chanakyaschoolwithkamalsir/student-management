import time, os

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

# def get_whatsapp_driver():
#     options = webdriver.ChromeOptions()
#     options.accept_insecure_certs = True
#     options.add_argument("disable-infobars")
#     # options.add_experimental_option('prefs',prefs)
#     options.add_argument("--disable-extensions")
#     options.add_argument('--no-sandbox')
#     options.page_load_strategy = 'normal'
#     options.binary_location ='C:\Program Files\Google\Chrome\Application\chrome.exe' 

#     chrome_driver_path = os.getcwd() + '\chromedriver\chromedriver.exe'
#     service = Service(executable_path=chrome_driver_path)
#     driver = webdriver.Chrome(service=service, options=options)

#     url = 'https://web.whatsapp.com/'
    
#     driver.get(url)

#     return driver


def send_whatsapp_msg(driver, mobile_number, name):
    FLAG = True
    while FLAG:
        try:
            wait = WebDriverWait(driver, 120)
            search_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Search or start new chat"]')))
            search_button.click()
            FLAG = False
        except:
            time.sleep(5)
            raise

    search_box = driver.find_element_by_xpath('/html/body/div[1]/div/div/div[4]/div/div[1]/div/div/div[2]/div/div[1]')
    search_box.send_keys(mobile_number)
    search_box.send_keys(Keys.RETURN)

    time.sleep(2)

    message_box = driver.find_element_by_xpath('/html/body/div[1]/div/div/div[5]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div[2]/div[1]')
    message_box.send_keys(f"Hello {name}, this is an automated message sent using Python and Selenium!")

    send_button = driver.find_element_by_xpath("//span[@data-icon='send']")
    send_button.click()

def send_whatsapp_file(driver, file_path, mobile_number):
    search_box = driver.find_element('xpath', '/html/body/div[1]/div/div/div[4]/div/div[1]/div/div/div[2]/div/div[1]')
    search_box.send_keys(mobile_number)
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)

    attachment_box = driver.find_element('xpath', '//div[@title = "Attach"]')
    attachment_box.click()

    image_box = driver.find_element('xpath', 
        '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
    image_box.send_keys(file_path)

    time.sleep(3)

    send_button = driver.find_element('xpath', '/html/body/div[1]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[2]/div[2]/div/div')
    send_button.click()