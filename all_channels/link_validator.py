import os
import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

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

# Function to get a random proxy from the list
def get_free_proxy():
    proxy_list = [
        'http://139.162.78.109:8080',    # Japan
        'http://222.252.194.204:8080',   # Vietnam
        'http://195.25.20.155:3128',     # France
        'http://198.74.51.79:8888',      # USA
        'http://51.68.175.56:1080',      # France
        'http://45.61.159.42:3128',      # USA
        'http://47.252.50.153:3128',     # USA
        'http://63.32.1.88:3128',        # Ireland
        'http://47.238.67.96:8888',      # Hong Kong
        'http://3.21.101.158:3128',      # USA
        'http://3.126.147.182:80',       # Germany
        'http://43.135.78.162:30004',    # Hong Kong
        'http://65.108.195.47:8080',     # Finland
        'http://13.36.87.105:3128',      # France
        'http://13.36.113.81:3128',      # France
        'http://13.36.104.85:80'         # France
    ]
    return random.choice(proxy_list)

def check_url_with_retries(url):
    """
    Check the given URL using HEAD (and fallback GET) requests.
    If a 429 is returned, retry up to 10 times before skipping.
    """
    global skipped_count
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Origin': 'https://pkpakiplay.xyz',
        'Referer': 'https://pkpakiplay.xyz/'
    }
    # Get a random proxy for this request
    proxy = get_free_proxy()
    proxies = {'http': proxy, 'https': proxy}
    attempt = 0
    while attempt < 10:
        attempt += 1
        try:
            print(f"🌍 Checking: {url} (Attempt {attempt}) via {proxy}")
            response = requests.head(url, headers=headers, proxies=proxies, allow_redirects=True, timeout=10)

            if response.status_code == 200:
                print(f"✅ {url} is valid (200).")
                return url, True
            elif response.status_code == 404:
                print(f"❌ {url} not found (404).")
                return url, False
            elif response.status_code == 429:
                print(f"⏳ {url} rate-limited (429). Retrying in 5s...")
                time.sleep(5)
                continue  # Retry the request
            else:
                print(f"⚠️ {url} returned unexpected status {response.status_code}. Trying GET...")
                response = requests.get(url, headers=headers, proxies=proxies, allow_redirects=True, timeout=10, stream=True)

                if response.status_code == 200:
                    print(f"✅ {url} is valid (200) on GET.")
                    return url, True
                elif response.status_code == 404:
                    print(f"❌ {url} not found (404) on GET.")
                    return url, False
                else:
                    print(f"⚠️ {url} returned unexpected status {response.status_code} on GET.")
                    return url, False
        except requests.RequestException as e:
            print(f"🚨 Request error for {url}: {e}.")
            return url, False

    print(f"⛔ Max retries reached for {url}. Skipping.")
    skipped_count += 1  # Increment skipped counter
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
