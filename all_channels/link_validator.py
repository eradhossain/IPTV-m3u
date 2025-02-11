import os
import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Input and output file names.
input_file = "tivimate_playlist.m3u8"
output_file = "links.m3u8"

# Check if the input file exists before trying to open it.
if not os.path.exists(input_file):
    print(f"Error: '{input_file}' not found. Make sure the file is present before running the script.")
    exit(1)

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
    exit(1)

print("Extracted numbers:", extracted_numbers)
