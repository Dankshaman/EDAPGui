from time import sleep
import time
import traceback
import re
import cv2
import os
from EDlogger import logger
import difflib
import StateManager as sm
from Screen_Regions import reg_scale_for_station
import json

# States for the Wing Mining state machine
STATE_IDLE = "IDLE"
STATE_TRAVEL_TO_STATION = "TRAVEL_TO_STATION"
STATE_SCAN_FOR_MISSIONS = "SCAN_FOR_MISSIONS"
STATE_PROCESS_QUEUE = "PROCESS_QUEUE"
STATE_RESCAN_STATION = "RESCAN_STATION"
STATE_SWITCH_STATION = "SWITCH_STATION"
STATE_TRAVEL_TO_FC = "TRAVEL_TO_FC"
STATE_BUY_COMMODITY = "BUY_COMMODITY"
STATE_TRAVEL_TO_TURN_IN = "TRAVEL_TO_TURN_IN"
STATE_TURN_IN_MISSION = "TURN_IN_MISSION"
STATE_WAIT_AND_RECHECK = "WAIT_AND_RECHECK"
STATE_DONE = "DONE"


class WingMining:
    def __init__(self, ed_ap):
        self.ap = ed_ap
        self.state = STATE_IDLE
        self.mission_queue = []
        self.current_mission = None
        self.current_station_idx = 0  # 0 for A, 1 for B
        self.mission_turned_in = False
        self.failed_carriers = []
        self.current_carrier_name = None
        self._load_state()

    def _get_state(self):
        return {
            "state": self.state,
            "mission_queue": self.mission_queue,
            "current_mission": self.current_mission,
            "current_station_idx": self.current_station_idx,
            "mission_turned_in": self.mission_turned_in,
        }

    def _load_state(self):
        state = sm.load_state()
        if state:
            self.state = state.get("state", STATE_IDLE)
            self.mission_queue = state.get("mission_queue", [])
            self.current_mission = state.get("current_mission", None)
            self.current_station_idx = state.get("current_station_idx", 0)
            self.mission_turned_in = state.get("mission_turned_in", False)
            logger.info("Wing Mining state restored.")

    def start(self):
        logger.info("Starting Wing Mining sequence.")
        self.mission_queue = []
        self.current_mission = None
        self.current_station_idx = 0
        self._update_config_values()
        self.mission_turned_in = False

        if self.ap.config.get('WingMining_CompletedMissions', 0) >= 20:
            self.set_state(STATE_DONE)
            return

        if not self.station_a or not self.station_b:
            logger.error("Wing Mining stations are not configured.")
            self.set_state(STATE_IDLE)
            return

        # Smarter start logic
        ship_state = self.ap.jn.ship_state()
        if ship_state['status'] == 'in_station':
            current_station = ship_state['cur_station']
            _, station_a_name = self.station_a.split('/')
            _, station_b_name = self.station_b.split('/')
            
            if current_station.upper() == station_a_name.upper():
                logger.info(f"Starting at Station A: {self.station_a}")
                self.current_station_idx = 0
                self.set_state(STATE_SCAN_FOR_MISSIONS)
                return
            elif current_station.upper() == station_b_name.upper():
                logger.info(f"Starting at Station B: {self.station_b}")
                self.current_station_idx = 1
                self.set_state(STATE_SCAN_FOR_MISSIONS)
                return

        logger.info("Not starting at a configured wing mining station. Traveling to Station A.")
        self.set_state(STATE_TRAVEL_TO_STATION)

    def stop(self):
        logger.info("Stopping Wing Mining sequence.")
        self.set_state(STATE_IDLE)
        sm.clear_state()

    def reset_mission_counter(self):
        logger.info("Resetting Wing Mining mission counter.")
        self.completed_missions = 0
        self.ap.config['WingMining_CompletedMissions'] = 0
        self.ap.update_config()
        self.ap.ap_ckb('update_wing_mining_mission_count', 0)
        self.stop() # Stop the sequence if it's running
        sm.clear_state()

    def run(self):
        if self.state == STATE_IDLE or self.state == STATE_DONE:
            return

        sm.save_state(self._get_state())
        self._update_config_values()
        if self.completed_missions >= 20:
            self.set_state(STATE_DONE)
            self.ap.update_ap_status("Wing Mining complete: 20 missions done.")
            self.stop()
            return

        # State machine logic
        if self.state == STATE_TRAVEL_TO_STATION:
            self._handle_travel_to_station()
        elif self.state == STATE_SCAN_FOR_MISSIONS:
            self._handle_scan_for_missions()
        elif self.state == STATE_PROCESS_QUEUE:
            self._handle_process_queue()
        elif self.state == STATE_RESCAN_STATION:
            self._handle_rescan_station()
        elif self.state == STATE_SWITCH_STATION:
            self._handle_switch_station()
        elif self.state == STATE_TRAVEL_TO_FC:
            self._handle_travel_to_fc()
        elif self.state == STATE_BUY_COMMODITY:
            self._handle_buy_commodity()
        elif self.state == STATE_TRAVEL_TO_TURN_IN:
            self._handle_travel_to_turn_in()
        elif self.state == STATE_TURN_IN_MISSION:
            self._handle_turn_in_mission()
        elif self.state == STATE_WAIT_AND_RECHECK:
            self._handle_wait_and_recheck()

    def set_state(self, new_state):
        if self.state != new_state:
            logger.info(f"Wing Mining state changing from {self.state} to {new_state}")
            self.state = new_state
            self.ap.update_ap_status(f"Wing Mining: {self.state}")

    def _update_config_values(self):
        self.completed_missions = self.ap.config.get('WingMining_CompletedMissions', 0)
        self.station_a = self.ap.config.get('WingMining_StationA', '')
        self.station_b = self.ap.config.get('WingMining_StationB', '')
        self.skip_depot_check = self.ap.config.get('WingMining_SkipDepotCheck', False)

    def _get_current_station_name(self):
        return self.station_a if self.current_station_idx == 0 else self.station_b

    def _handle_travel_to_station(self):
        station_name = self._get_current_station_name()
        system, station = station_name.split('/')

        # Check if we are already docked at the target station
        ship_state = self.ap.jn.ship_state()
        if ship_state['status'] == 'in_station' and ship_state['cur_station'] == station:
            logger.info(f"Already docked at {station_name}. Skipping travel.")
            self.set_state(STATE_SCAN_FOR_MISSIONS)
            return

        self.ap.update_ap_status(f"Traveling to station: {station_name}")
        if self.ap.travel_to_destination(system, station):
            self.set_state(STATE_SCAN_FOR_MISSIONS)
        else:
            # Travel failed, stop the assist
            self.stop()

    def _handle_scan_for_missions(self):
        station_name = self._get_current_station_name()
        self.ap.update_ap_status(f"Scanning for missions at {station_name}")
        self.ap.stn_svcs_in_ship.goto_mission_board()

        new_missions = self.ap.stn_svcs_in_ship.scan_wing_missions()

        if new_missions:
            self.mission_queue.extend(new_missions)
            logger.info(f"Found {len(new_missions)} new missions.")
        else:
            logger.info(f"No new missions found at {station_name}.")
            if not self.current_mission and not self.skip_depot_check:
                logger.info("No current mission, checking depot for pending missions.")
                self.ap.keys.send("UI_Back", repeat=10)
                sleep(1)
                self.ap.stn_svcs_in_ship.goto_mission_board()
                sleep(1)
                pending_missions = self.ap.stn_svcs_in_ship.check_mission_depot_for_wing_missions()
                if pending_missions:
                    self.mission_queue.extend(pending_missions)
                    logger.info(f"Found {len(pending_missions)} pending missions in depot.")
            elif self.skip_depot_check:
                logger.info("Skipping mission depot check as per configuration.")

        self.ap.keys.send("UI_Back", repeat=4)
        sleep(1)
        self.set_state(STATE_PROCESS_QUEUE)

    def _handle_process_queue(self):
        if self.mission_queue:
            self.current_mission = self.mission_queue.pop(0)
            self.failed_carriers = [] # Reset blacklist for new mission
            self.set_state(STATE_TRAVEL_TO_FC)
        else:
            if self.mission_turned_in:
                self.set_state(STATE_RESCAN_STATION)
            else:
                self.set_state(STATE_SWITCH_STATION)

    def _handle_rescan_station(self):
        station_name = self._get_current_station_name()
        self.ap.update_ap_status(f"Re-scanning for missions at {station_name}")
        self.ap.stn_svcs_in_ship.goto_mission_board()

        new_missions = self.ap.stn_svcs_in_ship.scan_wing_missions()

        if new_missions:
            self.mission_queue.extend(new_missions)
            logger.info(f"Found {len(new_missions)} new missions during re-scan.")
            self.ap.keys.send("UI_Back", repeat=4)
            sleep(1)
            self.set_state(STATE_PROCESS_QUEUE)
        else:
            logger.info(f"No new missions found during re-scan at {station_name}.")
            self.ap.keys.send("UI_Back", repeat=4)
            sleep(1)
            self.set_state(STATE_SWITCH_STATION)

    def _handle_switch_station(self):
        self.mission_queue = []
        self.current_station_idx = 1 if self.current_station_idx == 0 else 0
        self.mission_turned_in = False
        logger.info(f"Switching to station index {self.current_station_idx}")
        self.set_state(STATE_TRAVEL_TO_STATION)

    def _find_best_carrier(self, commodity, blacklisted_carriers=[]):
        if self.ap.discord_handler and self.ap.discord_handler.running:
            data = self.ap.discord_handler.get_data()
        else:
            logger.error("Discord OCR handler is not running.")
            return None, None

        if not data:
            logger.error("No data available from Discord OCR handler.")
            return None, None

        commodity = commodity.capitalize()
        stations_data = data.get('stations', {})
        
        station_configs = [
            self._get_current_station_name(),
            self.station_b if self.current_station_idx == 0 else self.station_a
        ]

        for station_config in station_configs:
            system, config_station_name = station_config.split('/')
            for json_station in stations_data.keys():
                if json_station.upper() in config_station_name.upper():
                    carriers = stations_data[json_station]
                    best_carrier_name = None
                    max_quantity = 0
                    for carrier in carriers:
                        if carrier.get('carrier_name') in blacklisted_carriers:
                            continue
                        
                        if carrier.get('commodity').lower() == commodity.lower() and carrier.get('quantity') > max_quantity:
                            max_quantity = carrier.get('quantity')
                            best_carrier_name = carrier.get('carrier_name')
                    
                    if best_carrier_name:
                        logger.info(f"Found best carrier '{best_carrier_name}' at '{json_station}' with {max_quantity} of {commodity}.")
                        return best_carrier_name, system
        
        logger.warning(f"No carrier found for commodity {commodity} at any station.")
        return None, None

    def _handle_travel_to_fc(self):
        commodity = self.current_mission['commodity']
        fc_name, system = self._find_best_carrier(commodity, self.failed_carriers)

        if not fc_name:
            logger.error(f"No Fleet Carrier found for {commodity}. Returning to station to wait.")
            self.set_state(STATE_WAIT_AND_RECHECK)
            return
        
        self.current_carrier_name = fc_name
        self.ap.update_ap_status(f"Traveling to FC: {fc_name} for {self.current_mission['commodity']}")
        
        if self.ap.travel_to_destination(system, fc_name):
            self.set_state(STATE_BUY_COMMODITY)
        else:
            logger.error(f"Failed to travel to {fc_name}. Blacklisting and retrying.")
            self.failed_carriers.append(fc_name)
            self.set_state(STATE_TRAVEL_TO_FC)

    def _handle_buy_commodity(self):
        try:
            required_tonnage = self.current_mission['tonnage']
            commodity = self.current_mission['commodity']
            self.ap.update_ap_status(f"Buying {required_tonnage} tons of {commodity} from {self.current_carrier_name}")

            success, purchased_qty = self.ap.stn_svcs_in_ship.buy_commodity_for_mission(self.current_mission)

            if success:
                if purchased_qty < required_tonnage:
                    logger.info(f"Partial buy: Got {purchased_qty}/{required_tonnage} of {commodity}. Finding another carrier.")
                    self.ap.update_ap_status(f"Bought {purchased_qty}/{required_tonnage}. Need more.")
                    self.current_mission['tonnage'] = required_tonnage - purchased_qty
                    self.failed_carriers.append(self.current_carrier_name)
                    self.set_state(STATE_TRAVEL_TO_FC)
                else:
                    logger.info(f"Successfully purchased all required {commodity}.")
                    self.set_state(STATE_TRAVEL_TO_TURN_IN)
            else:
                logger.warning(f"Failed to buy commodity from {self.current_carrier_name}. Blacklisting and retrying.")
                self.failed_carriers.append(self.current_carrier_name)
                self.set_state(STATE_TRAVEL_TO_FC)

        except Exception as e:
            logger.error(f"Exception caught in _handle_buy_commodity: {e}")
            logger.error(traceback.format_exc())
            logger.warning(f"Re-queuing mission due to exception: {self.current_mission}")
            self.mission_queue.insert(0, self.current_mission)
            self.set_state(STATE_PROCESS_QUEUE)

    def _handle_travel_to_turn_in(self):
        station_name = self._get_current_station_name()
        self.ap.update_ap_status(f"Returning to {station_name} to turn in mission.")
        system, station = station_name.split('/')
        if self.ap.travel_to_destination(system, station):
            self.set_state(STATE_TURN_IN_MISSION)
        else:
            self.stop()

    def _handle_turn_in_mission(self):
        self.ap.update_ap_status(f"Turning in mission for {self.current_mission['commodity']}")
        if self.turn_in_mission(self.current_mission):
            self.completed_missions += 1
            self.ap.config['WingMining_CompletedMissions'] = self.completed_missions
            self.ap.update_config()
            self.ap.ap_ckb('update_wing_mining_mission_count', self.completed_missions)
            self.ap.update_ap_status(f"Mission for {self.current_mission['commodity']} complete. Total: {self.completed_missions}")
            self.mission_turned_in = True
        else:
            logger.warning(f"Failed to turn in mission, re-queuing: {self.current_mission}")
            self.mission_queue.insert(0, self.current_mission)

        self.current_mission = None
        self.set_state(STATE_PROCESS_QUEUE)

    def _handle_wait_and_recheck(self):
        station_name = self._get_current_station_name()
        self.ap.update_ap_status(f"Returning to {station_name} to wait.")
        system, station = station_name.split('/')
        
        ship_state = self.ap.jn.ship_state()
        if not (ship_state['status'] == 'in_station' and ship_state['cur_station'] == station):
            if not self.ap.travel_to_destination(system, station):
                logger.error(f"Failed to travel back to {station_name}. Stopping.")
                self.stop()
                return
        
        ship_state = self.ap.jn.ship_state()
        if not (ship_state['status'] == 'in_station' and ship_state['cur_station'] == station):
            logger.error(f"Failed to confirm docking at {station_name} after traveling. Stopping.")
            self.stop()
            return

        self.ap.update_ap_status("Waiting for 5 minutes before rechecking for carriers.")
        logger.info("Waiting for 5 minutes before rechecking for carriers.")
        sleep(300)

        self.mission_queue.insert(0, self.current_mission)
        self.current_mission = None
        self.set_state(STATE_PROCESS_QUEUE)

    def turn_in_mission(self, mission):
        self.ap.stn_svcs_in_ship.goto_mission_board()

        self.ap.keys.send("UI_Right", repeat=3)
        sleep(1)
        self.ap.keys.send("UI_Down")
        sleep(1)
        self.ap.keys.send("UI_Select")
        
        scl_reg_loaded = reg_scale_for_station(self.ap.stn_svcs_in_ship.reg['mission_loaded'], self.ap.scr.screen_width, self.ap.scr.screen_height)
        if not self.ap.ocr.wait_for_any_text(self.ap, scl_reg_loaded):
            logger.error("Timed out waiting for mission turn-in list to load.")
            self.ap.keys.send("UI_Back", repeat=4)
            return False

        if self._find_mission_in_list(mission):
            self.ap.keys.send("UI_Select")
            sleep(1)
            self.ap.keys.send("UI_Select")
            sleep(1)
            self.ap.keys.send("UI_Right", hold=10)
            sleep(1)
            self.ap.keys.send("UI_Select")
            sleep(5)
            self.ap.keys.send("UI_Back", repeat=6)
            return True
        else:
            logger.warning(f"Could not find mission to turn in: {mission}")
            self.ap.keys.send("UI_Back", repeat=4)
            return False

    def _find_mission_in_list(self, mission):
        # We need to match the mission based on its core attributes, not the full OCR text
        # which might include variable reward amounts.
        target_commodity = mission['commodity']
        target_tonnage = mission['tonnage']

        mission_name_patterns = [
            "Mine",
            "Mining rush for",
            "Blast out",
        ]
        
        scl_reg_list = self.ap.stn_svcs_in_ship.reg['missions_list']
        min_w, min_h = self.ap.stn_svcs_in_ship.mission_item_size['width'], self.ap.stn_svcs_in_ship.mission_item_size['height']

        self.ap.keys.send('UI_Down')
        sleep(0.5)

        in_list = False
        for _ in range(100): # Max 100 scrolls
            image = self.ap.ocr.capture_region_pct(scl_reg_list)
            img_selected, _, ocr_textlist = self.ap.ocr.get_highlighted_item_data(image, min_w, min_h)

            if img_selected is None and in_list:
                # End of list
                break
            in_list = True

            if not ocr_textlist:
                self.ap.keys.send('UI_Down')
                continue

            details_text = " ".join(ocr_textlist)
            logger.info(f"Scanning turn-in list: {details_text}")

            matched_prefix = self.ap.ocr.find_fuzzy_pattern_in_text(details_text, mission_name_patterns)
            if matched_prefix:
                try:
                    if "units of" in details_text.lower():
                        parts = details_text.lower().split("units of")
                        tonnage_str = parts[0].strip().split()[-1]
                        tonnage = self.ap.stn_svcs_in_ship._parse_number_with_ocr_errors(tonnage_str)
                        
                        commodity_candidate = parts[1].strip().split()[0]
                        
                        # Fuzzy match commodity
                        # Using string_similarity directly as we are comparing a candidate word with a known commodity
                        if self.ap.ocr.string_similarity(commodity_candidate.upper(), target_commodity.upper()) > 0.7 and tonnage == target_tonnage:
                            logger.info(f"Found matching mission to turn in: {details_text}")
                            return True
                except (IndexError, ValueError):
                    pass # Could not parse, move to next
            
            self.ap.keys.send('UI_Down')
            sleep(0.2)
        
        return False
