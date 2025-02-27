import os
import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import json

# Input and output file names
input_file = "tivimate_playlist.m3u8"
output_file = "links.m3u8"

# Check if the input file exists before trying to open it
if not os.path.exists(input_file):
    print(f"❌ Error: '{input_file}' not found. Make sure the file is present before running the script.")
    exit(1)

# Compile a regex to extract numbers from links matching the pattern
pattern = re.compile(r'premium(\d+)/mono\.m3u8')

# Set to store unique extracted numbers
extracted_numbers = set()

# Read the input file and extract numbers
with open(input_file, 'r', encoding='utf-8') as fin:
    for line in fin:
        for match in pattern.finditer(line):
            extracted_numbers.add(match.group(1))

if not extracted_numbers:
    print("⚠️ No numbers were extracted. Please verify the input file contains links matching the pattern.")
    exit(1)

print(f"✅ Extracted numbers: {extracted_numbers}")

# URL templates where {num} will be replaced by the extracted number
url_templates = [
    "https://nfsnew.koskoros.ru/nfs/premium{num}/mono.m3u8",
    "https://windnew.koskoros.ru/wind/premium{num}/mono.m3u8",
    "https://zekonew.koskoros.ru/zeko/premium{num}/mono.m3u8",
    "https://dokko1new.koskoros.ru/dokko1/premium{num}/mono.m3u8",
    "https://ddy6new.koskoros.ru/ddy6/premium{num}/mono.m3u8"
]

# Build a list of all URLs to check
url_list = [template.format(num=num) for num in extracted_numbers for template in url_templates]

if not url_list:
    print("⚠️ No URLs generated for validation.")
    exit(1)

print(f"🔎 Total URLs to check: {len(url_list)}")

# List to store valid links
valid_links = []

# Add a counter for skipped URLs
skipped_count = 0

# Function to fetch fresh proxies from Geonode API
def fetch_proxy_list():
    api_url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&protocols=http,https"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        proxy_data = json.loads(response.text)
        # Extract HTTP/HTTPS proxies
        proxies = [
            f"http://{proxy['ip']}:{proxy['port']}"
            for proxy in proxy_data['data']
            if 'http' in proxy['protocols'] or 'https' in proxy['protocols']
        ]
        if not proxies:
            print("⚠️ No HTTP/HTTPS proxies found in API response.")
        else:
            print(f"✅ Fetched {len(proxies)} proxies from Geonode API.")
        return proxies
    except requests.RequestException as e:
        print(f"🚨 Failed to fetch proxies from Geonode API: {str(e)}")
        return []

# Get initial proxy list
proxy_list = fetch_proxy_list()

def get_free_proxy():
    if not proxy_list:
        return None  # No proxies available
    return random.choice(proxy_list)

def check_url_with_retries(url):
    """
    Check the given URL using HEAD (and fallback GET) requests with proxy, falling back to direct if proxy fails.
    If a 429 is returned, retry up to 10 times before skipping.
    """
    global skipped_count
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Origin': 'https://pkpakiplay.xyz',
        'Referer': 'https://pkpakiplay.xyz/'
    }
    proxy = get_free_proxy()
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    attempt = 0
    while attempt < 10:
        attempt += 1
        proxy_str = f"via {proxy}" if proxy else "direct"
        print(f"🌍 Checking: {url} (Attempt {attempt}) {proxy_str}")
        try:
            response = requests.head(url, headers=headers, proxies=proxies, allow_redirects=True, timeout=20)
            if response.status_code == 200:
                print(f"✅ {url} is valid (200).")
                return url, True
            elif response.status_code == 404:
                print(f"❌ {url} not found (404).")
                return url, False
            elif response.status_code == 429:
                print(f"⏳ {url} rate-limited (429). Retrying in 5s...")
                time.sleep(5)
                continue
            else:
                print(f"⚠️ {url} returned status {response.status_code}. Trying GET...")
                response = requests.get(url, headers=headers, proxies=proxies, allow_redirects=True, timeout=20, stream=True)
                if response.status_code == 200:
                    print(f"✅ {url} is valid (200) on GET.")
                    return url, True
                elif response.status_code == 404:
                    print(f"❌ {url} not found (404) on GET.")
                    return url, False
                else:
                    print(f"⚠️ {url} returned status {response.status_code} on GET.")
                    return url, False
        except requests.RequestException as e:
            error_msg = str(e)
            if proxy:
                print(f"🚨 Proxy error for {url} via {proxy}: {error_msg}. Falling back to direct request.")
                proxies = None  # Switch to direct request
            else:
                print(f"🚨 Direct request error for {url}: {error_msg}.")
                break  # Exit retry loop if direct request fails

    print(f"⛔ Max retries reached for {url}. Skipping.")
    skipped_count += 1
    return url, False

# Use ThreadPoolExecutor to check URLs concurrently
max_workers = 10  # Adjust as needed
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_url = {executor.submit(check_url_with_retries, url): url for url in url_list}
    for future in as_completed(future_to_url):
        url, is_valid = future.result()
        if is_valid:
            valid_links.append(url)

print(f"✅ Total valid links: {len(valid_links)}")
print(f"⛔ Total skipped URLs (max retries reached): {skipped_count}")

# Write valid links to the output file
with open(output_file, 'w', encoding='utf-8') as fout:
    for link in valid_links:
        fout.write(link + "\n")

print(f"🎉 Finished! Valid links have been written to {output_file}")
