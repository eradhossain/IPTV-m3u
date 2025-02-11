import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Input and output file names.
input_file = "tivimate_playlist.m3u8"
output_file = "links.m3u8"

# Compile a regex to extract numbers from links like:
# https://ddh2new.iosplayer.ru/ddh2/premium<number>/mono.m3u8
pattern = re.compile(r'https://ddh2new\.iosplayer\.ru/ddh2/premium(\d+)/mono\.m3u8')

# Set to store unique extracted numbers.
extracted_numbers = set()

# Read the input file and extract numbers.
with open(input_file, 'r', encoding='utf-8') as fin:
    for line in fin:
        for match in pattern.finditer(line):
            extracted_numbers.add(match.group(1))

if not extracted_numbers:
    print("No numbers were extracted. Please verify the input file contains links matching the pattern.")
else:
    print("Extracted numbers:", extracted_numbers)

# URL templates where {num} will be replaced by the extracted number.
url_templates = [
    "https://dokko1new.iosplayer.ru/dokko1/premium{num}/mono.m3u8",
    "https://windnew.iosplayer.ru/wind/premium{num}/mono.m3u8",
    "https://ddh2new.iosplayer.ru/ddh2/premium{num}/mono.m3u8",
    "https://zekonew.iosplayer.ru/zeko/premium{num}/mono.m3u8",
    "https://ddy6new.iosplayer.ru/ddy6/premium{num}/mono.m3u8"
]

# Build a list of all URLs to check.
url_list = []
for num in extracted_numbers:
    for template in url_templates:
        url = template.format(num=num)
        url_list.append(url)

print(f"Total URLs to check: {len(url_list)}")

# List to store valid links.
valid_links = []

def check_url_with_retries(url):
    """
    Check the given URL using HEAD (and fallback GET) requests.
    If a 429 is returned, retry after a delay until a 200 or 404 is received.
    Returns a tuple (url, is_valid) where is_valid is True if the URL returned 200.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            if response.status_code == 429:
                print(f"[{url}] Attempt {attempt}: Rate limited (429). Retrying after delay...")
                time.sleep(5)
                continue
            elif response.status_code == 200:
                print(f"[{url}] Attempt {attempt}: Valid (200).")
                return url, True
            elif response.status_code == 404:
                print(f"[{url}] Attempt {attempt}: Not found (404).")
                return url, False
            else:
                # If HEAD returns an unexpected code, try GET as a fallback.
                response = requests.get(url, allow_redirects=True, timeout=10, stream=True)
                if response.status_code == 429:
                    print(f"[{url}] Attempt {attempt}: Rate limited (429) on GET. Retrying after delay...")
                    time.sleep(5)
                    continue
                elif response.status_code == 200:
                    print(f"[{url}] Attempt {attempt}: Valid (200) on GET.")
                    return url, True
                elif response.status_code == 404:
                    print(f"[{url}] Attempt {attempt}: Not found (404) on GET.")
                    return url, False
                else:
                    print(f"[{url}] Attempt {attempt}: Returned status code {response.status_code}.")
                    return url, False
        except requests.RequestException as e:
            print(f"[{url}] Attempt {attempt}: Request exception: {e}.")
            return url, False

# Use a ThreadPoolExecutor to check URLs concurrently.
max_workers = 10  # Adjust as needed; too many workers might trigger more rate limiting.
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_url = {executor.submit(check_url_with_retries, url): url for url in url_list}
    for future in as_completed(future_to_url):
        url, is_valid = future.result()
        if is_valid:
            valid_links.append(url)

print(f"Total valid links: {len(valid_links)}")

# Write valid links to the output file.
with open(output_file, 'w', encoding='utf-8') as fout:
    for link in valid_links:
        fout.write(link + "\n")

print(f"Finished! Valid links have been written to {output_file}")
