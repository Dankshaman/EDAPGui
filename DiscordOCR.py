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
    
    lines = raw_text.split('\n')
    current_station_key = None
    known_commodities = ["BERTRANDITE", "GOLD", "INDITE", "SILVER"]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Pre-process line to handle common OCR errors
        processed_line = line.upper().replace('0', 'O').replace('1', 'I').replace('L', 'I')

        # State machine to determine current station
        if processed_line == "BURKIN":
            current_station_key = "BURKIN"
            continue
        elif processed_line == "DARITON" or processed_line == "DARLTON":
             current_station_key = "DARLTON"
             continue
        elif "WAIISY" in processed_line or "WALLY" in processed_line or "BEI" in processed_line or "MAIERBA" in processed_line or "MALERBA" in processed_line or "SWANSON" in processed_line:
            current_station_key = None
            continue

        if current_station_key:
            # Check if the line starts with a known commodity
            found_commodity = None
            for comm in known_commodities:
                if processed_line.startswith(comm):
                    found_commodity = comm
                    break
            
            if found_commodity:
                # The rest of the line should contain the carrier info.
                # We can now use a more targeted regex.
                line_after_commodity = line[len(found_commodity):].strip()
                match = re.search(r'x\s+([\d,O]+)\s+Tons\s+-\s+(.+?)\s+\(([A-Za-z0-9-]{7})\)', line_after_commodity)
                
                if match:
                    quantity_str = match.group(1).replace(',', '').replace('O', '0')
                    quantity = int(quantity_str)
                    carrier_name_part = match.group(2).strip()
                    carrier_id = match.group(3).strip()

                    carrier_name = f"{carrier_name_part} {carrier_id}".upper()

                    carrier_data = {
                        "carrier_name": carrier_name,
                        "commodity": found_commodity.capitalize(), # Use the cleaned commodity name
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
            image = screen.get_screen_rect_pct(region_data['rect'])
            ocr_textlist = ocr.image_simple_ocr(image)

            if ocr_textlist:
                # Join with newlines to preserve multi-line structure
                raw_text = "\n".join(ocr_textlist)
                
                formatted_data = parse_and_format_text(raw_text)

                with open("discord_data.json", "w") as f:
                    json.dump(formatted_data, f, indent=4)

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")

        time.sleep(60)


if __name__ == "__main__":
    main()
