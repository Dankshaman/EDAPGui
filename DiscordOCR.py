import json
import time
import re
from DiscordOCRHelper import OCR
from DiscordScreen import DiscordScreen


def get_discord_region():
    """
    Reads the discord region from the config file.
    """
    try:
        with open("discord_config.json", "r") as f:
            config = json.load(f)
            return config["region"]
    except FileNotFoundError:
        print("Error: discord_config.json not found. Please run calibrate_discord.py first.")
        return None
    except (KeyError, json.JSONDecodeError):
        print("Error: Invalid format in discord_config.json. Please run calibrate_discord.py again.")
        return None


def parse_and_format_text(raw_text):
    """
    Parses the raw OCR text and formats it into the desired JSON structure.
    """
    output = {
        "stations": {
            "BURKIN": [],
            "DARLTON": []
        }
    }

    # Define all known station headers to act as delimiters
    all_station_headers = ["MBUTAS BURKIN", "DARLTON", "WALLY BEI MALERBA", "SWANSON"]
    pattern = "|".join(all_station_headers)

    # Split the text by the station headers, keeping the delimiters
    parts = re.split(f'({pattern})', raw_text)

    current_station_key = None
    for part in parts:
        if part in all_station_headers:
            if part == "MBUTAS BURKIN":
                current_station_key = "BURKIN"
            elif part == "DARLTON":
                current_station_key = "DARLTON"
            else:
                current_station_key = None # Ignore other stations
        elif current_station_key and part.strip():
            # This part is the text block for a station of interest
            text_block = part

            # Regex to find all carrier entries in the block
            # This regex is more robust to handle variations in commodity names and OCR errors (O vs 0)
            carrier_matches = re.findall(r'([A-Za-z\s]+?)\s+x\s+([\d,O]+)\s+Tons\s+-\s+(.+?)\s+\(([A-Z0-9-]{7})\)', text_block)

            for match in carrier_matches:
                commodity = match[0].strip()
                # Handle OCR errors where 'O' is read instead of '0'
                quantity_str = match[1].replace(',', '').replace('O', '0')
                quantity = int(quantity_str)
                carrier_name_part = match[2].strip()
                carrier_id = match[3].strip()

                # Combine carrier name and ID, without parentheses
                carrier_name = f"{carrier_name_part} {carrier_id}"

                carrier_data = {
                    "carrier_name": carrier_name,
                    "commodity": commodity,
                    "quantity": quantity
                }
                output["stations"][current_station_key].append(carrier_data)

    return output


def main():
    """
    Main loop for the Discord OCR program.
    """
    region_data = get_discord_region()
    if not region_data:
        return

    try:
        screen = DiscordScreen()
        ocr = OCR(screen=None)
    except Exception as e:
        print(f"Error initializing screen or OCR: {e}")
        return

    while True:
        try:
            # Capture the screen region
            image = screen.get_screen_rect_pct(region_data['rect'])

            # Perform OCR on the image
            ocr_textlist = ocr.image_simple_ocr(image)

            # Process the text
            if ocr_textlist:
                raw_text = " ".join(ocr_textlist).strip()

                formatted_data = parse_and_format_text(raw_text)

                # Save data to JSON file
                with open("discord_data.json", "w") as f:
                    json.dump(formatted_data, f, indent=4)

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")

        # Wait for 60 seconds
        time.sleep(60)


if __name__ == "__main__":
    main()
