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

# Check if the input file exists
if not os.path.exists(input_file):
    print(f"❌ Error: '{input_file}' not found. Please ensure the file exists.")
    exit(1)

# Regex to extract numbers from links
pattern = re.compile(r'premium(\d+)/mono\.m3u8')

# Set to store unique extracted numbers
extracted_numbers = set()

# Read the input file and extract numbers
with open(input_file, 'r', encoding='utf-8') as fin:
    for line in fin:
        for match in pattern.finditer(line):
            extracted_numbers.add(match.group(1))

if not extracted_numbers:
    print("⚠️ No numbers extracted. Verify the input file contains matching links.")
    exit(1)

print(f"✅ Extracted numbers: {extracted_numbers}")

# URL templates to check
url_templates = [
    "https://nfsnew.koskoros.ru/nfs/premium{num}/mono.m3u8",
    "https://windnew.koskoros.ru/wind/premium{num}/mono.m3u8",
    "https://zekonew.koskoros.ru/zeko/premium{num}/mono.m3u8",
    "https://dokko1new.koskoros.ru/dokko1/premium{num}/mono.m3u8",
    "https://ddy6new.koskoros.ru/ddy6/premium{num}/mono.m3u8"
]

# Generate all URLs to validate
url_list = [template.format(num=num) for num in extracted_numbers for template in url_templates]

if not url_list:
    print("⚠️ No URLs generated for validation.")
    exit(1)

print(f"🔎 Total URLs to check: {len(url_list)}")

# List to store valid links
valid_links = []

# Counter for skipped URLs
skipped_count = 0

# Fetch fresh proxies from Geonode API
def fetch_proxy_list():
    api_url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&protocols=http,https"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        proxy_data = json.loads(response.text)
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
        print(f"🚨 Failed to fetch proxies: {str(e)}")
        return []

# Test a proxy by making a simple request
def test_proxy(proxy):
    test_url = "http://example.com"  # Reliable test site
    try:
        response = requests.head(test_url, proxies={'http': proxy, 'https': proxy}, timeout=10)
        if response.status_code == 200:
            print(f"✅ Proxy {proxy} is working.")
            return True
        else:
            print(f"❌ Proxy {proxy} returned status {response.status_code}.")
            return False
    except requests.RequestException as e:
        print(f"❌ Proxy {proxy} failed: {str(e)}")
        return False

# Fetch and test proxies
proxy_list = fetch_proxy_list()
working_proxies = [proxy for proxy in proxy_list if test_proxy(proxy)]

if working_proxies:
    print(f"✅ Found {len(working_proxies)} working proxies.")
else:
    print("⚠️ No working proxies found. Falling back to direct requests.")

# Get a random working proxy
def get_working_proxy():
    return random.choice(working_proxies) if working_proxies else None

# Check URL with retries and proxy fallback
def check_url_with_retries(url):
    global skipped_count
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Origin': 'https://pkpakiplay.xyz',
        'Referer': 'https://pkpakiplay.xyz/'
    }
    proxy = get_working_proxy()
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    attempt = 0
    max_attempts = 10

    while attempt < max_attempts:
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
                proxy = None
            else:
                print(f"🚨 Direct request error for {url}: {error_msg}.")
                break

    print(f"⛔ Max retries reached for {url}. Skipping.")
    skipped_count += 1
    return url, False

# Check URLs concurrently
max_workers = 10
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_url = {executor.submit(check_url_with_retries, url): url for url in url_list}
    for future in as_completed(future_to_url):
        url, is_valid = future.result()
        if is_valid:
            valid_links.append(url)

print(f"✅ Total valid links: {len(valid_links)}")
print(f"⛔ Total skipped URLs: {skipped_count}")

# Write valid links to output file
with open(output_file, 'w', encoding='utf-8') as fout:
    for link in valid_links:
        fout.write(link + "\n")

print(f"🎉 Finished! Valid links written to {output_file}")
