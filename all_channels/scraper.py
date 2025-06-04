import requests
import time
import re

API_URL = "https://ppv.wtf/api/streams"
ORIGIN = "https://ppv.wtf"
REFERER = "https://ppv.wtf/"

def sanitize_tvg_id(name):
    # Remove special chars, lowercase, replace spaces with dots
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", ".", name)
    return name

now = int(time.time())
resp = requests.get(API_URL)
data = resp.json()

all_streams = []
for category in data.get("streams", []):
    for stream in category.get("streams", []):
        # Filter only live or upcoming
        if stream.get("always_live") == 1 or (stream.get("starts_at", 0) <= now < stream.get("ends_at", 0)) or (stream.get("starts_at", 0) > now):
            stream["category_name"] = category.get("category", "Unknown")
            all_streams.append(stream)

# Group by category
grouped = {}
for s in all_streams:
    cat = s.get("category_name", "Unknown")
    grouped.setdefault(cat, []).append(s)

with open("ppv.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for category, streams in grouped.items():
        for s in streams:
            name = s.get("name", "Unknown")
            logo = s.get("poster", "")
            tvg_id = sanitize_tvg_id(name)
            group_title = category
            url = s.get("iframe", "")

            # Append headers for Origin and Referer in URL (compatible with players like TiviMate)
            url_with_headers = f"{url}|Origin={ORIGIN}&Referer={REFERER}"

            f.write(f'#EXTINF:-1 group-title="{group_title}" tvg-id="{tvg_id}" tvg-logo="{logo}" tvg-name="{name}",{name}\n')
            f.write(f"{url_with_headers}\n")
        f.write("\n")
