from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from PIL import Image
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def capture_chinese_character_section(character):
    # Specify the correct path to your ChromiumDriver
    chromium_driver_path = '/usr/bin/chromedriver'  # Update this path

    # Set up Selenium with headless Chromium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = '/usr/bin/google-chrome-stable'
    # Create a Service object with the correct path
    service = Service(chromium_driver_path)

    # Initialize the Chrome WebDriver with the service
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
        # Set window size to 1920x1080
    driver.set_window_size(1920, 1080)
    
    # Construct the URL
    url = f"https://www.dong-chinese.com/wiki/{character}"
    print(url)
    driver.get(url)
    
    screenshot_path = "full_screenshot.png"
    
    try:
        component_text_element = WebDriverWait(driver, 0.2).until(
            EC.presence_of_element_located((
                By.XPATH, 
                "//span[contains(@class, 'MuiTypography-root') and contains(@class, 'MuiTypography-caption') and contains(@class, 'MuiTypography-colorTextSecondary') and text()='Components']"
            ))
        )
    except TimeoutException:
        print(f"No component information found for character: {character}")
        return
    
    print(component_text_element)
    print("Found the Components span element.")
    
    # Go two divs up from the found span element
    component_section = component_text_element.find_element(By.XPATH, "./ancestor::div[2]")
    
    # Get the location and size of the element
    location = component_section.location
    size = component_section.size
    
    # Take a screenshot of the entire page
    driver.save_screenshot(screenshot_path)
    
    # Open the screenshot and crop away top 28 pixels and white space
    image = Image.open(screenshot_path)
    width, height = image.size
    
    # Crop the image to the component section
    left = location['x']
    top = location['y']
    right = left + size['width']
    bottom = top + size['height']
    
    # Crop the image
    cropped_image = image.crop((left, top+28, right, bottom))
    
    # Find where the image becomes all white
    def find_last_non_white_column(img):
        width, height = img.size
        img_data = img.convert('RGB')
        
        for x in range(width - 1, -1, -1):  # Start from right
            column_is_white = True
            for y in range(height):
                pixel = img_data.getpixel((x, y))
                if pixel != (255, 255, 255):  # If pixel is not white
                    column_is_white = False
                    break
            if not column_is_white:
                return x + 1  # Return the position after the last non-white column
        return 0

    # Find the last non-white column and crop again
    last_content_column = find_last_non_white_column(cropped_image)
    if last_content_column > 0:
        cropped_image = cropped_image.crop((0, 0, last_content_column + min(20, cropped_image.width - last_content_column), cropped_image.height))
    
    # Save the cropped image
    output_path = f"character_{character}.png"
    cropped_image.save(output_path)
    return output_path
        
    driver.quit()
 

# Example usage
single_characters = [
    "没", "这", 
    "儿", "吗", "坐", "客", "气", "中", "国", "不", "错", "哪", 
    "里", "行", "刚", "到", "差", "还", "会", "英", "法", "日", 
    "意", "大", "利", "西", "班", "牙", "俄", "阿", "拉", "伯", 
    "韩", "点", "儿", "明", "天", "见", "对", "起", "关", "系", 
    "母", "官", "方", "怎", "么", "样"
]

for character in single_characters:
    capture_chinese_character_section(character)
