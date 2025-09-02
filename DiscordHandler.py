import json
import time
import re
import threading
import cv2
import win32gui
import numpy as np
from paddleocr import PaddleOCR
import mss
import logging
from strsimpy.sorensen_dice import SorensenDice

from EDlogger import logger

# Configure logging for paddleocr to be less verbose
logging.getLogger('ppocr').setLevel(logging.ERROR)


def find_discord_hwnd():
    """Finds the hwnd of the Discord window."""
    def enum_windows_proc(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "discord" in title.lower():
                lParam.append(hwnd)

    hwnds = []
    win32gui.EnumWindows(enum_windows_proc, hwnds)
    return hwnds[0] if hwnds else None


class DiscordScreen:
    """Handles screen capture of the Discord window."""
    def __init__(self):
        self.mss = mss.mss()
        self.hwnd = find_discord_hwnd()
        if self.hwnd is None:
            raise Exception("Could not find Discord window. Please make sure Discord is running.")

        self.rect = win32gui.GetWindowRect(self.hwnd)
        self.screen_width = self.rect[2] - self.rect[0]
        self.screen_height = self.rect[3] - self.rect[1]

    def get_screen_rect_pct(self, rect_pct):
        """Grabs a screenshot of the window and returns the selected region as an image."""
        abs_rect = self.screen_rect_to_abs(rect_pct)
        monitor = {
            "top": self.rect[1] + abs_rect[1],
            "left": self.rect[0] + abs_rect[0],
            "width": abs_rect[2] - abs_rect[0],
            "height": abs_rect[3] - abs_rect[1],
        }
        image = np.array(self.mss.grab(monitor))
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        return image

    def screen_rect_to_abs(self, rect):
        """Converts percentage screen values to absolute pixel values."""
        return [
            int(rect[0] * self.screen_width), int(rect[1] * self.screen_height),
            int(rect[2] * self.screen_width), int(rect[3] * self.screen_height)
        ]


class DiscordOCR:
    """Handles OCR processing using PaddleOCR."""
    def __init__(self, use_gpu: bool = False):
        self.paddleocr = PaddleOCR(use_angle_cls=False, lang='en', use_gpu=use_gpu, show_log=False, use_dilation=True, use_space_char=True)
        self.sorensendice = SorensenDice()

    def image_simple_ocr(self, image) -> list[str] | None:
        """Performs OCR on an image and returns a list of strings."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        ocr_data = self.paddleocr.ocr(thresh)
        if ocr_data is None:
            return None

        ocr_textlist = []
        for res in ocr_data:
            if res is None:
                return None
            for line in res:
                ocr_textlist.append(line[1][0])
        return ocr_textlist


class DiscordHandler(threading.Thread):
    """
    A threaded handler to perform OCR on the Discord window for wing mining data.
    """
    def __init__(self, ed_ap, use_gpu=False):
        super().__init__()
        self.name = "DiscordHandlerThread"
        self.daemon = True
        self.ap = ed_ap
        self.running = False
        self.use_gpu = use_gpu
        self.data = {"stations": {"BURKIN": [], "DARLTON": []}}
        self.lock = threading.Lock()
        self.ocr_region = None

    def get_data(self):
        """Safely returns a copy of the latest OCR data."""
        with self.lock:
            return self.data.copy()

    def stop(self):
        """Stops the thread."""
        self.running = False
        logger.info("Discord OCR handler stopping.")

    def run(self):
        """Main loop for the Discord OCR thread."""
        self.running = True
        logger.info("Discord OCR handler started.")

        try:
            self.screen = DiscordScreen()
            self.ocr = DiscordOCR(use_gpu=self.use_gpu)
        except Exception as e:
            logger.error(f"Failed to initialize Discord OCR handler: {e}")
            self.running = False
            return

        while self.running:
            try:
                # Load region from the main app's calibration data
                if 'Discord.OCR' in self.ap.ocr_calibration_data:
                    self.ocr_region = self.ap.ocr_calibration_data['Discord.OCR']['rect']
                else:
                    logger.warning("Discord OCR region not calibrated. Using default.")
                    # Default region if not calibrated
                    self.ocr_region = [0.25, 0.25, 0.75, 0.75]

                image = self.screen.get_screen_rect_pct(self.ocr_region)
                ocr_textlist = self.ocr.image_simple_ocr(image)

                if ocr_textlist:
                    raw_text = "\n".join(ocr_textlist)
                    formatted_data = self._parse_and_format_text(raw_text)
                    with self.lock:
                        self.data = formatted_data
                else:
                    # Clear data if nothing is found
                    with self.lock:
                        self.data = {"stations": {"BURKIN": [], "DARLTON": []}}

            except Exception as e:
                logger.error(f"An error occurred in the Discord OCR loop: {e}")
                # Clear data on error
                with self.lock:
                    self.data = {"stations": {"BURKIN": [], "DARLTON": []}}

            # Wait for the next cycle or until stopped
            for _ in range(60):
                if not self.running:
                    break
                time.sleep(1)

    def _parse_and_format_text(self, raw_text):
        """Parses the raw OCR text and formats it into the desired JSON structure."""
        output = {"stations": {"BURKIN": [], "DARLTON": []}}

        commodity_map = {
            "BERTRANDITE": "Bertrandite", "BERTRANDLTE": "Bertrandite",
            "GOLD": "Gold", "GOID": "Gold", "G0ID": "Gold", "G0LD": "Gold",
            "INDITE": "Indite", "IND1TE": "Indite", "Indlte": "Indite", "lndlte": "Indite",
            "SILVER": "Silver", "SIIVER": "Silver", "SLLVER": "Silver"
        }

        lines = raw_text.split('\n')
        current_station_key = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

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
                loose_match = re.search(r'(.+?)\s+x\s+([\d,O]+)\s+Tons\s+-\s+(.+)', line)
                if loose_match:
                    candidate_commodity = loose_match.group(1).strip()
                    quantity_part = loose_match.group(2).strip()
                    carrier_part = loose_match.group(3).strip()

                    processed_commodity = candidate_commodity.upper().replace('0', 'O').replace('1', 'I').replace('|', 'I').replace('L', 'I')

                    if processed_commodity in commodity_map:
                        correct_commodity_name = commodity_map[processed_commodity]

                        carrier_match = re.search(r'(.+?)\s+\(([A-Za-z0-9-]{7})\)', carrier_part)
                        if carrier_match:
                            carrier_name_part = carrier_match.group(1).strip()
                            carrier_id = carrier_match.group(2).strip()

                            try:
                                quantity = int(quantity_part.replace(',', '').replace('O', '0'))
                                carrier_name = f"{carrier_name_part} {carrier_id}".upper()

                                carrier_data = {
                                    "carrier_name": carrier_name,
                                    "commodity": correct_commodity_name,
                                    "quantity": quantity
                                }
                                output["stations"][current_station_key].append(carrier_data)
                            except ValueError:
                                logger.warning(f"Could not parse quantity: {quantity_part}")

        return output
