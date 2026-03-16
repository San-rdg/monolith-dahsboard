import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime

# Configuration
CACHE_FILE = "live_cache.json"
CACHE_EXPIRY = 3600  # 1 hour
TARGET_ITEMS = [
    "Tokyo Super Cement", 
    "Insee Sanstha Cement", 
    "Melwa TMT Steel", 
    "Lanwa TMT Steel",
    "River Sand",
    "Metal 3/4"
]

def fetch_live_prices():
    """
    Scrapes Ikman.lk for construction material prices and returns a list of data points.
    Uses local caching to prevent rate limiting.
    """
    # 1. Check Cache
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
            if time.time() - cache_data.get('timestamp', 0) < CACHE_EXPIRY:
                return cache_data.get('data', [])

    # 2. Scrape Data
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://ikman.lk/',
        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }

    all_results = []
    
    for item in TARGET_ITEMS:
        try:
            url = f"https://ikman.lk/en/ads/sri-lanka/building-materials?query={item.replace(' ', '%20')}"
            response = scraper.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Even more flexible searching
                listings = soup.find_all(['li', 'div'], class_=re.compile(r'(normal|item|ad-item).*'))[:3] 
                
                for listing in listings:
                    try:
                        name_tag = listing.find(['h2', 'span'], class_=re.compile(r'(title|name).*'))
                        price_tag = listing.find(['div', 'span'], class_=re.compile(r'.*price.*'))
                        
                        if name_tag and price_tag and 'Rs' in price_tag.text:
                            name = name_tag.text.strip()
                            price_str = re.sub(r'[^\d.]', '', price_tag.text)
                            price = float(price_str)
                            
                            all_results.append({
                                "timestamp": datetime.now().isoformat(),
                                "item": f"{name} (Live)",
                                "price": price,
                                "source": "Ikman_Live",
                                "base_category": item
                            })
                    except Exception:
                        continue
            time.sleep(1)
        except Exception as e:
            print(f"Error scraping {item}: {e}")

    # 3. Update Cache
    if all_results:
        with open(CACHE_FILE, 'w') as f:
            json.dump({
                "timestamp": time.time(),
                "data": all_results
            }, f)
            
    return all_results

if __name__ == "__main__":
    print("Initializing Live Scraper...")
    data = fetch_live_prices()
    print(f"Success: Retrieved {len(data)} live data points.")
    for d in data[:5]:
        print(f"- {d['item']}: Rs. {d['price']}")

