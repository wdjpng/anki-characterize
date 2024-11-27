import os
import urllib.request
import shutil

def download_character_strokes(characters: list[str]) -> None:
    """
    Downloads stroke order images for Chinese characters from strokeorder.com
    
    Args:
        characters: List of Chinese characters to download stroke orders for
    """
    # Create characters directory if it doesn't exist
    if not os.path.exists('characters'):
        os.makedirs('characters')
        
    for char in characters:
        # Convert character to decimal unicode value
        decimal = ord(char)
        
        # Construct URL
        url = f'https://www.strokeorder.com/assets/bishun/stroke/{decimal}.png'
        print(url)
        try:
            # Create request with headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            req = urllib.request.Request(url, headers=headers)
            
            # Download image
            response = urllib.request.urlopen(req)
            
            # Save to characters folder
            output_path = os.path.join('characters', f'{char}_{decimal}.png')
            with open(output_path, 'wb') as f:
                shutil.copyfileobj(response, f)
                
            print(f'Successfully downloaded stroke order for {char} (decimal: {decimal})')
            
        except Exception as e:
            print(f'Failed to download stroke order for {char}: {str(e)}')

# Example usage:
characters = ['你', '好']
download_character_strokes(characters)
