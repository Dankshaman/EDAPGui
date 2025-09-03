import json
import time
import re
import cv2
from ocr_client import OCR
from DiscordScreen import DiscordScreen

# --- DEBUG SETTING ---
# Set to True to export the raw OCR text to a file for debugging
DEBUG_EXPORT_RAW_TEXT = True
# ---------------------


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
    
    # Dictionary to map common OCR errors to the correct commodity name
    commodity_map = {
        "BERTRANDITE": "Bertrandite","BERTRANDLTE": "Bertrandte",
        "GOLD": "Gold", "GOID": "Gold", "G0ID": "Gold", "G0LD": "Gold",
        "INDITE": "Indite", "IND1TE": "Indite", "Indlte": "Indite", "lndlte": "Indite",
        "SILVER": "Silver", "SIIVER": "Silver", "SLLVER": "Silver", "SIIVER": "Silver"
    }

    lines = raw_text.split('\n')
    current_station_key = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Station detection logic
        station_check_line = line.upper().replace('0', 'O').replace('1', 'I').replace('L', 'I')
        if "BURKIN" in station_check_line:
            current_station_key = "BURKIN"
            continue
        elif "DARLTON" in station_check_line or "DARITON" in station_check_line:
            current_station_key = "DARLTON"
            continue
        elif "WALLY" in station_check_line or "BEI" in station_check_line or "MALERBA" in station_check_line or "PAEMARA" in station_check_line or "RUKAVISHNIKOV" in station_check_line or "TERMINAL" in station_check_line or "SWANSON" in station_check_line:
            current_station_key = None
            continue

        if current_station_key:
            # Two-step parsing for robustness
            loose_match = re.search(r'(.+?)\s+x\s+([\d,O]+)\s+Tons\s+-\s+(.+)', line)
            if loose_match:
                candidate_commodity = loose_match.group(1).strip()
                quantity_part = loose_match.group(2).strip()
                carrier_part = loose_match.group(3).strip()

                # Clean the candidate commodity and look it up in the map
                processed_commodity = candidate_commodity.upper().replace('0', 'O').replace('1', 'I').replace('|', 'I').replace('L', 'I')
                
                if processed_commodity in commodity_map:
                    correct_commodity_name = commodity_map[processed_commodity]
                    
                    carrier_match = re.search(r'(.+?)\s+\(([A-Za-z0-9-]{7})\)', carrier_part)
                    if carrier_match:
                        carrier_name_part = carrier_match.group(1).strip()
                        carrier_id = carrier_match.group(2).strip()

                        quantity = int(quantity_part.replace(',', '').replace('O', '0'))
                        carrier_name = f"{carrier_name_part} {carrier_id}".upper()
                        
                        carrier_data = {
                            "carrier_name": carrier_name,
                            "commodity": correct_commodity_name,
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

            # Pre-process the image to improve OCR accuracy
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Binarize the image - use THRESH_BINARY_INV for white text on dark background
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

            ocr_textlist = ocr.image_simple_ocr(thresh)

            if ocr_textlist:
                raw_text = "\n".join(ocr_textlist)
                
                if DEBUG_EXPORT_RAW_TEXT:
                    with open("raw_ocr_output.txt", "w", encoding="utf-8") as f:
                        f.write(raw_text)

                formatted_data = parse_and_format_text(raw_text)

                with open("discord_data.json", "w") as f:
                    json.dump(formatted_data, f, indent=4)

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")

        time.sleep(60)


if __name__ == "__main__":
    main()
