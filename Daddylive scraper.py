from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import os
import json
import fetcher
import tvlogo  # Assuming this is the module that handles tv logo extraction

daddyLiveChannelsFileName = '247channels.html'
daddyLiveChannelsURL = 'https://thedaddy.to/24-7-channels.php'

tvLogosFilename = 'tvlogos.html'
tvLogosURL = 'https://github.com/tv-logo/tv-logos/tree/main/countries/united-states'

matches = []

def search_streams(file_path):
    """
    Scrapes all streams from a file without filtering by keyword.
    """
    matches = []  # to collect all matches

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                stream_number = href.split('-')[-1].replace('.php', '')
                stream_name = link.text.strip()
                match = (stream_number, stream_name)

                if match not in matches:
                    matches.append(match)

    except FileNotFoundError:
        print(f'The file {file_path} does not exist.')

    return matches

def search_channel_ids(file_path, idMatches):
    """
    Scrapes all channel IDs without filtering by search string.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for channel in root.findall('.//channel'):
            channel_id = channel.get('id')
            if channel_id and channel_id not in [entry['id'] for entry in idMatches]:
                idMatches.append({'id': channel_id, 'source': file_path})

    except FileNotFoundError:
        print(f'The file {file_path} does not exist.')
    except ET.ParseError:
        print(f'The file {file_path} is not a valid XML file.')

    return idMatches

def delete_file_if_exists(file_path):
    """
    Checks if a file exists and deletes it if it does.
    """
    if os.path.isfile(file_path):
        os.remove(file_path)
        print(f'File {file_path} deleted.')
        return True
    else:
        print(f'File {file_path} does not exist.')
        return False

delete_file_if_exists('out.m3u8')
delete_file_if_exists('tvg-ids.txt')

epgs = [
    {'filename': 'epgShare1.xml', 'url': 'https://www.dropbox.com/scl/fi/7r7h1jdufwoplnhhxkism/m3u4u-103216-593044-EPG.xml?rlkey=606vswc00na76l51otnz116ed&st=q273qocn&dl=1'},
    {'filename': 'epgShare2.xml', 'url': 'https://www.dropbox.com/scl/fi/tsj8796ea6krin4pv4t32/m3u4u-103216-595541-EPG.xml?rlkey=tu42144366j5w0n2s8fc1ogvp&st=2gg7ylx2&dl=1'},
    {'filename': 'epgShare3.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_US1.xml.gz'},
    {'filename': 'epgShare4.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS2.xml.gz'},
    {'filename': 'epgShare5.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_CA1.xml.gz'},
    {'filename': 'epgShare6.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz'},
    {'filename': 'epgShare7.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz'},
    {'filename': 'epgShare8.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_IE1.xml.gz'},
    {'filename': 'epgShare9.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz'},
    {'filename': 'epgShare10.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_ZA1.xml.gz'},
    {'filename': 'epgShare11.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_FR1.xml.gz'},
    {'filename': 'epgShare12.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_CL1.xml.gz'},
    {'filename': 'epgShare13.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_BR1.xml.gz'},
    {'filename': 'epgShare14.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_BG1.xml.gz'},
    {'filename': 'epgShare15.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_DK1.xml.gz'},
    {'filename': 'epgShare16.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_GR1.xml.gz'},
    {'filename': 'epgShare17.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_IL1.xml.gz'},
    {'filename': 'epgShare18.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz'},
    {'filename': 'epgShare19.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_MY1.xml.gz'},
    {'filename': 'epgShare20.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_MX1.xml.gz'},
    {'filename': 'epgShare21.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_NL1.xml.gz'},
    {'filename': 'epgShare22.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_NZ1.xml.gz'},
    {'filename': 'epgShare23.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_CZ1.xml.gz'},
    {'filename': 'epgShare24.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_SG1.xml.gz'},
    {'filename': 'epgShare25.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_PK1.xml.gz'},
    {'filename': 'epgShare26.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_RO1.xml.gz'},
    {'filename': 'epgShare27.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_CH1.xml.gz'},
    {'filename': 'epgShare28.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_PL1.xml.gz'},
    {'filename': 'epgShare29.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_SE1.xml.gz'},
    {'filename': 'epgShare30.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_UY1.xml.gz'},
    {'filename': 'epgShare31.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_CO1.xml.gz'},
    {'filename': 'epgShare32.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz'},
    {'filename': 'epgShare33.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_ES1.xml.gz'},
    {'filename': 'epgShare34.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_TR1.xml.gz'},
    {'filename': 'epgShare35.xml', 'url': 'https://epgshare01.online/epgshare01/epg_ripper_FANDUEL1.xml.gz'},
    {'filename': 'epgShare36.xml', 'url': 'https://epg.pw/api/epg.xml?channel_id=8486'},
    {'filename': 'epgShare37.xml', 'url': 'https://epg.pw/api/epg.xml?channel_id=12358'},
    {'filename': 'epgShare38.xml', 'url': 'https://epg.pw/api/epg.xml?channel_id=9206'}
]

fetcher.fetchHTML(daddyLiveChannelsFileName, daddyLiveChannelsURL)
fetcher.fetchHTML(tvLogosFilename, tvLogosURL)

for epg in epgs:
    fetcher.fetchXML(epg['filename'], epg['url'])

# Fetch all streams without the need for search terms
matches = search_streams(daddyLiveChannelsFileName)

payload = tvlogo.extract_payload_from_file(tvLogosFilename)
print(json.dumps(payload, indent=2))

# Example usage with search_channel_ids function
idMatches = []
for epg in epgs:
    idMatches = search_channel_ids(epg['filename'], idMatches)

for channel in matches:
    word = channel[1].lower().replace('channel', '').replace('hdtv', '').replace('tv','').replace(' hd', '').replace('2','').replace('sports','').replace('1','').replace('usa','')
    possibleIds = []

    # Directly skip the user input question for all channels.
    print("Searching for matches...")
    for epg in epgs:
        idMatches = search_channel_ids(epg['filename'], idMatches)  # Correctly call the function with 2 arguments

    matches = tvlogo.search_tree_items(word, payload)

    channelID = possibleIds[0] if possibleIds else None

    if channelID:
        tvicon = possibleIds[0] if possibleIds else {'id': {'path': ''}}

        with open("out.m3u8", 'a', encoding='utf-8') as file:  # Use 'a' mode for appending
            initialPath = payload.get('initial_path')
            file.write(f'#EXTINF:-1 tvg-id="{channelID["id"]}" tvg-name="{channel[1]}" tvg-logo="https://raw.githubusercontent.com{initialPath}{tvicon["id"]["path"]}" group-title="USA (DADDY LIVE)", {channel[1]}\n')
            file.write(f"https://xyzdddd.mizhls.ru/lb/premium{channel[0]}/index.m3u8\n")
            file.write('\n')

        with open("tvg-ids.txt", 'a', encoding='utf-8') as file:  # Use 'a' mode for appending
            file.write(f'{channelID["id"]}\n')

print("Number of Streams: ", len(matches))
