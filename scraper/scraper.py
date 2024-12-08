# Context: This script scraped components from Chinese characters from dong-chinese.com

# Currently onyl attempts to downlaod data for the most common characters as listed in character_list.txt 

import os
import sys

# Add the lib directory to the Python path
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, lib_path)

# Third-party imports from lib directory
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests

# Import PIL from Anki's environment
import aqt
if hasattr(aqt, 'PIL'):
    from aqt.PIL import Image
else:
    from PIL import Image

# Standard library imports
import shutil
from datetime import datetime

failed_characters = set()
existing_component_images = set()  # New set to store existing image filenames


# Create images directory if it doesn't exist
images_dir = "scraper/images"
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

def load_existing_component_images():
    global existing_component_images
    if os.path.exists(images_dir):
        existing_component_images = {
            filename for filename in os.listdir(images_dir) 
            if filename.startswith('_component_') and filename.endswith('.png')
        }

def capture_chinese_character_section(character):
    # Check if character is in failed list
    if character in failed_characters:
        print(f"Skipping previously failed character: {character}")
        return None

    print(f"Capturing component for character: {character}")
    
    # Check if image already exists for this character using the set
    character_filename = f"_component_{ord(character)}.png"
    if character_filename in existing_component_images:
        print(f"Image already exists for character: {character}")
        return os.path.join("images", character_filename)

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
    
    screenshot_path = os.path.join(images_dir, "full_screenshot.png")
    
    try:
        component_text_element = WebDriverWait(driver, 0.2).until(
            EC.presence_of_element_located((
                By.XPATH, 
                "//span[contains(@class, 'MuiTypography-root') and contains(@class, 'MuiTypography-caption') and contains(@class, 'MuiTypography-colorTextSecondary') and text()='Components']"
            ))
        )
    except TimeoutException:
        print(f"Timeout: No component information found for character: {character}")
        failed_characters.add(character)
        driver.quit()
        return None
   
    
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
    
    # Save with underscore prefix for Anki in images directory
    output_path = os.path.join(images_dir, f"_component_{ord(character)}.png")
    cropped_image.save(output_path)
    return output_path
        
    driver.quit()
 
def get_all_chinese_characters_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            text = file.read()
            
        # Unicode ranges for Chinese characters
        chinese_chars = []
        seen = set()
        for char in text:
            # Skip ellipsis and check if character is unique
            if char == '…' or char in seen:
                continue
                
            # Check if character is in Chinese unicode ranges
            if ('\u4e00' <= char <= '\u9fff' or  # CJK Unified Ideographs
                '\u3400' <= char <= '\u4dbf' or  # CJK Unified Ideographs Extension A
                '\u20000' <= char <= '\u2a6df'): # CJK Unified Ideographs Extension B
                chinese_chars.append(char)
                seen.add(char)
                
        return chinese_chars
    except FileNotFoundError:
        print("Error: used_characters.txt not found")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def import_anki(filename):
    first_chars = []
   
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            # Skip empty lines and header lines
            if not line.strip() or line.startswith('#'):
                continue
            
            # Get the first character from each line
            if line[0]:
                first_chars.append(line[0])
    
    return first_chars

# Example usage
characters = import_anki("scraper/character_list.txt")
failed_characters = set(open("scraper/failed_characters.txt", 'r', encoding='utf-8').read().strip())

# Before the main loop, load existing images
load_existing_component_images()

ctr = 0
for character in characters:
    capture_chinese_character_section(character)
    ctr += 1

    if ctr % 30 == 0:
        with open("scraper/failed_characters.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(failed_characters))

with open("scraper/failed_characters.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(failed_characters))