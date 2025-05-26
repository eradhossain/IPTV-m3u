# main.py (final with strict enforcement + logging)
import os
import re
import sys
import time
import base64
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

CHANNELS_URL = 'https://josh9456-myproxy.hf.space/playlist/channels'
PREMIUM = re.compile(r'premium(\d+)/mono\.m3u8')
PROXY_PREFIX = 'https://josh9456-myproxy.hf.space/watch/'

# 1. Fetch channels

def fetch_channels(dest='channels.m3u8'):
    print(f"⬇️ Fetching channels from {CHANNELS_URL}")
    try:
        r = requests.get(CHANNELS_URL, timeout=10)
        if r.status_code == 200:
            with open(dest, 'wb') as f:
                f.write(r.content)
            print(f"✅ {dest} updated")
        else:
            print(f"❌ HTTP {r.status_code} from proxy server")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Download error: {e}")
        sys.exit(1)

# 2. Validate decoded stream URLs from proxy format

def validate_links(src='tivimate_playlist.m3u8', out='links.m3u8'):
    if not os.path.exists(src):
        print(f"❌ {src} missing.")
        sys.exit(1)

    decoded_urls = set()
    with open(src) as f:
        for line in f:
            line = line.strip()
            if line.startswith(PROXY_PREFIX):
                try:
                    b64 = line[len(PROXY_PREFIX):].split('.m3u8')[0]
                    url = base64.b64decode(b64).decode().strip()
                    decoded_urls.add(url)
                except Exception as e:
                    print(f"⚠️ Decode error: {e} in line {line}")

    ids = {match.group(1) for u in decoded_urls if (match := PREMIUM.search(u))}
    if not ids:
        print("⚠️ No premium IDs after decode.")
        sys.exit(1)

    print(f"✅ Premium IDs extracted: {ids}")

    templates = [
        'https://nfsnew.newkso.ru/nfs/premium{}/mono.m3u8',
        'https://windnew.newkso.ru/wind/premium{}/mono.m3u8',
        'https://zekonew.newkso.ru/zeko/premium{}/mono.m3u8',
        'https://dokko1new.newkso.ru/dokko1/premium{}/mono.m3u8',
        'https://ddy6new.newkso.ru/ddy6/premium{}/mono.m3u8'
    ]
    candidates = [t.format(i) for i in ids for t in templates]

    print(f"🔎 Validating {len(candidates)} URLs")
    valid = []

    def check(url):
        headers = {'User-Agent': 'Mozilla/5.0'}
        for _ in range(5):
            try:
                r = requests.head(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    return url
                if r.status_code == 429:
                    time.sleep(5)
                    continue
                if r.status_code == 404:
                    return None
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    return url
            except:
                return None
        return None

    with ThreadPoolExecutor(10) as ex:
        for result in ex.map(check, candidates):
            if result:
                valid.append(result)

    with open(out, 'w') as f:
        f.write('\n'.join(valid))

    print(f"🎉 {len(valid)} valid URLs written to {out}")

# 3. Map decoded URLs to proxy entries

def build_proxy_map(channels='channels.m3u8'):
    proxy_map = {}
    lines = open(channels).read().splitlines()
    for i in range(len(lines)-1):
        if lines[i].startswith('#EXTINF'):
            extinf = lines[i]
            stream = lines[i+1].strip()
            if '/watch/' in stream:
                try:
                    b64 = stream.split('/watch/')[1].split('.m3u8')[0]
                    original = base64.b64decode(b64).decode().strip()
                    proxy_map[original] = (extinf, stream)
                except:
                    continue
    print(f"✅ Loaded {len(proxy_map)} proxy mappings")
    return proxy_map

# 4. Assemble playlist with proxy-only strict replacement

def assemble(src='tivimate_playlist.m3u8', links='links.m3u8', channels='channels.m3u8'):
    valid = set(open(links).read().splitlines())
    proxy_map = build_proxy_map(channels)

    log_valid = []
    log_missing = []
    out = []

    lines = open(src).read().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF') and i+1 < len(lines):
            url_line = lines[i+1].strip()
            decoded = None
            if url_line.startswith(PROXY_PREFIX):
                try:
                    b64 = url_line[len(PROXY_PREFIX):].split('.m3u8')[0]
                    decoded = base64.b64decode(b64).decode().strip()
                except:
                    decoded = None
            if decoded and decoded in valid and decoded in proxy_map:
                ext, proxy_url = proxy_map[decoded]
                out.append(ext)
                out.append(proxy_url)
                log_valid.append(decoded)
            else:
                log_missing.append(decoded or url_line)
            i += 2
        else:
            i += 1

    with open(src, 'w') as f:
        f.write('\n'.join(out) + '\n')

    print(f"✅ Replaced {len(log_valid)} entries with proxies")
    if log_missing:
        print(f"⚠️ Skipped {len(log_missing)} entries (not validated or missing from proxy map)")
        with open('missing_proxies.txt', 'w') as m:
            m.write('\n'.join(log_missing))

if __name__ == '__main__':
    fetch_channels()
    print('=== Validating Stream Links ===')
    validate_links()
    print('=== Rewriting Playlist ===')
    assemble()
    print('✅ Done — Playlist updated with proxies only')
