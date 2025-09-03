from __future__ import annotations

import cv2
import json
import os
import re
import ED_AP
from MarketParser import MarketParser
from ocr_client import OCR
from StatusParser import StatusParser
from time import sleep, time
from EDlogger import logger
from Screen_Regions import reg_scale_for_station, size_scale_for_station

"""
File:StationServicesInShip.py    

Description:
  TBD 

Author: Stumpii
"""


class EDStationServicesInShip:
    """ Handles Station Services In Ship. """
    def __init__(self, ed_ap, screen, keys, cb):
        self.ap = ed_ap
        self.ocr = ed_ap.ocr
        self.locale = self.ap.locale
        self.screen = screen
        self.keys = keys
        self.ap_ckb = cb
        self.status_parser = StatusParser()
        self.market_parser = MarketParser()
        # The rect is top left x, y, and bottom right x, y in fraction of screen resolution
        self.reg = {'connected_to': {'rect': [0.0, 0.0, 0.30, 0.30]},
                    'carrier_admin_header': {'rect': [0.4, 0.1, 0.6, 0.2]},
                    'commodities_list': {'rect': [0.2, 0.2, 0.8, 0.9]},
                    'commodity_quantity': {'rect': [0.4, 0.5, 0.6, 0.6]},
                    'mission_board_header': {'rect': [0.4, 0.1, 0.6, 0.2]},
                    'missions_list': {'rect': [0.06, 0.25, 0.48, 0.8]},
                    'mission_depot_tab': {'rect': [0.6, 0.15, 0.8, 0.2]},
                    'mission_loaded': {'rect': [0.06, 0.25, 0.48, 0.35]},
                    }
        self.commodity_item_size = {"width": 100, "height": 15}
        self.mission_item_size = {"width": 100, "height": 15}

        self.load_calibrated_regions()

    def load_calibrated_regions(self):
        calibration_file = 'configs/ocr_calibration.json'
        if os.path.exists(calibration_file):
            with open(calibration_file, 'r') as f:
                calibrated_regions = json.load(f)

            for key, value in self.reg.items():
                calibrated_key = f"EDStationServicesInShip.{key}"
                if calibrated_key in calibrated_regions:
                    self.reg[key]['rect'] = calibrated_regions[calibrated_key]['rect']
            
            calibrated_size_key = "EDStationServicesInShip.size.commodity_item"
            if calibrated_size_key in calibrated_regions:
                self.commodity_item_size = calibrated_regions[calibrated_size_key]

            calibrated_size_key = "EDStationServicesInShip.size.mission_item"
            if calibrated_size_key in calibrated_regions:
                self.mission_item_size = calibrated_regions[calibrated_size_key]

    def goto_station_services(self) -> bool:
        """ Goto Station Services. """
        scl_reg = reg_scale_for_station(self.reg['connected_to'], self.screen.screen_width, self.screen.screen_height)

        # If not, go to cockpit view and navigate
        self.ap.ship_control.goto_cockpit_view()

        self.keys.send("UI_Up", repeat=3)  # go to very top (refuel line)
        self.keys.send("UI_Down")  # station services
        self.keys.send("UI_Select")  # station services

        # Wait for screen to appear
        if not self.ocr.wait_for_text(self.ap, [self.locale["STN_SVCS_CONNECTED_TO"]], scl_reg):
            logger.error("Failed to open station services.")
            return False

        return True

    def goto_construction_services(self) -> bool:
        """ Goto Construction Services. This is for an Orbital Construction Site. """
        # Go to cockpit view
        self.ap.ship_control.goto_cockpit_view()

        self.keys.send("UI_Up", repeat=3)  # go to very top (refuel line)
        self.keys.send("UI_Down")  # station services
        self.keys.send("UI_Select")  # station services

        # TODO - replace with OCR from OCR branch?
        sleep(3)  # wait for new menu to finish rendering

        return True

    def select_buy(self, keys) -> bool:
        """ Select Buy. Assumes on Commodities Market screen. """

        # Select Buy
        keys.send("UI_Left", repeat=2)
        keys.send("UI_Up", repeat=4)

        keys.send("UI_Select")  # Select Buy

        sleep(0.5)  # give time to bring up list
        keys.send('UI_Right')  # Go to top of commodities list
        return True

    def select_sell(self, keys) -> bool:
        """ Select Buy. Assumes on Commodities Market screen. """

        # Select Buy
        keys.send("UI_Left", repeat=2)
        keys.send("UI_Up", repeat=4)

        keys.send("UI_Down")
        keys.send("UI_Select")  # Select Sell

        sleep(0.5)  # give time to bring up list
        keys.send('UI_Right')  # Go to top of commodities list
        return True

    def _parse_quantity(self, ocr_text: list[str]) -> int:
        if not ocr_text:
            return 0
        try:
            s = "".join(ocr_text).replace(",", "").split('/')[0].strip()
            return int(s)
        except (ValueError, IndexError):
            # It could be that the OCR picked up something else.
            # Try to find a number in the string.
            import re
            numbers = re.findall(r'\d+', "".join(ocr_text).replace(",", ""))
            if numbers:
                return int(numbers[0])
        return 0

    def _parse_number_with_ocr_errors(self, s: str) -> int:
        s = s.upper().replace('O', '0').replace('I', '1').replace('L', '1').replace('S', '5').replace('B', '8')
        try:
            return int(s)
        except ValueError:
            return 0

    def _set_quantity_with_ocr(self, keys, act_qty: int, name: str, is_buy: bool, max_qty: bool) -> bool:
        """
        Sets the quantity of an item using OCR verification.
        Assumes the UI is on the buy/sell panel.
        """
        # Wait for the buy/sell panel to appear
        start_time = time()
        panel_found = False
        min_w, min_h = size_scale_for_station(self.commodity_item_size['width'], self.commodity_item_size['height'], self.screen.screen_width, self.screen.screen_height)
        while time() - start_time < 10:
            image = self.ocr.capture_region_pct(self.reg['commodities_list'])
            _, _, ocr_textlist = self.ocr.get_highlighted_item_data(image, min_w, min_h)
            if ocr_textlist:
                ocr_string = str(ocr_textlist).upper()
                if "BUY" in ocr_string or "SELL" in ocr_string or re.search(r'\d', ocr_string):
                    panel_found = True
                    break
            sleep(0.2)
            keys.send('UI_Up')  # go up to quantity, try again
        
        if not panel_found:
            self.ap_ckb('log+vce', f"Error: Timed out waiting for buy/sell panel to appear for {name}.")
            keys.send('UI_Back')
            return False

        keys.send('UI_Up', repeat=2)  # go up to quantity

        scl_reg_qty = reg_scale_for_station(self.reg['commodity_quantity'], self.screen.screen_width,
                                        self.screen.screen_height)
        
        abs_rect_qty = self.screen.screen_rect_to_abs(scl_reg_qty['rect'])
        if self.ap.debug_overlay:
            self.ap.overlay.overlay_rect1('commodity_quantity', abs_rect_qty, (0, 255, 0), 2)
            self.ap.overlay.overlay_paint()

        if max_qty:
            keys.send("UI_Right", hold=4)
        else:
            # Smart reset to 1
            keys.send('UI_Left', state=1) # Press and hold left
            try:
                start_time = time()
                qty_is_one = False
                while time() - start_time < 4: # 4 second timeout
                    img_qty = self.ocr.capture_region_pct(scl_reg_qty)
                    gray_image = cv2.cvtColor(img_qty, cv2.COLOR_BGR2GRAY)
                    _, processed_img = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV)
                    ocr_text = self.ocr.image_simple_ocr(processed_img)
                    current_qty = self._parse_quantity(ocr_text)
                    if current_qty == 0:
                        qty_is_zero = True
                        break
                    sleep(0.1)
                if not qty_is_zero:
                    logger.warning("Timed out waiting for quantity to reset to 0.")
            finally:
                keys.send('UI_Left', state=0) # Release left

            if act_qty > 0:
                keys.send('UI_Right', repeat=act_qty, fast=True)
        
        sleep(0.5)

        # Skip final verification if max_qty is True (user wants to sell maximum amount)
        if max_qty:
            if self.ap.debug_overlay:
                sleep(1)
                self.ap.overlay.overlay_remove_rect('commodity_quantity')
                self.ap.overlay.overlay_paint()
            return True

        # Final verification
        img_qty = self.ocr.capture_region_pct(scl_reg_qty)
        gray_image = cv2.cvtColor(img_qty, cv2.COLOR_BGR2GRAY)
        _, processed_img = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV)
        ocr_text = self.ocr.image_simple_ocr(processed_img)
        current_qty = self._parse_quantity(ocr_text)

        if self.ap.debug_overlay:
            self.ap.overlay.overlay_floating_text('commodity_quantity_text', f'Target: {act_qty}, OCR: {current_qty}', abs_rect_qty[0], abs_rect_qty[1] - 25, (0, 255, 0))
            self.ap.overlay.overlay_paint()

        if current_qty != act_qty:
            # Fallback to adjust loop
            for _ in range(10): # Try to adjust 10 times
                if current_qty == act_qty:
                    break
                
                diff = act_qty - current_qty
                if diff > 0:
                    keys.send('UI_Right', repeat=diff, fast=True)
                else:
                    keys.send('UI_Left', repeat=-diff, fast=True)
                sleep(0.5)

                img_qty = self.ocr.capture_region_pct(scl_reg_qty)
                gray_image = cv2.cvtColor(img_qty, cv2.COLOR_BGR2GRAY)
                _, processed_img = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV)
                ocr_text = self.ocr.image_simple_ocr(processed_img)
                current_qty = self._parse_quantity(ocr_text)

                if self.ap.debug_overlay:
                    self.ap.overlay.overlay_floating_text('commodity_quantity_text', f'Target: {act_qty}, OCR: {current_qty}', abs_rect_qty[0], abs_rect_qty[1] - 25, (0, 255, 0))
                    self.ap.overlay.overlay_paint()

        if self.ap.debug_overlay:
            sleep(1)
            self.ap.overlay.overlay_remove_rect('commodity_quantity')
            self.ap.overlay.overlay_remove_floating_text('commodity_quantity_text')
            self.ap.overlay.overlay_paint()

        if current_qty != act_qty:
            self.ap_ckb('log+vce', f"Could not set quantity to {act_qty} for '{name}'.")
            logger.error(f"Could not set quantity to {act_qty} for '{name}'. Current quantity: {current_qty}")
            keys.send('UI_Back')
            return False

        return True

    def _find_item_in_list(self, item_name, list_region, min_w, min_h, keys):
        """
        Finds an item in a list using the "intelligent scroll" method.
        """
        if self.ap.debug_overlay:
            abs_rect = self.screen.screen_rect_to_abs(list_region['rect'])
            self.ap.overlay.overlay_rect1('commodities_list_rect', abs_rect, (255, 0, 0), 2)
            self.ap.overlay.overlay_paint()

        # Go to top of list
        last_text = ""
        keys.send('UI_Up', state=1)
        for _ in range(40):  # Max 10 seconds
            sleep(0.5)
            image = self.ocr.capture_region_pct(list_region)
            _, _, ocr_textlist = self.ocr.get_highlighted_item_data(image, min_w, min_h)
            current_text = str(ocr_textlist)

            if last_text == current_text:
                break
            last_text = current_text
        keys.send('UI_Up', state=0)
        sleep(0.1)

        # Find item in the list
        item_found = False
        in_list = False
        for _ in range(100):  # Max 100 scrolls, to be safe
            image = self.ocr.capture_region_pct(list_region)
            img_selected, _, ocr_textlist = self.ocr.get_highlighted_item_data(image, min_w, min_h)

            if self.ap.debug_overlay:
                abs_rect = self.screen.screen_rect_to_abs(list_region['rect'])
                self.ap.overlay.overlay_floating_text('commodities_list_text', f'{ocr_textlist}', abs_rect[0],
                                                      abs_rect[1] - 25, (0, 255, 0))
                self.ap.overlay.overlay_paint()

            if ocr_textlist and self.ocr.find_best_match_in_list(ocr_textlist, item_name):
                item_found = True
                break

            if img_selected is None and in_list:
                # End of list
                break

            in_list = True
            keys.send('UI_Down')

        if self.ap.debug_overlay:
            sleep(1)
            self.ap.overlay.overlay_remove_rect('commodities_list_rect')
            self.ap.overlay.overlay_remove_floating_text('commodities_list_text')
            self.ap.overlay.overlay_paint()

        return item_found

    def _wait_for_market_list_ready(self, item_name: str, timeout=10) -> bool:
        """
        Waits for the market list to be ready by detecting a specific highlighted item.
        """
        start_time = time()
        scl_reg = reg_scale_for_station(self.reg['commodities_list'], self.screen.screen_width,
                                        self.screen.screen_height)
        min_w, min_h = size_scale_for_station(self.commodity_item_size['width'], self.commodity_item_size['height'], self.screen.screen_width, self.screen.screen_height)

        while time() - start_time < timeout:
            image = self.ocr.capture_region_pct(scl_reg)
            img_selected, _, ocr_textlist = self.ocr.get_highlighted_item_data(image, min_w, min_h)
            
            if img_selected is not None:
                if ocr_textlist and item_name.upper() in str(ocr_textlist).upper():
                    logger.debug(f"Market list is ready (item '{item_name}' is highlighted).")
                    return True
            
            sleep(0.2) # Poll every 200ms
        
        logger.warning(f"Timed out waiting for '{item_name}' to be highlighted after {timeout}s.")
        return False

    def buy_commodity(self, keys, name: str, qty: int, free_cargo: int) -> tuple[bool, int]:
        """ Buy qty of commodity. If qty >= 9999 then buy as much as possible.
        Assumed to be in the commodities buy screen in the list. """

        # If we are updating requirement count, me might have all the qty we need
        if qty <= 0:
            return False, 0

        # Determine if station sells the commodity!
        self.market_parser.get_market_data()
        if not self.market_parser.can_buy_item(name):
            self.ap_ckb('log+vce', f"'{name}' is not sold or has no stock at {self.market_parser.get_market_name()}.")
            logger.debug(f"Item '{name}' is not sold or has no stock at {self.market_parser.get_market_name()}.")
            return False, 0

        # Find commodity in mar
        # ket and return the index
        index = -1
        stock = 0
        buyable_items = self.market_parser.get_buyable_items()
        if buyable_items is not None:
            for i, value in enumerate(buyable_items):
                if value['Name_Localised'].upper() == name.upper():
                    index = i
                    stock = value['Stock']
                    logger.debug(f"Execute trade: Buy {name} (want {qty} of {stock} avail.) at position {index + 1}.")
                    break

        # Actual qty we can sell
        act_qty = min(qty, stock, free_cargo)

        # See if we buy all and if so, remove the item to update the list, as the item will be removed
        # from the commodities screen, but the market.json will not be updated.
        buy_all = act_qty == stock
        if buy_all:
            for i, value in enumerate(self.market_parser.current_data['Items']):
                if value['Name_Localised'].upper() == name.upper():
                    # Set the stock bracket to 0, so it does not get included in available commodities list.
                    self.market_parser.current_data['Items'][i]['StockBracket'] = 0

        if buyable_items is None:
            return False, 0

        # Find item in list with OCR
        scl_reg = reg_scale_for_station(self.reg['commodities_list'], self.screen.screen_width,
                                        self.screen.screen_height)
        min_w, min_h = size_scale_for_station(self.commodity_item_size['width'], self.commodity_item_size['height'], self.screen.screen_width, self.screen.screen_height)
        found_on_screen = self._find_item_in_list(name, scl_reg, min_w, min_h, keys)

        if not found_on_screen:
            self.ap_ckb('log+vce', f"Could not find '{name}' on screen in the market.")
            logger.error(f"Could not find '{name}' on screen in the market.")
            return False, 0

        keys.send('UI_Select')  # Select that commodity

        max_qty = qty >= 9999 or qty >= stock or qty >= free_cargo
        if not self._set_quantity_with_ocr(keys, act_qty, name, True, max_qty):
            return False, 0

        self.ap_ckb('log+vce', f"Buying {act_qty} units of {name}.")
        logger.info(f"Buying {act_qty} units of {name}")
        keys.send('UI_Down')
        keys.send('UI_Select')  # Select Buy
        sleep(0.5)
        # keys.send('UI_Back')  # Back to commodities list

        return True, act_qty

    def sell_commodity(self, keys, name: str, qty: int, cargo_parser, sell_one_at_a_time: bool = False) -> tuple[bool, int]:
        """ Sell qty of commodity. If qty >= 9999 then sell as much as possible.
        Assumed to be in the commodities sell screen in the list.
        @param keys: Keys class for sending keystrokes.
        @param name: Name of the commodity.
        @param qty: Quantity to sell.
        @param cargo_parser: Current cargo to check if rare or demand=1 items exist in hold.
        @param sell_one_at_a_time: If True, sell items one at a time.
        @return: Sale successful (T/F) and Qty.
        """

        # If we are updating requirement count, me might have sold all we have
        if qty <= 0:
            return False, 0

        # Determine if station buys the commodity!
        self.market_parser.get_market_data()
        if not self.market_parser.can_sell_item(name):
            self.ap_ckb('log+vce', f"'{name}' is not bought at {self.market_parser.get_market_name()}.")
            logger.debug(f"Item '{name}' is not bought at {self.market_parser.get_market_name()}.")
            return False, 0

        # Find commodity in market and return the index
        demand = 0
        sellable_items = self.market_parser.get_sellable_items(cargo_parser)
        if sellable_items is not None:
            for i, value in enumerate(sellable_items):
                if value['Name_Localised'].upper() == name.upper():
                    demand = value['Demand']
                    logger.debug(f"Execute trade: Sell {name} ({qty} of {demand} demanded).")
                    break
        else:
            return False, 0

        # Qty we can sell. Unlike buying, we can sell more than the demand
        # But maybe not at all stations!
        act_qty = qty

        # Find item in list with OCR
        scl_reg = reg_scale_for_station(self.reg['commodities_list'], self.screen.screen_width,
                                        self.screen.screen_height)
        min_w, min_h = size_scale_for_station(self.commodity_item_size['width'], self.commodity_item_size['height'], self.screen.screen_width, self.screen.screen_height)
        found_on_screen = self._find_item_in_list(name, scl_reg, min_w, min_h, keys)

        if not found_on_screen:
            self.ap_ckb('log+vce', f"Could not find '{name}' on screen in the market.")
            logger.error(f"Could not find '{name}' on screen in the market.")
            return False, 0
        
        if sell_one_at_a_time:
            total_sold = 0
            for i in range(act_qty):
                keys.send('UI_Select')  # Select that commodity (it's already highlighted)

                self.ap_ckb('log+vce', f"Selling 1 unit of {name} ({i + 1}/{act_qty}).")
                if not self._set_quantity_with_ocr(keys, 1, name, False, False):
                    # On failure, _set_quantity_with_ocr will have sent UI_Back,
                    # so we should be on the market list screen.
                    return False, total_sold

                keys.send('UI_Down')
                keys.send('UI_Select')  # Select Sell
                
                if not self._wait_for_market_list_ready(name):
                    self.ap_ckb('log+vce', f"Error: Timed out waiting for '{name}' to be highlighted after selling a unit.")
                    return False, total_sold

                total_sold += 1
            return True, total_sold
        else:
            keys.send('UI_Select')  # Select that commodity
            max_qty = qty >= 9999
            if not self._set_quantity_with_ocr(keys, act_qty, name, False, max_qty):
                return False, 0

            keys.send('UI_Down')  # Down to the Sell button (already assume sell all)
            keys.send('UI_Select')  # Select to Sell all
            sleep(0.5)
            # keys.send('UI_Back')  # Back to commodities list

            return True, act_qty

    def buy_commodity_for_mission(self, mission) -> tuple[bool, int]:
        """
        Buys a commodity required for a given mission.
        Returns a tuple of (success, quantity_purchased).
        """
        commodity_name = mission['commodity']
        tonnage = mission['tonnage']
        free_cargo = self.ap.get_cargo_info()['free']

        self.ap_ckb('log+vce', f"Attempting to buy {tonnage} of {commodity_name} for mission.")
        logger.info(f"Attempting to buy {tonnage} of {commodity_name} for mission.")

        # Navigate to commodity market
        if not self.goto_station_services():
            return False, 0
            
        self.keys.send("UI_Right", repeat=2)
        self.keys.send("UI_Select")
        sleep(5) # Wait for screen to load

        # Determine actual quantity we can buy from market data
        self.market_parser.get_market_data()
        if not self.market_parser.can_buy_item(commodity_name):
            self.ap_ckb('log+vce', f"'{commodity_name}' is not sold or has no stock at this market.")
            logger.warning(f"'{commodity_name}' is not sold or has no stock at this market.")
            return False, 0

        stock = 0
        buyable_items = self.market_parser.get_buyable_items()
        if buyable_items:
            for item in buyable_items:
                if item['Name_Localised'].upper() == commodity_name.upper():
                    stock = item['Stock']
                    break
        
        if stock == 0:
            self.ap_ckb('log+vce', f"Market has zero stock of {commodity_name}.")
            logger.warning(f"Market has zero stock of {commodity_name}.")
            return False, 0

        qty_to_buy = min(tonnage, stock, free_cargo)
        if qty_to_buy <= 0:
            self.ap_ckb('log+vce', f"Cannot buy {commodity_name}, need {tonnage}, have {free_cargo} free space, stock is {stock}.")
            logger.warning(f"Cannot buy {commodity_name}, need {tonnage}, have {free_cargo} free space, stock is {stock}.")
            return False, 0

        logger.info(f"Calculated quantity to buy: {qty_to_buy} of {commodity_name}.")

        if not self.select_buy(self.keys):
            self.ap_ckb('log+vce', "Failed to select buy tab in commodities market.")
            # Back out to main menu
            self.keys.send("UI_Back", repeat=4)
            sleep(1)
            return False, 0

        success, purchased_qty = self.buy_commodity(self.keys, commodity_name, qty_to_buy, free_cargo)

        # Back to the main station services menu
        self.keys.send("UI_Back", repeat=4)
        sleep(1)

        return success, purchased_qty

    def goto_fleet_carrier_management(self):
        """ Navigates to the Fleet Carrier Management screen from station services. """
        self.ap_ckb('log+vce', "Navigating to Fleet Carrier Management.")
        logger.debug("goto_fleet_carrier_management: entered")

        if not self.goto_station_services():
            logger.error("Could not open station services.")
            return False

        sleep(0.2)
        self.keys.send('UI_Down') # To redemption office
        sleep(0.2)
        self.keys.send('UI_Down') # To tritium depot
        sleep(0.2)
        self.keys.send('UI_Right') # To tritium depot
        sleep(0.2)
        self.keys.send('UI_Right') # To tritium depot
        sleep(0.2)
        self.keys.send('UI_Select') # To tritium depot
        sleep(1) # Wait for screen to load


        # Scale the regions based on the target resolution.
        scl_fleet = reg_scale_for_station(self.reg['carrier_admin_header'], self.screen.screen_width, self.screen.screen_height)

        # Wait for screen to appear
        res = self.ocr.wait_for_text(self.ap, [self.locale["STN_SVCS_FC_ADMIN_HEADER"]], scl_fleet)

        # Store image
        # image = self.screen.get_screen_rect_pct(scl_reg['rect'])
        # cv2.imwrite(f'test/carrier-management/carrier-management.png', image)

        # After the OCR timeout, carrier management will have appeared, to return true anyway.
        self.ap_ckb('log+vce', "Sucessfully entered Fleet Carrier Management.")
        logger.debug("goto_fleet_carrier_management: sucess")
        return True


    def goto_mission_board(self):
        """ Navigates to the Mission Board screen from station services. """
        self.ap_ckb('log+vce', "Navigating to Mission Board.")
        logger.debug("goto_mission_board: entered")

        if not self.goto_station_services():
            logger.error("Could not open station services.")
            return False

        sleep(1) # Give it a second to load station services

        # Navigate to the mission board in the station services menu
        # This is a bit of a guess, might need calibration
        self.keys.send('UI_Select')
        sleep(0.2)
        self.keys.send('UI_Select')
        sleep(2) # Wait for screen to load

        # Scale the regions based on the target resolution.
        scl_mission_board = reg_scale_for_station(self.reg['mission_board_header'], self.screen.screen_width, self.screen.screen_height)

        # Wait for screen to appear
        if not self.ocr.wait_for_text(self.ap, [self.locale["STN_SVCS_MISSION_BOARD_HEADER"]], scl_mission_board):
            logger.error("Could not verify that we are on the mission board.")
            self.ap.keys.send("UI_Back", repeat=4)
            return False

        # Wait for the "ALL" tab to be highlighted
        scl_reg_list = reg_scale_for_station(self.reg['missions_list'], self.screen.screen_width, self.screen.screen_height)
        min_w, min_h = size_scale_for_station(self.mission_item_size['width'], self.mission_item_size['height'], self.screen.screen_width, self.screen.screen_height)
        if not self.ocr.wait_for_highlighted_text(self.ap, "ALL", scl_reg_list, min_w, min_h):
            logger.error("Could not verify that the 'ALL' tab is selected on the mission board.")
            self.ap.keys.send("UI_Back", repeat=4)
            return False



        self.ap_ckb('log+vce', "Successfully entered Mission Board.")
        logger.debug("goto_mission_board: success")
        sleep(0.5)
        return True


    def scan_missions(self, keys):
        """
        Scans the mission board for specific mining missions and accepts them if they meet the criteria.
        """
        sleep(0.2)
        self.keys.send('UI_Right')
        sleep(0.2)
        self.keys.send('UI_Right')
        sleep(0.2)
        self.keys.send('UI_Select')
        sleep(5) # Reduced from 10
        self.ap_ckb('log+vce', "Scanning mission board.")
        logger.debug("scan_missions: entered")

        mission_name_patterns = [
            "Mine",
            "Mining rush for",
            "Blast out",
        ]

        exclusion_patterns = [
            "Bring us..",
            "We need...",
            "Industry Needs..",
            "Source and return..",
        ]

        commodities = {
            "Gold": (150, 600),
            "Silver": (300, 705),
            "Bertrandite": (600, 1000),
            "Indite": (650, 1200),
        }

        min_reward = 40000000

        scl_reg_list = reg_scale_for_station(self.reg['missions_list'], self.screen.screen_width, self.screen.screen_height)
        min_w, min_h = size_scale_for_station(self.mission_item_size['width'], self.mission_item_size['height'], self.screen.screen_width, self.screen.screen_height)

        if self.ap.debug_overlay:
            abs_rect = self.screen.screen_rect_to_abs(scl_reg_list['rect'])
            self.ap.overlay.overlay_rect1('missions_list_rect', abs_rect, (255, 0, 0), 2)
            self.ap.overlay.overlay_paint()

        # Go to top of list
        last_text = ""
        sleep(1)
        keys.send('UI_Down')
        sleep(0.5)

        consecutive_failures = 0
        in_list = False
        for _ in range(100):  # Max 100 scrolls
            image = self.ocr.capture_region_pct(scl_reg_list)
            img_selected, _, ocr_textlist = self.ocr.get_highlighted_item_data(image, min_w, min_h)

            if self.ap.debug_overlay:
                abs_rect = self.screen.screen_rect_to_abs(scl_reg_list['rect'])
                self.ap.overlay.overlay_floating_text('missions_list_text', f'{ocr_textlist}', abs_rect[0],
                                                      abs_rect[1] - 25, (0, 255, 0))
                self.ap.overlay.overlay_paint()

            if img_selected is None:
                if in_list:
                    consecutive_failures += 1
                    if consecutive_failures >= 2:
                        logger.info("End of mission list (2 consecutive OCR failures).")
                        break
            else:
                consecutive_failures = 0

            in_list = True

            if not ocr_textlist:
                keys.send('UI_Down')
                sleep(0.2)
                continue

            details_text = " ".join(ocr_textlist)
            logger.info(f"Scanning mission: {details_text}")

            # Check for exclusion patterns
            if self.ocr.find_fuzzy_pattern_in_text(details_text, exclusion_patterns):
                keys.send('UI_Down')
                continue

            # Check for mission name patterns
            matched_prefix = self.ocr.find_fuzzy_pattern_in_text(details_text, mission_name_patterns)
            if matched_prefix:
                try:
                    # Extract tonnage and commodity from the text
                    # This logic assumes "units of" is a reliable separator
                    if "units of" in details_text.lower():
                        parts = details_text.lower().split("units of")
                        tonnage_str = parts[0].strip().split()[-1]
                        tonnage = self._parse_number_with_ocr_errors(tonnage_str)
                        
                        commodity_candidate = parts[1].strip().split()[0]
                        
                        # Fuzzy match commodity
                        matched_commodity = self.ocr.find_best_match_in_list(list(commodities.keys()), commodity_candidate, threshold=0.7)

                        if matched_commodity:
                            min_ton, max_ton = commodities[matched_commodity]
                            if min_ton <= tonnage <= max_ton:
                                # Check reward
                                reward_matches = re.findall(r"([\d,]+) CR", details_text, re.IGNORECASE)
                                if reward_matches:
                                    possible_rewards = [int(r.replace(",", "")) for r in reward_matches]
                                    reward = max(possible_rewards)
                                    if reward >= min_reward:
                                        self.ap_ckb('log+vce', f"Found matching mission: {details_text}")
                                        logger.info(f"Mission matched, accepting: {details_text}")
                                        keys.send('UI_Select') # Select mission
                                        sleep(1)
                                        keys.send('UI_Select') # Accept mission
                                        sleep(5)
                                        self.keys.send('UI_Up') # Move up one to make sure we scan the next mission proper.
                                        sleep(0.5)
                except (IndexError, ValueError):
                    pass # Could not parse, move to next
            keys.send('UI_Down')


        if self.ap.debug_overlay:
            self.ap.overlay.overlay_remove_rect('missions_list_rect')
            self.ap.overlay.overlay_remove_floating_text('missions_list_text')
            self.ap.overlay.overlay_paint()

        self.ap_ckb('log+vce', "Finished scanning mission board.")
        return True

    def _scan_list_for_wing_missions(self):
        """
        Scans the current mission list for wing mining missions.
        NOTE: This function does not check for duplicates. It scans what's on screen.
        """
        mission_name_patterns = [
            "Mine",
            "Mining rush for",
            "Blast out",
        ]

        exclusion_patterns = [
            "Bring us..",
            "We need...",
            "Industry Needs..",
            "Source and return..",
        ]

        commodities = {
            "Gold": (150, 600),
            "Silver": (300, 705),
            "Bertrandite": (600, 1000),
            "Indite": (650, 1200),
        }

        min_reward = 40000000

        accepted_missions = []

        scl_reg_list = reg_scale_for_station(self.reg['missions_list'], self.screen.screen_width, self.screen.screen_height)
        min_w, min_h = size_scale_for_station(self.mission_item_size['width'], self.mission_item_size['height'], self.screen.screen_width, self.screen.screen_height)

        if self.ap.debug_overlay:
            abs_rect = self.screen.screen_rect_to_abs(scl_reg_list['rect'])
            self.ap.overlay.overlay_rect1('missions_list_rect', abs_rect, (255, 0, 0), 2)
            self.ap.overlay.overlay_paint()

        # Go to top of list
        last_text = ""
        sleep(1)
        self.keys.send('UI_Down')
        sleep(0.5)

        consecutive_failures = 0
        in_list = False
        for _ in range(100):  # Max 100 scrolls
            image = self.ocr.capture_region_pct(scl_reg_list)
            img_selected, _, ocr_textlist = self.ocr.get_highlighted_item_data(image, min_w, min_h)

            if self.ap.debug_overlay:
                abs_rect = self.screen.screen_rect_to_abs(scl_reg_list['rect'])
                self.ap.overlay.overlay_floating_text('missions_list_text', f'{ocr_textlist}', abs_rect[0],
                                                      abs_rect[1] - 25, (0, 255, 0))
                self.ap.overlay.overlay_paint()

            if img_selected is None:
                if in_list:
                    consecutive_failures += 1
                    if consecutive_failures >= 2:
                        logger.info("End of mission list (2 consecutive OCR failures).")
                        break
            else:
                consecutive_failures = 0

            in_list = True

            if not ocr_textlist:
                self.keys.send('UI_Down')
                sleep(0.2)
                continue

            details_text = " ".join(ocr_textlist)
            logger.info(f"Scanning mission: {details_text}")

            # Check for exclusion patterns
            if self.ocr.find_fuzzy_pattern_in_text(details_text, exclusion_patterns):
                self.keys.send('UI_Down')
                continue

            # Check for mission name patterns
            matched_prefix = self.ocr.find_fuzzy_pattern_in_text(details_text, mission_name_patterns)
            if matched_prefix:
                try:
                    # Extract tonnage and commodity from the text
                    if "units of" in details_text.lower():
                        parts = details_text.lower().split("units of")
                        tonnage_str = parts[0].strip().split()[-1]
                        tonnage = self._parse_number_with_ocr_errors(tonnage_str)

                        commodity_candidate = parts[1].strip().split()[0]

                        # Fuzzy match commodity
                        matched_commodity = self.ocr.find_best_match_in_list(list(commodities.keys()),
                                                                            commodity_candidate, threshold=0.7)

                        if matched_commodity:
                            min_ton, max_ton = commodities[matched_commodity]
                            if min_ton <= tonnage <= max_ton:
                                # Check reward
                                reward_matches = re.findall(r"([\d,]+) CR", details_text, re.IGNORECASE)
                                if reward_matches:
                                    possible_rewards = [int(r.replace(",", "")) for r in reward_matches]
                                    reward = max(possible_rewards)
                                    if reward >= min_reward:
                                        self.ap_ckb('log+vce', f"Found matching mission: {details_text}")
                                        logger.info(f"Mission matched, accepting: {details_text}")
                                        self.keys.send('UI_Select')  # Select mission
                                        sleep(1)
                                        self.keys.send('UI_Select')  # Accept mission
                                        mission_accepted_event = self.ap.jn.wait_for_event('MissionAccepted')
                                        if mission_accepted_event:
                                            mission_id = mission_accepted_event.get('MissionID')
                                            ocr_text = details_text
                                            accepted_missions.append({"commodity": matched_commodity, "tonnage": tonnage,
                                                                    "reward": reward, "mission_id": mission_id,
                                                                    "ocr_text": ocr_text})
                                        else:
                                            logger.warning("Did not find MissionAccepted event in journal")
                                        sleep(5)
                                        self.keys.send('UI_Up')  # Move up one to make sure we scan the next mission proper.
                                        sleep(0.5)
                except (IndexError, ValueError):
                    pass  # Couldn't parse mission details, try next one
            self.keys.send('UI_Down')


        if self.ap.debug_overlay:
            self.ap.overlay.overlay_remove_rect('missions_list_rect')
            self.ap.overlay.overlay_remove_floating_text('missions_list_text')
            self.ap.overlay.overlay_paint()

        return accepted_missions

    def scan_wing_missions(self):
        """
        Scans the mission board for specific mining missions and accepts them if they meet the criteria.
        This function now scans both TRANSPORT and ALL tabs.
        """
        self.ap_ckb('log+vce', "Scanning mission board for wing missions (TRANSPORT and ALL tabs).")
        logger.debug("scan_wing_missions: entered")

        all_accepted_missions = []

        # --- Scan TRANSPORT tab ---
        self.ap_ckb('log+vce', "Scanning TRANSPORT tab.")
        logger.info("Scanning TRANSPORT tab for wing missions.")
        sleep(0.2)
        self.keys.send('UI_Right')
        sleep(0.2)
        self.keys.send('UI_Right')
        sleep(0.2)
        self.keys.send('UI_Select')
        sleep(2)
        
        scl_reg_loaded = reg_scale_for_station(self.reg['mission_loaded'], self.screen.screen_width, self.screen.screen_height)
        if not self.ocr.wait_for_any_text(self.ap, scl_reg_loaded):
            logger.error("Timed out waiting for TRANSPORT mission list to load.")
        else:
            transport_missions = self._scan_list_for_wing_missions()
            if transport_missions:
                all_accepted_missions.extend(transport_missions)
                logger.info(f"Found {len(transport_missions)} missions in TRANSPORT tab.")

        # --- Scan ALL tab ---
        self.ap_ckb('log+vce', "Scanning ALL tab.")
        logger.info("Scanning ALL tab for wing missions.")
        self.keys.send('UI_Back')
        sleep(1)
        self.keys.send('UI_Select') # As per user, this should select the "ALL" tab
        sleep(2)
        
        if not self.ocr.wait_for_any_text(self.ap, scl_reg_loaded):
            logger.error("Timed out waiting for ALL mission list to load.")
        else:
            all_tab_missions = self._scan_list_for_wing_missions()
            if all_tab_missions:
                all_accepted_missions.extend(all_tab_missions)
                logger.info(f"Found {len(all_tab_missions)} missions in ALL tab.")


        self.ap_ckb('log+vce', f"Finished scanning mission board. Found {len(all_accepted_missions)} new missions in total.")
        return all_accepted_missions

    def check_mission_depot_for_wing_missions(self):
        """
        Checks the mission depot for unfulfilled wing mining missions.
        """
        # Navigate to the mission depot tab
        self.keys.send("UI_Right", repeat=4)
        sleep(1)
        self.keys.send("UI_Down")
        sleep(1)
        self.keys.send("UI_Select")
        sleep(2)
        
        scl_reg_loaded = reg_scale_for_station(self.reg['mission_loaded'], self.screen.screen_width, self.screen.screen_height)
        if not self.ocr.wait_for_any_text(self.ap, scl_reg_loaded):
            logger.error("Timed out waiting for mission depot list to load.")
            return []

        self.ap_ckb('log+vce', "Scanning mission depot.")
        logger.debug("check_mission_depot_for_wing_missions: entered")

        mission_name_patterns = [
            "Mine",
            "Mining rush for",
            "Blast out",
        ]

        commodities = {
            "Gold": (150, 600),
            "Silver": (300, 705),
            "Bertrandite": (600, 1000),
            "Indite": (650, 1200),
        }

        pending_missions = []

        scl_reg_list = reg_scale_for_station(self.reg['missions_list'], self.screen.screen_width, self.screen.screen_height)
        min_w, min_h = size_scale_for_station(self.mission_item_size['width'], self.mission_item_size['height'], self.screen.screen_width, self.screen.screen_height)

        # Go to top of list
        sleep(1)
        self.keys.send('UI_Down')
        sleep(0.5)

        consecutive_failures = 0
        in_list = True
        for _ in range(100):  # Max 100 scrolls
            image = self.ocr.capture_region_pct(scl_reg_list)
            img_selected, _, ocr_textlist = self.ocr.get_highlighted_item_data(image, min_w, min_h)

            if img_selected is None:
                if in_list:
                    consecutive_failures += 1
                    if consecutive_failures >= 2:
                        logger.info("End of mission list (2 consecutive OCR failures).")
                        break
            else:
                consecutive_failures = 0

            in_list = True

            if not ocr_textlist:
                self.keys.send('UI_Down')
                sleep(0.2)
                continue

            details_text = " ".join(ocr_textlist)
            logger.info(f"Scanning depot mission: {details_text}")

            # Check if it's a completed mission
            if "COMPLETED" in details_text.upper():
                self.keys.send('UI_Down')
                continue

            # Check for mission name patterns
            matched_prefix = self.ocr.find_fuzzy_pattern_in_text(details_text, mission_name_patterns)
            if matched_prefix:
                try:
                    # Extract tonnage and commodity from the text
                    if "units of" in details_text.lower():
                        parts = details_text.lower().split("units of")
                        tonnage_str = parts[0].strip().split()[-1]
                        tonnage = self._parse_number_with_ocr_errors(tonnage_str)

                        commodity_candidate = parts[1].strip().split()[0]

                        # Fuzzy match commodity
                        matched_commodity = self.ocr.find_best_match_in_list(list(commodities.keys()),
                                                                             commodity_candidate, threshold=0.7)

                        if matched_commodity:
                            min_ton, max_ton = commodities[matched_commodity]
                            if min_ton <= tonnage <= max_ton:
                                # This is a pending wing mining mission
                                # We need to find the mission ID from the journal
                                # This is tricky because we don't have the accept event here.
                                # For now, let's just add it to the queue without the ID.
                                # The turn-in logic will have to find it by OCR text.
                                logger.info(f"Found pending wing mining mission in depot: {details_text}")
                                pending_missions.append({"commodity": matched_commodity, "tonnage": tonnage,
                                                         "reward": 0, "mission_id": None, "ocr_text": details_text})
                except (IndexError, ValueError):
                    pass  # Couldn't parse mission details, try next one
            self.keys.send('UI_Down')

        self.ap_ckb('log+vce', "Finished scanning mission depot.")
        return pending_missions

def dummy_cb(msg, body=None):
    pass


# Usage Example
if __name__ == "__main__":
    test_ed_ap = ED_AP.EDAutopilot(cb=dummy_cb)
    test_ed_ap.keys.activate_window = True
    svcs = EDStationServicesInShip(test_ed_ap, test_ed_ap.scr, test_ed_ap.keys, test_ed_ap.ap_ckb)
    svcs.goto_station_services()
