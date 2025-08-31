from __future__ import annotations

import time
import cv2
import numpy as np
from paddleocr import PaddleOCR
import logging
from strsimpy import SorensenDice
from strsimpy.jaro_winkler import JaroWinkler

from EDlogger import logger

"""
File:OCR.py    

Description:
  Class for OCR processing using PaddleOCR. 

Author: Stumpii
"""


class OCR:
    def __init__(self, screen, language: str = 'en', use_gpu: bool = False):
        self.screen = screen
        self.paddleocr = PaddleOCR(use_angle_cls=False, lang=language, use_gpu=use_gpu, show_log=False, use_dilation=True,
                                   use_space_char=True)
        logging.getLogger('ppocr').setLevel(logging.ERROR)
        # Class for text similarity metrics
        self.jarowinkler = JaroWinkler()
        self.sorensendice = SorensenDice()

    def string_similarity(self, s1, s2) -> float:
        """ Performs a string similarity check and returns the result.
        @param s1: The first string to compare.
        @param s2: The second string to compare.
        @return: The similarity from 0.0 (no match) to 1.0 (identical).
        """
        #return self.jarowinkler.similarity(s1, s2)
        return self.sorensendice.similarity(s1, s2)

    def find_best_match_in_list(self, ocr_textlist: list[str], target_text: str, threshold: float = 0.6) -> str | None:
        """
        Finds the best fuzzy match for a target string in a list of OCR results.
        """
        best_match_score = 0
        best_match_text = None

        if not ocr_textlist:
            return None

        for ocr_text in ocr_textlist:
            # Pre-process strings
            s1 = ocr_text.upper().replace("O", "0").replace(" ", "").replace("L", "1")
            s2 = target_text.upper().replace("O", "0").replace(" ", "").replace("L", "1")
            
            score = self.string_similarity(s1, s2)
            if score > best_match_score:
                best_match_score = score
                best_match_text = ocr_text

        if best_match_score >= threshold:
            return best_match_text
        else:
            return None

    def find_fuzzy_pattern_in_text(self, text_body: str, patterns: list[str], threshold: float = 0.8) -> str | None:
        """
        Finds the best fuzzy matching pattern from a list that matches the start of a text body.
        """
        best_match_score = 0
        best_match_pattern = None

        if not text_body or not patterns:
            return None

        for pattern in patterns:
            # Get substring of text_body to compare against
            candidate_substring = text_body[:len(pattern)]
            
            # Pre-process for better comparison
            s1 = candidate_substring.upper().replace("O", "0").replace("L", "1")
            s2 = pattern.upper().replace("O", "0").replace("L", "1")

            score = self.string_similarity(s1, s2)
            
            if score > best_match_score:
                best_match_score = score
                best_match_pattern = pattern
        
        if best_match_score >= threshold:
            return best_match_pattern
        else:
            return None

    def image_ocr(self, image):
        """ Perform OCR with no filtering. Returns the full OCR data and a simplified list of strings.
        This routine is the slower than the simplified OCR.

        OCR Data is returned in the following format, or (None, None):
        [[[[[86.0, 8.0], [208.0, 8.0], [208.0, 34.0], [86.0, 34.0]], ('ROBIGO 1 A', 0.9815958738327026)]]]
        """
        ocr_data = self.paddleocr.ocr(image)

        # print(ocr_data)

        if ocr_data is None:
            return None, None
        else:
            ocr_textlist = []
            for res in ocr_data:
                if res is None:
                    return None, None
                for line in res:
                    ocr_textlist.append(line[1][0])

            #print(ocr_textlist)
            return ocr_data, ocr_textlist

    def image_simple_ocr(self, image) -> list[str] | None:
        """ Perform OCR with no filtering. Returns a simplified list of strings with no positional data.
        This routine is faster than the function that returns the full data. Generally good when you
        expect to only return one or two lines of text.

        OCR Data is returned in the following format, or None:
        [[[[[86.0, 8.0], [208.0, 8.0], [208.0, 34.0], [86.0, 34.0]], ('ROBIGO 1 A', 0.9815958738327026)]]]
        """
        ocr_data = self.paddleocr.ocr(image)

        # print(f"image_simple_ocr: {ocr_data}")

        if ocr_data is None:
            return None
        else:
            ocr_textlist = []
            for res in ocr_data:
                if res is None:
                    return None

                for line in res:
                    ocr_textlist.append(line[1][0])

            # print(f"image_simple_ocr: {ocr_textlist}")
            # logger.info(f"image_simple_ocr: {ocr_textlist}")
            return ocr_textlist

    def get_highlighted_item_data(self, image, min_w, min_h):
        """ Attempts to find a selected item in an image. The selected item is identified by being solid orange or blue
            rectangle with dark text, instead of orange/blue text on a dark background.
            The OCR daya of the first item matching the criteria is returned, otherwise None.
            @param image: The image to check.
            @param min_w: The minimum width of the text block.
            @param min_h: The minimum height of the text block.
        """
        # Find the selected item/menu (solid orange)
        img_selected, x, y = self.get_highlighted_item_in_image(image, min_w, min_h)
        if img_selected is not None:
            # cv2.imshow("img", img_selected)

            ocr_data, ocr_textlist = self.image_ocr(img_selected)

            if ocr_data is not None:
                return img_selected, ocr_data, ocr_textlist
            else:
                return None, None, None

        else:
            return None, None, None

    def get_highlighted_item_in_image(self, image, min_w, min_h):
        """ Attempts to find a selected item in an image. The selected item is identified by being solid orange or blue
        rectangle with dark text, instead of orange/blue text on a dark background.
        The image of the first item matching the criteria and minimum width and height is returned
        with x and y co-ordinates, otherwise None.
        @param image: The image to check.
        @param min_h: Minimum height in pixels.
        @param min_w: Minimum width in pixels.
        """
        # Perform HSV mask
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_range = np.array([0, 100, 180])
        upper_range = np.array([255, 255, 255])
        mask = cv2.inRange(hsv, lower_range, upper_range)
        masked_image = cv2.bitwise_and(image, image, mask=mask)
        cv2.imwrite('test/nav-panel/out/1-masked.png', masked_image)

        # Convert to gray scale and invert
        gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite('test/nav-panel/out/2-gray.png', gray)

        # Blur slightly to remove thin lines
        blur = cv2.GaussianBlur(gray, (3, 3), cv2.BORDER_DEFAULT)
        cv2.imwrite('test/nav-panel/out/3-blur.png', blur)

        # Convert to B&W to allow FindContours to find rectangles.
        ret, thresh1 = cv2.threshold(blur, 0, 255, cv2.THRESH_OTSU)  # | cv2.THRESH_BINARY_INV)
        cv2.imwrite('test/nav-panel/out/4-thresh1.png', thresh1)

        # Finding contours in B&W image. White are the areas detected
        contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        output = image
        cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
        cv2.imwrite('test/nav-panel/out/5-contours.png', output)

        # bounds = image
        cropped = image
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Check the item is greater than 90% of the minimum width or height. Which allows for some variation.
            if w > (min_w * 0.9) and h > (min_h * 0.9):
                # Drawing a rectangle on the copied image
                # bounds = cv2.rectangle(bounds, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Crop to leave only the contour (the selected rectangle)
                cropped = image[y:y + h, x:x + w]

                # cv2.imshow("cropped", cropped)
                cv2.imwrite('test/nav-panel/out/6-selected_item.png', cropped)
                return cropped, x, y

        # No good matches, then return None
        return None, 0, 0

    def capture_region_pct(self, region):
        """ Grab the image based on the region name/rect.
        Returns an unfiltered image, either from screenshot or provided image.
        @param region: The region to check in % (0.0 - 1.0).
        """
        rect = region['rect']
        image = self.screen.get_screen_rect_pct(rect)
        return image

    def is_text_in_selected_item_in_image(self, img, text, min_w, min_h):
        """ Does the selected item in the region include the text being checked for.
        Checks if text exists in a region using OCR.
        Return True if found, False if not and None if no item was selected.
        @param min_h: Minimum height in pixels.
        @param min_w: Minimum width in pixels.
        @param img: The image to check.
        @param text: The text to find.
        """
        img_selected, x, y = self.get_highlighted_item_in_image(img, min_w, min_h)
        if img_selected is None:
            logger.debug(f"Did not find a selected item in the region.")
            return None

        ocr_textlist = self.image_simple_ocr(img_selected)
        # print(str(ocr_textlist))

        if text.upper() in str(ocr_textlist).upper():
            logger.debug(f"Found '{text}' text in item text '{str(ocr_textlist)}'.")
            return True
        else:
            logger.debug(f"Did not find '{text}' text in item text '{str(ocr_textlist)}'.")
            return False

    def is_text_in_region(self, text, region) -> (bool, str):
        """ Does the region include the text being checked for. The region does not need
        to include highlighted areas.
        Checks if text exists in a region using OCR.
        Return True if found, False if not and None if no item was selected.
        @param text: The text to check for.
        @param region: The region to check in % (0.0 - 1.0).
        """

        img = self.capture_region_pct(region)

        ocr_textlist = self.image_simple_ocr(img)
        # print(str(ocr_textlist))

        if text.upper() in str(ocr_textlist).upper():
            logger.debug(f"Found '{text}' text in item text '{str(ocr_textlist)}'.")
            return True, str(ocr_textlist)
        else:
            logger.debug(f"Did not find '{text}' text in item text '{str(ocr_textlist)}'.")
            return False, str(ocr_textlist)

    def select_item_in_list(self, text, region, keys, min_w, min_h) -> bool:
        """ Attempt to find the item by text in a list defined by the region.
        If found, leaves it selected for further actions.
        @param keys:
        @param text: Text to find.
        @param region: The region to check in % (0.0 - 1.0).
        @param min_h: Minimum height in pixels.
        @param min_w: Minimum width in pixels.
        """

        in_list = False  # Have we seen one item yet? Prevents quiting if we have not selected the first item.
        while 1:
            img = self.capture_region_pct(region)
            if img is None:
                return False

            found = self.is_text_in_selected_item_in_image(img, text, min_w, min_h)

            # Check if end of list.
            if found is None and in_list:
                logger.debug(f"Did not find '{text}' in {region} list.")
                return False

            if found:
                logger.debug(f"Found '{text}' in {region} list.")
                return True
            else:
                # Next item
                in_list = True
                keys.send("UI_Down")

    def wait_for_text(self, ap, texts: list[str], region, timeout=30) -> bool:
        """ Wait for a screen to appear by checking for text to appear in the region.
        @param ap: ED_AP instance.
        @param texts: List of text to check for. Success occurs if any in the list is found.
        @param region: The region to check in % (0.0 - 1.0).
        @param timeout: Time to wait for screen in seconds
        """
        # Draw box around region
        abs_rect = self.screen.screen_rect_to_abs(region['rect'])
        if ap.debug_overlay:
            ap.overlay.overlay_rect1('wait_for_text', abs_rect, (0, 255, 0), 2)
            ap.overlay.overlay_paint()

        start_time = time.time()
        text_found = False
        while True:
            # Check for timeout.
            if time.time() > (start_time + timeout):
                break

            # Check if screen has appeared.
            for text in texts:
                text_found, ocr_text = self.is_text_in_region(text, region)

                # Over OCR result
                if ap.debug_overlay:
                    ap.overlay.overlay_floating_text('wait_for_text', f'{ocr_text}', abs_rect[0], abs_rect[1] - 25, (0, 255, 0))
                    ap.overlay.overlay_paint()

                if text_found:
                    break

            if text_found:
                break

            time.sleep(0.25)

        # Clean up screen
        if ap.debug_overlay:
            time.sleep(2)
            ap.overlay.overlay_remove_rect('wait_for_text')
            ap.overlay.overlay_remove_floating_text('wait_for_text')
            ap.overlay.overlay_paint()

        return text_found

    def wait_for_any_text(self, ap, region, timeout=60) -> bool:
        """ Wait for a screen to appear by checking for any text to appear in the region.
        @param ap: ED_AP instance.
        @param region: The region to check in % (0.0 - 1.0).
        @param timeout: Time to wait for screen in seconds
        """
        # Draw box around region
        abs_rect = self.screen.screen_rect_to_abs(region['rect'])
        if ap.debug_overlay:
            ap.overlay.overlay_rect1('wait_for_any_text', abs_rect, (0, 255, 0), 2)
            ap.overlay.overlay_paint()

        start_time = time.time()
        text_found = False
        while True:
            # Check for timeout.
            if time.time() > (start_time + timeout):
                break

            img = self.capture_region_pct(region)
            if img is None:
                time.sleep(0.25)
                continue
            
            ocr_textlist = self.image_simple_ocr(img)

            # Over OCR result
            if ap.debug_overlay:
                ap.overlay.overlay_floating_text('wait_for_any_text', f'{ocr_textlist}', abs_rect[0], abs_rect[1] - 25, (0, 255, 0))
                ap.overlay.overlay_paint()

            if ocr_textlist:
                text_found = True
                break

            time.sleep(0.25)

        # Clean up screen
        if ap.debug_overlay:
            time.sleep(2)
            ap.overlay.overlay_remove_rect('wait_for_any_text')
            ap.overlay.overlay_remove_floating_text('wait_for_any_text')
            ap.overlay.overlay_paint()

        return text_found

    def wait_for_highlighted_text(self, ap, text: str, region, min_w, min_h, timeout=60) -> bool:
        """ Wait for a screen to appear by checking for highlighted text to appear in the region.
        @param ap: ED_AP instance.
        @param text: The text to check for.
        @param region: The region to check in % (0.0 - 1.0).
        @param min_w: The minimum width of the text block.
        @param min_h: The minimum height of the text block.
        @param timeout: Time to wait for screen in seconds
        """
        # Draw box around region
        abs_rect = self.screen.screen_rect_to_abs(region['rect'])
        if ap.debug_overlay:
            ap.overlay.overlay_rect1('wait_for_highlighted_text', abs_rect, (0, 255, 0), 2)
            ap.overlay.overlay_paint()

        start_time = time.time()
        text_found = False
        while True:
            # Check for timeout.
            if time.time() > (start_time + timeout):
                break

            # Check if screen has appeared.
            img = self.capture_region_pct(region)
            if img is None:
                time.sleep(0.25)
                continue

            found = self.is_text_in_selected_item_in_image(img, text, min_w, min_h)

            # Over OCR result
            if ap.debug_overlay:
                # This is a bit tricky since is_text_in_selected_item_in_image doesn't return the ocr text
                # I will just display the target text
                ap.overlay.overlay_floating_text('wait_for_highlighted_text', f'Waiting for: {text}', abs_rect[0], abs_rect[1] - 25, (0, 255, 0))
                ap.overlay.overlay_paint()

            if found:
                text_found = True
                break

            time.sleep(0.25)

        # Clean up screen
        if ap.debug_overlay:
            time.sleep(2)
            ap.overlay.overlay_remove_rect('wait_for_highlighted_text')
            ap.overlay.overlay_remove_floating_text('wait_for_highlighted_text')
            ap.overlay.overlay_paint()

        return text_found
