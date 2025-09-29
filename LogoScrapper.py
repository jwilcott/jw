import requests
from bs4 import BeautifulSoup
import os
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin

def scrape_and_download_images(url, min_size=(500, 500)):
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Send a GET request to the URL
    response = requests.get(url)
    response.raise_for_status()
    
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all img tags
    images = soup.find_all('img')
    print(f"Found {len(images)} img tags on the page.")
    
    for img in images:
        img_url = img.get('src')
        if not img_url:
            continue
        
        # If src is data:, try data-src
        if img_url.startswith('data:'):
            img_url = img.get('data-src')
            if not img_url:
                continue
        
        # Handle relative URLs and protocol-relative URLs
        img_url = urljoin(url, img_url)
        
        # Skip data URLs or invalid URLs
        if img_url.startswith('data:') or not img_url.startswith(('http://', 'https://')):
            continue
        
        print(f"Processing image: {img_url}")
        
        try:
            # Download the image
            img_response = requests.get(img_url, timeout=10)
            img_response.raise_for_status()
            
            # Open the image with PIL to check size
            image = Image.open(BytesIO(img_response.content))
            width, height = image.size
            print(f"Image size: {width}x{height}")
            
            # Check if size is at least 500x500
            if width >= min_size[0] and height >= min_size[1]:
                # Generate a filename (use alt text or a default)
                alt_text = img.get('alt', 'image')
                alt_text = alt_text.replace(' ', '_').replace('/', '_').replace('\\', '_')
                filename = f"{alt_text}.png"
                filepath = os.path.join(script_dir, filename)
                
                # Avoid overwriting files by adding a counter if needed
                counter = 1
                original_filepath = filepath
                while os.path.exists(filepath):
                    name, ext = os.path.splitext(original_filepath)
                    filepath = f"{name}_{counter}{ext}"
                    counter += 1
                
                # Save as PNG
                image.save(filepath, 'PNG')
                print(f"Saved: {filepath}")
            else:
                print(f"Image too small: {width}x{height}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {img_url}: {e}")
        except Exception as e:
            print(f"Error processing {img_url}: {e}")

# URL to scrape
url = "https://www.nfl.com/teams/"
scrape_and_download_images(url)