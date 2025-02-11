import re

# Define file names.
valid_links_file = "links.m3u8"                     # Contains valid links (one per line)
input_playlist_file = "updated_tivimate_playlist.m3u8"
output_playlist_file = "completed_tivimate_playlist.m3u8"

# Step 1: Load valid links from valid_links_file into a dictionary.
# We'll map the premium number (as a string) to the valid link.
valid_links_dict = {}

print("Loading valid links from", valid_links_file)
with open(valid_links_file, 'r', encoding='utf-8') as vf:
    for line in vf:
        link = line.strip()
        if not link:
            continue  # skip empty lines
        # Extract the number following 'premium' in the link.
        m = re.search(r'premium(\d+)/mono\.m3u8', link)
        if m:
            num = m.group(1)
            # If more than one valid link exists for the same number, we'll keep the first one.
            if num not in valid_links_dict:
                valid_links_dict[num] = link
                print(f"  Loaded valid link for premium{num}: {link}")
            else:
                print(f"  Duplicate valid link for premium{num} found; ignoring: {link}")
        else:
            print(f"  WARNING: Could not extract premium number from link: {link}")

print(f"Total valid links loaded: {len(valid_links_dict)}")
print()

# Step 2: Open the updated playlist and replace links based on premium number.
print("Processing playlist:", input_playlist_file)
lines_processed = 0
replacements_made = 0
output_lines = []

with open(input_playlist_file, 'r', encoding='utf-8') as fin:
    for line in fin:
        lines_processed += 1
        # If the line is a metadata line (starts with "#"), leave it unchanged.
        if line.startswith("#"):
            output_lines.append(line)
            continue

        # Otherwise, assume the line contains a URL (possibly with extra parameters after a pipe).
        # Split the line on the pipe; the first part should be the URL.
        parts = line.strip().split("|")
        url_part = parts[0].strip()

        # Look for a premium number in the URL.
        m = re.search(r'premium(\d+)', url_part)
        if m:
            num = m.group(1)
            if num in valid_links_dict:
                old_url = url_part
                new_url = valid_links_dict[num]
                parts[0] = new_url
                replacements_made += 1
                print(f"Line {lines_processed}: Replacing URL for premium{num}")
                print(f"  Old URL: {old_url}")
                print(f"  New URL: {new_url}")
            else:
                print(f"Line {lines_processed}: premium{num} not found in valid links. Leaving unchanged.")
        else:
            print(f"Line {lines_processed}: No premium number found. No replacement made.")

        # Reassemble the line (preserving any extra parameters, if they exist).
        new_line = "|".join(parts)
        output_lines.append(new_line + "\n")

print()
print(f"Processing complete. {lines_processed} lines processed with {replacements_made} replacements made.")

# Step 3: Write the updated content to the output file.
with open(output_playlist_file, 'w', encoding='utf-8') as fout:
    fout.writelines(output_lines)

print(f"Output written to {output_playlist_file}")
