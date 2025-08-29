from time import sleep
import time
import traceback
from EDlogger import logger
import difflib

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
STATE_DONE = "DONE"


class WingMining:
    def __init__(self, ed_ap):
        self.ap = ed_ap
        self.state = STATE_IDLE
        self.mission_queue = []
        self.current_mission = None
        self.current_station_idx = 0  # 0 for A, 1 for B

    def start(self):
        logger.info("Starting Wing Mining sequence.")
        self.mission_queue = []
        self.current_mission = None
        self.current_station_idx = 0
        self._update_config_values()

        if self.ap.config.get('WingMining_CompletedMissions', 0) >= 20:
            self.set_state(STATE_DONE)
            return

        if not self.station_a or not self.station_b:
            logger.error("Wing Mining stations are not configured.")
            self.set_state(STATE_IDLE)
            return

        self.set_state(STATE_TRAVEL_TO_STATION)

    def stop(self):
        logger.info("Stopping Wing Mining sequence.")
        self.set_state(STATE_IDLE)

    def reset_mission_counter(self):
        logger.info("Resetting Wing Mining mission counter.")
        self.completed_missions = 0
        self.ap.config['WingMining_CompletedMissions'] = 0
        self.ap.update_config()
        self.ap.ap_ckb('update_wing_mining_mission_count', 0)
        self.stop() # Stop the sequence if it's running

    def run(self):
        if self.state == STATE_IDLE or self.state == STATE_DONE:
            return

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

    def set_state(self, new_state):
        if self.state != new_state:
            logger.info(f"Wing Mining state changing from {self.state} to {new_state}")
            self.state = new_state
            self.ap.update_ap_status(f"Wing Mining: {self.state}")

    def _update_config_values(self):
        self.completed_missions = self.ap.config.get('WingMining_CompletedMissions', 0)
        self.station_a = self.ap.config.get('WingMining_StationA', '')
        self.station_b = self.ap.config.get('WingMining_StationB', '')
        self.fc_config = {
            0: { # Station A
                "bertrandite": self.ap.config.get('WingMining_FC_A_Bertrandite', ''),
                "gold": self.ap.config.get('WingMining_FC_A_Gold', ''),
                "indite": self.ap.config.get('WingMining_FC_A_Indite', ''),
                "silver": self.ap.config.get('WingMining_FC_A_Silver', '')
            },
            1: { # Station B
                "bertrandite": self.ap.config.get('WingMining_FC_B_Bertrandite', ''),
                "gold": self.ap.config.get('WingMining_FC_B_Gold', ''),
                "indite": self.ap.config.get('WingMining_FC_B_Indite', ''),
                "silver": self.ap.config.get('WingMining_FC_B_Silver', '')
            }
        }

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

        accepted_ocr_texts = [m['ocr_text'] for m in self.mission_queue]
        new_missions = self.ap.stn_svcs_in_ship.scan_wing_missions(accepted_ocr_texts)

        if new_missions:
            self.mission_queue.extend(new_missions)
            logger.info(f"Found {len(new_missions)} new missions.")
        else:
            logger.info(f"No new missions found at {station_name}.")

        self.ap.keys.send("UI_Back", repeat=4)
        sleep(1)
        self.set_state(STATE_PROCESS_QUEUE)

    def _handle_process_queue(self):
        if self.mission_queue:
            self.current_mission = self.mission_queue.pop(0)
            self.set_state(STATE_TRAVEL_TO_FC)
        else:
            self.set_state(STATE_RESCAN_STATION)

    def _handle_rescan_station(self):
        station_name = self._get_current_station_name()
        self.ap.update_ap_status(f"Re-scanning for missions at {station_name}")
        self.ap.stn_svcs_in_ship.goto_mission_board()

        accepted_ocr_texts = [m['ocr_text'] for m in self.mission_queue]
        new_missions = self.ap.stn_svcs_in_ship.scan_wing_missions(accepted_ocr_texts)

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
        logger.info(f"Switching to station index {self.current_station_idx}")
        self.set_state(STATE_TRAVEL_TO_STATION)

    def _handle_travel_to_fc(self):
        commodity = self.current_mission['commodity'].lower()
        fc_name = self.fc_config[self.current_station_idx][commodity]
        if not fc_name:
            logger.error(f"No Fleet Carrier configured for {commodity} at station index {self.current_station_idx}")
            self.stop()
            return

        self.ap.update_ap_status(f"Traveling to FC: {fc_name} for {self.current_mission['commodity']}")
        system, station = fc_name.split('/')
        if self.ap.travel_to_destination(system, station):
            self.set_state(STATE_BUY_COMMODITY)
        else:
            self.stop()

    def _handle_buy_commodity(self):
        try:
            self.ap.update_ap_status(f"Buying {self.current_mission['tonnage']} tons of {self.current_mission['commodity']}")
            if self.ap.stn_svcs_in_ship.buy_commodity_for_mission(self.current_mission):
                self.set_state(STATE_TRAVEL_TO_TURN_IN)
            else:
                logger.warning(f"Failed to buy commodity (returned False), re-queuing mission: {self.current_mission}")
                self.mission_queue.insert(0, self.current_mission)
                self.set_state(STATE_PROCESS_QUEUE)
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
        else:
            logger.warning(f"Failed to turn in mission, re-queuing: {self.current_mission}")
            self.mission_queue.insert(0, self.current_mission)

        self.current_mission = None
        self.set_state(STATE_PROCESS_QUEUE)

    def turn_in_mission(self, mission):
        self.ap.stn_svcs_in_ship.goto_mission_board()

        scl_mission_board = self.ap.stn_svcs_in_ship.reg['mission_board_header']
        if not self.ap.ocr.wait_for_text(self.ap, [self.ap.locale["STN_SVCS_MISSION_BOARD_HEADER"]], scl_mission_board):
            logger.error("Could not verify that we are on the mission board.")
            self.ap.keys.send("UI_Back", repeat=4)
            return False

        self.ap.keys.send("UI_Right", repeat=3)
        sleep(1)
        self.ap.keys.send("UI_Down")
        sleep(1)
        self.ap.keys.send("UI_Select")
        sleep(2)

        scl_mission_depot_tab = self.ap.stn_svcs_in_ship.reg['mission_depot_tab']
        if not self.ap.ocr.wait_for_text(self.ap, [self.ap.locale["STN_SVCS_MISSION_DEPOT_TAB"]], scl_mission_depot_tab):
            logger.error("Could not verify that we are on the Mission Depot tab.")
            self.ap.keys.send("UI_Back", repeat=4)
            return False

        if self._find_mission_in_list(mission):
            self.ap.keys.send("UI_Select")
            sleep(1)
            self.ap.keys.send("UI_Select")
            sleep(1)
            self.ap.keys.send("UI_Right", hold=30)
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
        ocr_text_to_find = mission['ocr_text']
        scl_reg_list = self.ap.stn_svcs_in_ship.reg['missions_list']
        min_w, min_h = self.ap.stn_svcs_in_ship.mission_item_size['width'], self.ap.stn_svcs_in_ship.mission_item_size['height']

        self.ap.keys.send('UI_Up', state=1)
        sleep(1)
        self.ap.keys.send('UI_Up', state=0)
        sleep(0.1)

        last_text = ""
        for _ in range(20): # Scroll up to 20 times max
            image = self.ap.ocr.capture_region_pct(scl_reg_list)
            _, _, ocr_textlist = self.ap.ocr.get_highlighted_item_data(image, min_w, min_h)
            current_text = str(ocr_textlist)
            if last_text == current_text:
                break
            last_text = current_text
            self.ap.keys.send('UI_Up')
            sleep(0.2)

        item_found = False
        in_list = False
        for _ in range(100):
            image = self.ap.ocr.capture_region_pct(scl_reg_list)
            img_selected, _, ocr_textlist = self.ap.ocr.get_highlighted_item_data(image, min_w, min_h)

            if ocr_textlist:
                current_text = " ".join(ocr_textlist)
                similarity = difflib.SequenceMatcher(None, ocr_text_to_find, current_text).ratio()
                if similarity > 0.8:
                    item_found = True
                    break

            if img_selected is None and in_list:
                break

            in_list = True
            self.ap.keys.send('UI_Down')
            sleep(0.2)

        return item_found
