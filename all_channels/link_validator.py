import os
import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    "https://nfsnew.newkso.ru/nfs/premium{num}/mono.m3u8",
    "https://windnew.newkso.ru/wind/premium{num}/mono.m3u8",
    "https://zekonew.newkso.ru/zeko/premium{num}/mono.m3u8",
    "https://dokko1new.newkso.ru/dokko1/premium{num}/mono.m3u8",
    "https://ddy6new.newkso.ru/ddy6/premium{num}/mono.m3u8"

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

def check_url_with_retries(url):
    """
    Check the given URL using HEAD (and fallback GET) requests.
    If a 429 is returned, retry up to 10 times before skipping.
    """
    global skipped_count
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
        'Origin': 'https://webxzplay.cfd',
        'Referer': 'https://webxzplay.cfd/'
    }
    attempt = 0
    while attempt < 10:
        attempt += 1
        try:
            print(f"🌍 Checking: {url} (Attempt {attempt})")
            response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)

            if response.status_code == 200:
                print(f"✅ {url} is valid (200).")
                return url, True
            elif response.status_code == 404:
                print(f"❌ {url} not found (404).")
                return url, False
            elif response.status_code == 429:
                print(f"⏳ {url} is rate-limited (429). Retrying in 5s...")
                time.sleep(5)
                continue  # Retry the request
            else:
                print(f"⚠️ {url} returned unexpected status {response.status_code}. Trying GET...")
                response = requests.get(url, headers=headers, allow_redirects=True, timeout=10, stream=True)

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
