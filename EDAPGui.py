import queue
import sys
import os
import threading
import kthread
from datetime import datetime
from time import sleep
import cv2
import json
from pathlib import Path
import keyboard
import webbrowser
import requests


from PIL import Image, ImageGrab, ImageTk
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import messagebox
from tkinter import ttk
import sv_ttk
import pywinstyles
import sys
from tktooltip import ToolTip

from Voice import *
from MousePt import MousePoint

from Image_Templates import *
from Screen import *
from Screen_Regions import *
from EDKeys import *
from Screen_Regions import reg_scale_for_station
from EDJournal import *
#from ED_AP import *
from EDAPWaypointEditor import WaypointEditorTab
from WingMining import *

from EDlogger import logger


"""
File:EDAPGui.py

Description:
User interface for controlling the ED Autopilot

Note:
Ideas taken from:  https://github.com/skai2/EDAutopilot

 HotKeys:
    Home - Start FSD Assist
    INS  - Start SC Assist
    PG UP - Start Robigo Assist
    End - Terminate any ongoing assist (FSD, SC, AFK)

Author: sumzer0@yahoo.com
"""

# ---------------------------------------------------------------------------
# must be updated with a new release so that the update check works properly!
# contains the names of the release.
EDAP_VERSION = "V1.7.0 beta 1"
# depending on how release versions are best marked you could also change it to the release tag, see function check_update.
# ---------------------------------------------------------------------------

FORM_TYPE_CHECKBOX = 0
FORM_TYPE_SPINBOX = 1
FORM_TYPE_ENTRY = 2


def hyperlink_callback(url):
    webbrowser.open_new(url)


class APGui():
    def load_ocr_calibration_data(self):
        self.ocr_calibration_data = {}
        calibration_file = 'configs/ocr_calibration.json'

        default_regions = {
            "Screen_Regions.sun": {"rect": [0.30, 0.30, 0.70, 0.68]},
            "Screen_Regions.disengage": {"rect": [0.42, 0.65, 0.60, 0.80]},
            "Screen_Regions.sco": {"rect": [0.42, 0.65, 0.60, 0.80]},
            "Screen_Regions.fss": {"rect": [0.5045, 0.7545, 0.532, 0.7955]},
            "Screen_Regions.mission_dest": {"rect": [0.46, 0.38, 0.65, 0.86]},
            "Screen_Regions.missions": {"rect": [0.50, 0.78, 0.65, 0.85]},
            "EDInternalStatusPanel.tab_bar": {"rect": [0.35, 0.2, 0.85, 0.26]},
            "EDInternalStatusPanel.inventory_list": {"rect": [0.2, 0.3, 0.8, 0.9]},
            "EDInternalStatusPanel.size.inventory_item": {"width": 100, "height": 20},
            "EDInternalStatusPanel.size.nav_pnl_tab": {"width": 100, "height": 20},
            "EDStationServicesInShip.connected_to": {"rect": [0.0, 0.0, 0.30, 0.30]},
            "EDStationServicesInShip.carrier_admin_header": {"rect": [0.4, 0.1, 0.6, 0.2]},
            "EDStationServicesInShip.commodities_list": {"rect": [0.2, 0.2, 0.8, 0.9]},
            "EDStationServicesInShip.commodity_quantity": {"rect": [0.4, 0.5, 0.6, 0.6]},
            "EDStationServicesInShip.size.commodity_item": {"width": 100, "height": 15},
            "EDStationServicesInShip.mission_board_header": {"rect": [0.4, 0.1, 0.6, 0.2]},
            "EDStationServicesInShip.missions_list": {"rect": [0.06, 0.25, 0.48, 0.8]},
            "EDStationServicesInShip.mission_loaded": {"rect": [0.06, 0.25, 0.48, 0.35]},
            "EDStationServicesInShip.size.mission_item": {"width": 100, "height": 15},
            "EDGalaxyMap.cartographics": {"rect": [0.0, 0.0, 0.25, 0.25]},
            "EDSystemMap.cartographics": {"rect": [0.0, 0.0, 0.25, 0.25]},
            "EDNavigationPanel.tab_bar": {"rect": [0.0, 0.2, 0.7, 0.35]},
            "EDNavigationPanel.size.nav_pnl_tab": {"width": 260, "height": 35},
            "EDNavigationPanel.size.nav_pnl_location": {"width": 500, "height": 35},
            "EDNavigationPanel.deskew_angle": -1.0
        }

        if not os.path.exists(calibration_file):
            # Create the file with default values if it doesn't exist
            with open(calibration_file, 'w') as f:
                json.dump(default_regions, f, indent=4)
            self.ocr_calibration_data = default_regions
        else:
            with open(calibration_file, 'r') as f:
                self.ocr_calibration_data = json.load(f)

            # Check for missing keys and add them
            updated = False
            for key, value in default_regions.items():
                if key not in self.ocr_calibration_data:
                    self.ocr_calibration_data[key] = value
                    updated = True

            # If we updated the data, save it back to the file
            if updated:
                with open(calibration_file, 'w') as f:
                    json.dump(self.ocr_calibration_data, f, indent=4)

    def save_ocr_calibration_data(self):
        calibration_file = 'configs/ocr_calibration.json'
        with open(calibration_file, 'w') as f:
            json.dump(self.ocr_calibration_data, f, indent=4)
        self.log_msg("OCR calibration data saved.")
        messagebox.showinfo("Saved", "OCR calibration data saved.\nPlease restart the application for changes to take effect.")

    def __init__(self, root):
        self.root = root
        root.title("EDAutopilot " + EDAP_VERSION)
        # root.overrideredirect(True)
        # root.geometry("400x550")
        # root.configure(bg="blue")
        root.protocol("WM_DELETE_WINDOW", self.close_window)
        root.resizable(False, False)

        self.tooltips = {
            'FSD Route Assist': "Will execute your route. \nAt each jump the sequence will perform some fuel scooping.",
            'Supercruise Assist': "Will keep your ship pointed to target, \nyou target can only be a station for the autodocking to work.",
            'Waypoint Assist': "When selected, will prompt for the waypoint file. \nThe waypoint file contains System names that \nwill be entered into Galaxy Map and route plotted.",
            'Robigo Assist': "",
            'DSS Assist': "When selected, will perform DSS scans while you are traveling between stars.",
            'Single Waypoint Assist': "",
            'CUDA OCR': "RESTART REQUIRED! This requires an NVIDIA GPU with CUDA Cores. you must install CUDA 11.8 and CUDNN for CUDA 11.8.  performance difference is probably minimal.",
            'ELW Scanner': "Will perform FSS scans while FSD Assist is traveling between stars. \nIf the FSS shows a signal in the region of Earth, \nWater or Ammonia type worlds, it will announce that discovery.",
            'AFK Combat Assist': "Used with a AFK Combat ship in a Rez Zone.",
            'Fleet Carrier Assist': "Automates fleet carrier jumps along a waypoint route.",
            'Wing Mining Assist': "Automates wing mining missions.",
            'RollRate': "Roll rate your ship has in deg/sec. Higher the number the more maneuverable the ship.",
            'PitchRate': "Pitch (up/down) rate your ship has in deg/sec. Higher the number the more maneuverable the ship.",
            'YawRate': "Yaw rate (rudder) your ship has in deg/sec. Higher the number the more maneuverable the ship.",
            'SunPitchUp+Time': "This field are for ship that tend to overheat. \nProviding 1-2 more seconds of Pitch up when avoiding the Sun \nwill overcome this problem.",
            'Sun Bright Threshold': "The low level for brightness detection, \nrange 0-255, want to mask out darker items",
            'Nav Align Tries': "How many attempts the ap should make at alignment.",
            'Jump Tries': "How many attempts the ap should make to jump.",
            'Docking Retries': "How many attempts to make to dock.",
            'Wait For Autodock': "After docking granted, \nwait this amount of time for us to get docked with autodocking",
            'Start FSD': "Button to start FSD route assist.",
            'Start SC': "Button to start Supercruise assist.",
            'Start Robigo': "Button to start Robigo assist.",
            'Stop All': "Button to stop all assists.",
            'Refuel Threshold': "If fuel level get below this level, \nit will attempt refuel.",
            'Scoop Timeout': "Number of second to wait for full tank, \nmight mean we are not scooping well or got a small scooper",
            'Fuel Threshold Abort': "Level at which AP will terminate, \nbecause we are not scooping well.",
            'X Offset': "Offset left the screen to start place overlay text.",
            'Y Offset': "Offset down the screen to start place overlay text.",
            'Font Size': "Font size of the overlay.",
            'Calibrate': "Will iterate through a set of scaling values \ngetting the best match for your system. \nSee HOWTO-Calibrate.md",
            'Waypoint List Button': "Read in a file with with your Waypoints.",
            'Cap Mouse XY': "This will provide the StationCoord value of the Station in the SystemMap. \nSelecting this button and then clicking on the Station in the SystemMap \nwill return the x,y value that can be pasted in the waypoints file",
            'Reset Waypoint List': "Reset your waypoint list, \nthe waypoint assist will start again at the first point in the list.",
            'Auto-Dock Boost': "Enable boosting when disengaging from supercruise for docking.",
            'Auto-Dock Fwd Time': "Time in seconds to move forward after disengaging before attempting to dock.",
            'Auto-Dock Delay': "Time in seconds to wait after moving forward before requesting docking.",
            'Enable Webhook': "Enable sending log messages to a Discord webhook.",
            'Webhook URL': "The URL of the Discord webhook.",
            'User ID': "Your Discord User ID to be mentioned in the message."
        }

        self.gui_loaded = False
        self.log_buffer = queue.Queue()
        self.log_msg(f'Starting ED Autopilot {EDAP_VERSION}.')

        self.load_ocr_calibration_data()
        self.autopilot_server_url = tk.StringVar()
        self.autopilot_server_url.set("http://127.0.0.1:8001")

        self.config = {}
        self.ship_configs = {}
        self.pitchrate = 0.0
        self.rollrate = 0.0
        self.yawrate = 0.0
        self.sunpitchuptime = 0.0
        self.current_ship_type = None
        self.last_status_text = ""

        self.mouse = MousePoint()

        self.checkboxvar = {}
        self.radiobuttonvar = {}
        self.entries = {}
        self.lab_ck = {}
        self.single_waypoint_system = tk.StringVar()
        self.single_waypoint_station = tk.StringVar()
        self.TCE_Destination_Filepath = tk.StringVar()

        self.cv_view = False

        self.msgList = self.gui_gen(root)
        self.load_config_from_server()

        # check for updates
        self.check_updates()

        self.gui_loaded = True
        # Send a log entry which will flush out the buffer.
        self.log_msg('ED Autopilot GUI loaded successfully.')

        # Start the server polling thread
        self.polling_thread = kthread.KThread(target=self.poll_server, name="ServerPoller")
        self.polling_thread.start()

    def load_config_from_server(self):
        try:
            response = requests.get(f"{self.autopilot_server_url.get()}/config")
            response.raise_for_status()
            data = response.json()

            self.config = data.get('config', {})
            self.ship_configs = data.get('ship_configs', {})
            self.pitchrate = data.get('pitch', 0.0)
            self.rollrate = data.get('roll', 0.0)
            self.yawrate = data.get('yaw', 0.0)
            self.sunpitchuptime = data.get('sunpitchuptime', 0.0)

            self.TCE_Destination_Filepath.set(self.config.get('TCEDestinationFilepath', ''))

            self.checkboxvar['Enable Randomness'].set(self.config.get('EnableRandomness', False))
            self.checkboxvar['Activate Elite for each key'].set(self.config.get('ActivateEliteEachKey', False))
            self.checkboxvar['Automatic logout'].set(self.config.get('AutomaticLogout', False))
            self.checkboxvar['Enable Overlay'].set(self.config.get('OverlayTextEnable', False))
            self.checkboxvar['Enable Voice'].set(self.config.get('VoiceEnable', False))
            self.checkboxvar['DiscordWebhook'].set(self.config.get('DiscordWebhook', False))
            self.checkboxvar['CUDA OCR'].set(self.ocr_calibration_data.get('use_gpu_ocr', False))

            self.radiobuttonvar['dss_button'].set(self.config.get('DSSButton', 'Primary'))

            self.entries['ship']['PitchRate'].delete(0, tk.END)
            self.entries['ship']['RollRate'].delete(0, tk.END)
            self.entries['ship']['YawRate'].delete(0, tk.END)
            self.entries['ship']['SunPitchUp+Time'].delete(0, tk.END)
            self.entries['ship']['PitchRate'].insert(0, float(self.pitchrate))
            self.entries['ship']['RollRate'].insert(0, float(self.rollrate))
            self.entries['ship']['YawRate'].insert(0, float(self.yawrate))
            self.entries['ship']['SunPitchUp+Time'].insert(0, float(self.sunpitchuptime))

            self.entries['autopilot']['Sun Bright Threshold'].delete(0, tk.END)
            self.entries['autopilot']['Nav Align Tries'].delete(0, tk.END)
            self.entries['autopilot']['Jump Tries'].delete(0, tk.END)
            self.entries['autopilot']['Docking Retries'].delete(0, tk.END)
            self.entries['autopilot']['Wait For Autodock'].delete(0, tk.END)
            self.entries['autopilot']['Sun Bright Threshold'].insert(0, int(self.config.get('SunBrightThreshold', 125)))
            self.entries['autopilot']['Nav Align Tries'].insert(0, int(self.config.get('NavAlignTries', 3)))
            self.entries['autopilot']['Jump Tries'].insert(0, int(self.config.get('JumpTries', 3)))
            self.entries['autopilot']['Docking Retries'].insert(0, int(self.config.get('DockingRetries', 30)))
            self.entries['autopilot']['Wait For Autodock'].insert(0, int(self.config.get('WaitForAutoDockTimer', 240)))

            self.entries['refuel']['Refuel Threshold'].delete(0, tk.END)
            self.entries['refuel']['Scoop Timeout'].delete(0, tk.END)
            self.entries['refuel']['Fuel Threshold Abort'].delete(0, tk.END)
            self.entries['refuel']['Refuel Threshold'].insert(0, int(self.config.get('RefuelThreshold', 65)))
            self.entries['refuel']['Scoop Timeout'].insert(0, int(self.config.get('FuelScoopTimeOut', 35)))
            self.entries['refuel']['Fuel Threshold Abort'].insert(0, int(self.config.get('FuelThreasholdAbortAP', 10)))

            self.entries['overlay']['X Offset'].delete(0, tk.END)
            self.entries['overlay']['Y Offset'].delete(0, tk.END)
            self.entries['overlay']['Font Size'].delete(0, tk.END)
            self.entries['overlay']['X Offset'].insert(0, int(self.config.get('OverlayTextXOffset', 50)))
            self.entries['overlay']['Y Offset'].insert(0, int(self.config.get('OverlayTextYOffset', 400)))
            self.entries['overlay']['Font Size'].insert(0, int(self.config.get('OverlayTextFontSize', 14)))

            self.entries['buttons']['Start FSD'].delete(0, tk.END)
            self.entries['buttons']['Start SC'].delete(0, tk.END)
            self.entries['buttons']['Start Robigo'].delete(0, tk.END)
            self.entries['buttons']['Stop All'].delete(0, tk.END)
            self.entries['buttons']['Start FSD'].insert(0, str(self.config.get('HotKey_StartFSD', 'home')))
            self.entries['buttons']['Start SC'].insert(0, str(self.config.get('HotKey_StartSC', 'ins')))
            self.entries['buttons']['Start Robigo'].insert(0, str(self.config.get('HotKey_StartRobigo', 'pgup')))
            self.entries['buttons']['Stop All'].insert(0, str(self.config.get('HotKey_StopAllAssists', 'end')))

            self.entries['discord']['Webhook URL'].delete(0, tk.END)
            self.entries['discord']['Webhook URL'].insert(0, self.config.get('DiscordWebhookURL', ''))
            self.entries['discord']['User ID'].delete(0, tk.END)
            self.entries['discord']['User ID'].insert(0, self.config.get('DiscordUserID', ''))

            self.entries['ocr']['OcrServerUrl'].delete(0, tk.END)
            self.entries['ocr']['OcrServerUrl'].insert(0, self.config.get('OcrServerUrl', 'http://127.0.0.1:8000/ocr'))

            # Wing Mining Settings
            self.entries['wing_mining_station_a'].insert(0, self.config.get('WingMining_StationA', ''))
            self.entries['wing_mining_station_b'].insert(0, self.config.get('WingMining_StationB', ''))
            self.entries['wing_mining_fc_a_bertrandite'].insert(0, self.config.get('WingMining_FC_A_Bertrandite', ''))
            self.entries['wing_mining_fc_a_gold'].insert(0, self.config.get('WingMining_FC_A_Gold', ''))
            self.entries['wing_mining_fc_a_indite'].insert(0, self.config.get('WingMining_FC_A_Indite', ''))
            self.entries['wing_mining_fc_a_silver'].insert(0, self.config.get('WingMining_FC_A_Silver', ''))
            self.entries['wing_mining_fc_b_bertrandite'].insert(0, self.config.get('WingMining_FC_B_Bertrandite', ''))
            self.entries['wing_mining_fc_b_gold'].insert(0, self.config.get('WingMining_FC_B_Gold', ''))
            self.entries['wing_mining_fc_b_indite'].insert(0, self.config.get('WingMining_FC_B_Indite', ''))
            self.entries['wing_mining_fc_b_silver'].insert(0, self.config.get('WingMining_FC_B_Silver', ''))
            self.entries['wing_mining_discord_data_path'].insert(0, self.config.get('WingMiningDiscordDataPath', 'discord_data.json'))
            self.checkboxvar['WingMining_SkipDepotCheck'].set(self.config.get('WingMining_SkipDepotCheck', False))
            self.checkboxvar['WingMining_MissionScannerMode'].set(self.config.get('WingMining_MissionScannerMode', False))

            completed_missions = self.config.get('WingMining_CompletedMissions', 0)
            self.completed_missions_var.set(str(completed_missions))
            self.entries['wing_mining_mission_count'].insert(0, str(completed_missions))

            if self.config.get('LogDEBUG'):
                self.radiobuttonvar['debug_mode'].set("Debug")
            elif self.config.get('LogINFO'):
                self.radiobuttonvar['debug_mode'].set("Info")
            else:
                self.radiobuttonvar['debug_mode'].set("Error")

            self.checkboxvar['Debug Overlay'].set(self.config.get('DebugOverlay', False))
            if 'DisableLogFile' in self.config:
                self.checkboxvar['DisableLogFile'].set(self.config.get('DisableLogFile', False))

            self.log_msg("Configuration loaded from server.")
            self.setup_hotkeys()

        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error loading config from server: {e}")
            messagebox.showerror("Connection Error", "Could not connect to the autopilot server. Please ensure it is running and the URL is correct.")

    def setup_hotkeys(self):
        # The keyboard library should handle replacing hotkeys, so we don't need to remove them all.
        # This also avoids a crash with some versions of the library.

        # Add new hotkeys based on the loaded config
        keyboard.add_hotkey(self.config.get('HotKey_StopAllAssists', 'end'), self.stop_all_assists)
        keyboard.add_hotkey(self.config.get('HotKey_StartFSD', 'home'), lambda: self.check_cb_by_hotkey('FSD Route Assist'))
        keyboard.add_hotkey(self.config.get('HotKey_StartSC', 'ins'), lambda: self.check_cb_by_hotkey('Supercruise Assist'))
        keyboard.add_hotkey(self.config.get('HotKey_StartRobigo', 'pgup'), lambda: self.check_cb_by_hotkey('Robigo Assist'))

    def check_cb_by_hotkey(self, field):
        """
        Toggles the state of a checkbox when a hotkey is pressed.
        """
        current_state = self.checkboxvar[field].get()
        self.checkboxvar[field].set(1 - current_state) # Toggle
        self.check_cb(field)

    def poll_server(self):
        while True:
            try:
                # Poll for events
                response = requests.get(f"{self.autopilot_server_url.get()}/events")
                response.raise_for_status()
                events = response.json().get('events', [])
                for event in events:
                    self.handle_server_event(event['type'], event['payload'])

                # Poll for status
                status_response = requests.get(f"{self.autopilot_server_url.get()}/status")
                status_response.raise_for_status()
                status_data = status_response.json()
                self.update_gui_from_status(status_data)

            except requests.exceptions.RequestException as e:
                # Don't spam the log if the server is just not running
                sleep(2)

            sleep(0.2) # Poll every 200ms

    def handle_server_event(self, msg, body=None):
        if msg == 'log':
            self.log_msg(body)
        elif msg == 'log+vce':
            self.log_msg(body)
            # Voice should be handled server-side if possible, but we can add a client-side option if needed
        elif msg == 'statusline':
            self.update_statusline(body)
        elif msg == 'jumpcount':
            self.update_jumpcount(body)
        elif msg == 'update_ship_cfg':
            self.update_ship_cfg()
        elif msg == 'update_wing_mining_mission_count':
            self.completed_missions_var.set(str(body))
            self.entries['wing_mining_mission_count'].delete(0, tk.END)
            self.entries['wing_mining_mission_count'].insert(0, str(body))
        # The '..._stop' messages can be handled by the general status update
        # but we can also handle them here for immediate feedback if desired.
        elif msg.endswith('_stop'):
             # e.g. 'fsd_stop' -> 'FSD Route Assist'
            assist_name = msg.replace('_', ' ').replace('stop', 'Assist').title()
            if 'Fsd' in assist_name: assist_name = 'FSD Route Assist'
            if 'Sc' in assist_name: assist_name = 'Supercruise Assist'
            if 'Afk' in assist_name: assist_name = 'AFK Combat Assist'
            if 'Fc' in assist_name: assist_name = 'Fleet Carrier Assist'

            if assist_name in self.checkboxvar:
                if self.checkboxvar[assist_name].get() == 1:
                    self.checkboxvar[assist_name].set(0)
                    self.check_cb(assist_name) # To update button states

    def update_gui_from_status(self, status_data):
        # Mapping from status key to GUI checkbox field name
        status_map = {
            'fsd_assist_enabled': 'FSD Route Assist',
            'sc_assist_enabled': 'Supercruise Assist',
            'waypoint_assist_enabled': 'Waypoint Assist',
            'robigo_assist_enabled': 'Robigo Assist',
            'afk_combat_assist_enabled': 'AFK Combat Assist',
            'dss_assist_enabled': 'DSS Assist',
            'single_waypoint_enabled': 'Single Waypoint Assist',
            'fc_assist_enabled': 'Fleet Carrier Assist',
            'wing_mining_assist_enabled': 'Wing Mining Assist',
        }

        for status_key, field_name in status_map.items():
            is_running = status_data.get(status_key, False)
            if self.checkboxvar[field_name].get() != is_running:
                self.checkboxvar[field_name].set(is_running)
                # This will trigger the check_cb logic to disable/enable other buttons
                self.check_cb(field_name)

        self.update_statusline(status_data.get('ap_state', 'Idle'))
        self.current_ship_type = status_data.get('ship_state', {}).get('type')


    def update_ship_cfg(self):
        # This can be called by an event from the server when the ship changes
        self.log_msg("Ship changed, reloading configuration from server.")
        self.load_config_from_server()

    def calibrate_callback(self):
        try:
            requests.post(f"{self.autopilot_server_url.get()}/calibrate/target")
            self.log_msg("Target calibration started.")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting target calibration: {e}")

    def calibrate_compass_callback(self):
        try:
            requests.post(f"{self.autopilot_server_url.get()}/calibrate/compass")
            self.log_msg("Compass calibration started.")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting compass calibration: {e}")

    def quit(self):
        logger.debug("Entered: quit")
        self.close_window()

    def close_window(self):
        logger.debug("Entered: close_window")
        self.stop_all_assists()
        if hasattr(self, 'polling_thread') and self.polling_thread.is_alive():
            self.polling_thread.terminate()
        sleep(0.1)
        self.root.destroy()

    # this routine is to stop any current autopilot activity
    def stop_all_assists(self):
        logger.debug("Entered: stop_all_assists")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/stop_all")
            self.log_msg("Sent stop all assists command.")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error stopping all assists: {e}")

    def start_fsd(self):
        logger.debug("Entered: start_fsd")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/start/fsd")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting FSD assist: {e}")

    def stop_fsd(self):
        logger.debug("Entered: stop_fsd")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/stop/fsd")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error stopping FSD assist: {e}")

    def start_sc(self):
        logger.debug("Entered: start_sc")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/start/sc")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting SC assist: {e}")

    def stop_sc(self):
        logger.debug("Entered: stop_sc")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/stop/sc")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error stopping SC assist: {e}")

    def start_waypoint(self):
        logger.debug("Entered: start_waypoint")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/start/waypoint")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting waypoint assist: {e}")

    def stop_waypoint(self):
        logger.debug("Entered: stop_waypoint")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/stop/waypoint")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error stopping waypoint assist: {e}")

    def start_robigo(self):
        logger.debug("Entered: start_robigo")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/start/robigo")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting robigo assist: {e}")

    def stop_robigo(self):
        logger.debug("Entered: stop_robigo")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/stop/robigo")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error stopping robigo assist: {e}")

    def start_dss(self):
        logger.debug("Entered: start_dss")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/start/dss")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting DSS assist: {e}")

    def stop_dss(self):
        logger.debug("Entered: stop_dss")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/stop/dss")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error stopping DSS assist: {e}")

    def start_single_waypoint_assist(self):
        """ The debug command to go to a system or station or both."""
        logger.debug("Entered: start_single_waypoint_assist")
        system = self.single_waypoint_system.get()
        station = self.single_waypoint_station.get()

        if system != "" or station != "":
            try:
                requests.post(f"{self.autopilot_server_url.get()}/start/single_waypoint", json={"system": system, "station": station})
            except requests.exceptions.RequestException as e:
                self.log_msg(f"Error starting single waypoint assist: {e}")

    def stop_single_waypoint_assist(self):
        """ The debug command to go to a system or station or both."""
        logger.debug("Entered: stop_single_waypoint_assist")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/stop/single_waypoint")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error stopping single waypoint assist: {e}")

    def start_fc(self):
        logger.debug("Entered: start_fc")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/start/fc")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting Fleet Carrier assist: {e}")

    def stop_fc(self):
        logger.debug("Entered: stop_fc")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/stop/fc")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error stopping Fleet Carrier assist: {e}")

    def start_wing_mining(self):
        logger.debug("Entered: start_wing_mining")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/start/wing_mining")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting Wing Mining assist: {e}")

    def stop_wing_mining(self):
        logger.debug("Entered: stop_wing_mining")
        try:
            requests.post(f"{self.autopilot_server_url.get()}/stop/wing_mining")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error stopping Wing Mining assist: {e}")

    def about(self):
        webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui")

    def check_updates(self):
        # response = requests.get("https://api.github.com/repos/SumZer0-git/EDAPGui/releases/latest")
        # if EDAP_VERSION != response.json()["name"]:
        #     mb = messagebox.askokcancel("Update Check", "A new release version is available. Download now?")
        #     if mb == True:
        #         webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui/releases/latest")
        pass

    def open_changelog(self):
        webbrowser.open_new("https://github.com/SumZer0-git/EDAPGui/blob/main/ChangeLog.md")

    def open_discord(self):
        webbrowser.open_new("https://discord.gg/HCgkfSc")

    def open_logfile(self):
        os.startfile('autopilot.log')

    def log_msg(self, msg):
        message = datetime.now().strftime("%H:%M:%S: ") + msg

        if not self.gui_loaded:
            # Store message in queue
            self.log_buffer.put(message)
            logger.info(msg)
        else:
            # Add queued messages to the list
            while not self.log_buffer.empty():
                self.msgList.insert(tk.END, self.log_buffer.get())

            self.msgList.insert(tk.END, message)
            self.msgList.yview(tk.END)
            logger.info(msg)

            # if self.ed_ap.discord_bot:
            #     self.ed_ap.discord_bot.send_message(msg)

    def set_statusbar(self, txt):
        self.statusbar.configure(text=txt)

    def update_jumpcount(self, txt):
        self.jumpcount.configure(text=txt)

    def update_statusline(self, txt):
        if txt != self.last_status_text:
            self.status.configure(text="Status: " + txt)
            self.log_msg(f"Status update: {txt}")
            self.last_status_text = txt

    def ship_tst_pitch(self):
        try:
            requests.post(f"{self.autopilot_server_url.get()}/test/pitch")
            self.log_msg("Pitch test started.")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting pitch test: {e}")

    def ship_tst_roll(self):
        try:
            requests.post(f"{self.autopilot_server_url.get()}/test/roll")
            self.log_msg("Roll test started.")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting roll test: {e}")

    def ship_tst_yaw(self):
        try:
            requests.post(f"{self.autopilot_server_url.get()}/test/yaw")
            self.log_msg("Yaw test started.")
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error starting yaw test: {e}")

    def open_wp_file(self):
        filetypes = (
            ('json files', '*.json'),
            ('All files', '*.*')
        )
        filename = fd.askopenfilename(title="Waypoint File", initialdir='./waypoints/', filetypes=filetypes)
        if filename != "":
            try:
                response = requests.post(f"{self.autopilot_server_url.get()}/waypoints/load", json={"filename": filename})
                response.raise_for_status()
                if response.json().get("success"):
                    self.wp_filelabel.set("loaded: " + Path(filename).name)
                    self.log_msg(f"Waypoint file loaded: {filename}")
                else:
                    self.wp_filelabel.set("<no list loaded>")
                    self.log_msg(f"Failed to load waypoint file: {filename}")
                    messagebox.showerror("Load Error", "Server failed to load waypoint file.")
            except requests.exceptions.RequestException as e:
                self.log_msg(f"Error loading waypoint file: {e}")
                messagebox.showerror("Load Error", f"Could not send waypoint file to server: {e}")


    def reset_wp_file(self):
        if self.WP_A_running != True:
            mb = messagebox.askokcancel("Waypoint List Reset", "After resetting the Waypoint List, the Waypoint Assist will start again from the first point in the list at the next start.")
            if mb == True:
                try:
                    response = requests.post(f"{self.autopilot_server_url.get()}/waypoints/reset")
                    response.raise_for_status()
                    self.log_msg("Waypoint list reset on server.")
                except requests.exceptions.RequestException as e:
                    self.log_msg(f"Error resetting waypoints: {e}")
                    messagebox.showerror("Reset Error", f"Could not reset waypoints on server: {e}")
        else:
            mb = messagebox.showerror("Waypoint List Error", "Waypoint Assist must be disabled before you can reset the list.")

    def save_settings(self):
        self.entry_update()
        try:
            payload = {
                "config": self.config,
                "ship_configs": self.ship_configs
            }
            response = requests.post(f"{self.autopilot_server_url.get()}/config", json=payload)
            response.raise_for_status()
            self.log_msg("Settings saved to server.")
            # Also save local-only OCR data
            self.save_ocr_calibration_data()
            # Re-apply hotkeys in case they changed
            self.setup_hotkeys()
        except requests.exceptions.RequestException as e:
            self.log_msg(f"Error saving settings: {e}")
            messagebox.showerror("Save Error", f"Could not save settings to server: {e}")


    def load_tce_dest(self):
        # This functionality should now be handled by the server if needed,
        # or the GUI can read the local file and then use the single waypoint assist.
        # For now, we will assume local file reading.
        filepath = self.TCE_Destination_Filepath.get()
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as json_file:
                    f_details = json.load(json_file)
                self.single_waypoint_system.set(f_details.get('StarSystem', ''))
                self.single_waypoint_station.set(f_details.get('Station', ''))
                self.log_msg(f"Loaded TCE destination from {filepath}")
            except Exception as e:
                self.log_msg(f"Error reading TCE file: {e}")
                messagebox.showerror("File Error", f"Could not read TCE destination file: {e}")
        else:
            self.log_msg(f"TCE destination file not found: {filepath}")
            messagebox.showwarning("File Not Found", f"TCE destination file not found at:\n{filepath}")


    # new data was added to a field, re-read them all for simple logic
    def entry_update(self, event=''):
        # This method will now update the local config dictionary,
        # which will then be sent to the server when save_settings is called.
        try:
            # --- Ship Configs ---
            if not self.current_ship_type:
                return # Don't do anything if we don't know the ship type yet

            current_ship_type = self.current_ship_type
            if current_ship_type not in self.ship_configs.get("Ship_Configs", {}):
                self.ship_configs["Ship_Configs"][current_ship_type] = {}

            ship_cfg = self.ship_configs["Ship_Configs"][current_ship_type]
            ship_cfg['PitchRate'] = float(self.entries['ship']['PitchRate'].get())
            ship_cfg['RollRate'] = float(self.entries['ship']['RollRate'].get())
            ship_cfg['YawRate'] = float(self.entries['ship']['YawRate'].get())
            ship_cfg['SunPitchUp+Time'] = float(self.entries['ship']['SunPitchUp+Time'].get())
            ship_cfg['AutoDockBoost'] = self.checkboxvar['AutoDockBoost'].get()
            ship_cfg['AutoDockForwardTime'] = int(self.entries['ship']['AutoDockForwardTime'].get())
            ship_cfg['AutoDockDelayTime'] = int(self.entries['ship']['AutoDockDelayTime'].get())

            # --- Main Config ---
            self.config['SunBrightThreshold'] = int(self.entries['autopilot']['Sun Bright Threshold'].get())
            self.config['NavAlignTries'] = int(self.entries['autopilot']['Nav Align Tries'].get())
            self.config['JumpTries'] = int(self.entries['autopilot']['Jump Tries'].get())
            self.config['DockingRetries'] = int(self.entries['autopilot']['Docking Retries'].get())
            self.config['WaitForAutoDockTimer'] = int(self.entries['autopilot']['Wait For Autodock'].get())
            self.config['RefuelThreshold'] = int(self.entries['refuel']['Refuel Threshold'].get())
            self.config['FuelScoopTimeOut'] = int(self.entries['refuel']['Scoop Timeout'].get())
            self.config['FuelThreasholdAbortAP'] = int(self.entries['refuel']['Fuel Threshold Abort'].get())
            self.config['OverlayTextXOffset'] = int(self.entries['overlay']['X Offset'].get())
            self.config['OverlayTextYOffset'] = int(self.entries['overlay']['Y Offset'].get())
            self.config['OverlayTextFontSize'] = int(self.entries['overlay']['Font Size'].get())
            self.config['HotKey_StartFSD'] = self.entries['buttons']['Start FSD'].get()
            self.config['HotKey_StartSC'] = self.entries['buttons']['Start SC'].get()
            self.config['HotKey_StartRobigo'] = self.entries['buttons']['Start Robigo'].get()
            self.config['HotKey_StopAllAssists'] = self.entries['buttons']['Stop All'].get()
            self.config['DiscordWebhookURL'] = self.entries['discord']['Webhook URL'].get()
            self.config['DiscordUserID'] = self.entries['discord']['User ID'].get()
            self.config['OcrServerUrl'] = self.entries['ocr']['OcrServerUrl'].get()
            self.config['TCEDestinationFilepath'] = self.TCE_Destination_Filepath.get()

            self.config['EnableRandomness'] = self.checkboxvar['Enable Randomness'].get()
            self.config['ActivateEliteEachKey'] = self.checkboxvar['Activate Elite for each key'].get()
            self.config['AutomaticLogout'] = self.checkboxvar['Automatic logout'].get()
            self.config['OverlayTextEnable'] = self.checkboxvar['Enable Overlay'].get()
            self.config['VoiceEnable'] = self.checkboxvar['Enable Voice'].get()
            self.config['DiscordWebhook'] = self.checkboxvar['DiscordWebhook'].get()
            self.config['DSSButton'] = self.radiobuttonvar['dss_button'].get()
            self.config['DebugOverlay'] = self.checkboxvar['Debug Overlay'].get()
            self.config['DisableLogFile'] = self.checkboxvar['DisableLogFile'].get()

            log_mode = self.radiobuttonvar['debug_mode'].get()
            self.config['LogDEBUG'] = (log_mode == "Debug")
            self.config['LogINFO'] = (log_mode == "Info" or log_mode == "Debug")

        except (ValueError, tk.TclError) as e:
            # Ignore errors that happen during user input
            pass


    # ckbox.state:(ACTIVE | DISABLED)

    # ('FSD Route Assist', 'Supercruise Assist', 'Enable Voice', 'Enable CV View')
    def check_cb(self, field):
        is_checked = self.checkboxvar[field].get() == 1

        assist_map = {
            'FSD Route Assist': ('fsd', self.start_fsd, self.stop_fsd),
            'Supercruise Assist': ('sc', self.start_sc, self.stop_sc),
            'Waypoint Assist': ('waypoint', self.start_waypoint, self.stop_waypoint),
            'Robigo Assist': ('robigo', self.start_robigo, self.stop_robigo),
            'AFK Combat Assist': ('afk_combat', lambda: requests.post(f"{self.autopilot_server_url.get()}/start/afk_combat"), lambda: requests.post(f"{self.autopilot_server_url.get()}/stop/afk_combat")),
            'DSS Assist': ('dss', self.start_dss, self.stop_dss),
            'Fleet Carrier Assist': ('fc', self.start_fc, self.stop_fc),
            'Wing Mining Assist': ('wing_mining', self.start_wing_mining, self.stop_wing_mining),
            'Single Waypoint Assist': ('single_waypoint', self.start_single_waypoint_assist, self.stop_single_waypoint_assist),
        }

        # Handle mutually exclusive assists
        if field in assist_map:
            start_func, stop_func = assist_map[field][1], assist_map[field][2]
            if is_checked:
                for other_field, (other_key, _, _) in assist_map.items():
                    if other_field != field:
                        self.lab_ck[other_field].config(state='disabled')
                start_func()
            else:
                for other_field, (other_key, _, _) in assist_map.items():
                    if other_field != field:
                        self.lab_ck[other_field].config(state='active')
                stop_func()

        # For settings checkboxes, we update the local config and then save it to the server.
        if field in ['Enable Randomness', 'Activate Elite for each key', 'Automatic logout',
                     'Enable Overlay', 'Enable Voice', 'ELW Scanner', 'Enable CV View',
                     'Debug Overlay', 'DisableLogFile', 'AutoDockBoost', 'DiscordWebhook', 'dss_button', 'debug_mode']:
            self.entry_update()
            self.save_settings()

        # For settings checkboxes, we update the local config and then save it to the server.
        if field in ['Enable Randomness', 'Activate Elite for each key', 'Automatic logout',
                     'Enable Overlay', 'Enable Voice', 'ELW Scanner', 'Enable CV View',
                     'Debug Overlay', 'DisableLogFile', 'AutoDockBoost', 'DiscordWebhook', 'dss_button', 'debug_mode']:
            self.entry_update()
            self.save_settings()

        if field == 'Single Waypoint Assist':
            if self.checkboxvar['Single Waypoint Assist'].get() == 1 and self.SWP_A_running == False:
                self.start_single_waypoint_assist()
            elif self.checkboxvar['Single Waypoint Assist'].get() == 0 and self.SWP_A_running == True:
                self.stop_single_waypoint_assist()

        if field == 'CUDA OCR':
            self.ocr_calibration_data['use_gpu_ocr'] = self.checkboxvar['CUDA OCR'].get()
            self.save_ocr_calibration_data()

    def makeform(self, win, ftype, fields, r=0, inc=1, rfrom=0, rto=1000):
        entries = {}
        win.columnconfigure(1, weight=1)

        for field in fields:
            if ftype == FORM_TYPE_CHECKBOX:
                self.checkboxvar[field] = tk.IntVar()
                lab = ttk.Checkbutton(win, text=field, variable=self.checkboxvar[field], command=(lambda field=field: self.check_cb(field)))
                self.lab_ck[field] = lab
                lab.grid(row=r, column=0, columnspan=2, padx=2, pady=2, sticky=tk.W)
            else:
                lab = ttk.Label(win, text=field + ": ")
                if ftype == FORM_TYPE_SPINBOX:
                    ent = ttk.Spinbox(win, width=10, from_=rfrom, to=rto, increment=inc, justify=tk.RIGHT)
                else:
                    ent = ttk.Entry(win, width=10, justify=tk.RIGHT)
                ent.bind('<FocusOut>', self.entry_update)
                ent.insert(0, "0")
                lab.grid(row=r, column=0, padx=2, pady=2, sticky=tk.W)
                ent.grid(row=r, column=1, padx=2, pady=2, sticky=tk.E)
                entries[field] = ent

            lab = ToolTip(lab, msg=self.tooltips[field], delay=1.0, bg="#808080", fg="#FFFFFF")
            r += 1
        return entries

    # OCR calibration methods moved to before __init__

    def on_region_select(self, event):
        selected_region = self.calibration_region_var.get()
        if selected_region in self.ocr_calibration_data:
            rect = self.ocr_calibration_data[selected_region]['rect']
            self.calibration_rect_label_var.set(f"[{rect[0]:.4f}, {rect[1]:.4f}, {rect[2]:.4f}, {rect[3]:.4f}]")

    def create_calibration_tab(self, tab):
        self.load_ocr_calibration_data()
        tab.columnconfigure(0, weight=1)

        # Region Calibration
        blk_region_cal = ttk.LabelFrame(tab, text="Region Calibration")
        blk_region_cal.grid(row=0, column=0, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_region_cal.columnconfigure(1, weight=1)

        region_keys = sorted([key for key, value in self.ocr_calibration_data.items() if isinstance(value, dict) and 'rect' in value and 'compass' not in key and 'target' not in key])
        self.calibration_region_var = tk.StringVar()
        self.calibration_region_combo = ttk.Combobox(blk_region_cal, textvariable=self.calibration_region_var, values=region_keys)
        self.calibration_region_combo.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.calibration_region_combo.bind("<<ComboboxSelected>>", self.on_region_select)

        ttk.Label(blk_region_cal, text="Region:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(blk_region_cal, text="Rect:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.calibration_rect_label_var = tk.StringVar()
        ttk.Label(blk_region_cal, textvariable=self.calibration_rect_label_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Button(blk_region_cal, text="Calibrate Region", command=self.calibrate_ocr_region).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

        # Size Calibration
        blk_size_cal = ttk.LabelFrame(tab, text="Size Calibration")
        blk_size_cal.grid(row=1, column=0, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_size_cal.columnconfigure(1, weight=1)

        size_keys = sorted([key for key in self.ocr_calibration_data.keys() if '.size.' in key])
        self.calibration_size_var = tk.StringVar()
        self.calibration_size_combo = ttk.Combobox(blk_size_cal, textvariable=self.calibration_size_var, values=size_keys)
        self.calibration_size_combo.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.calibration_size_combo.bind("<<ComboboxSelected>>", self.on_size_select)

        ttk.Label(blk_size_cal, text="Size:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(blk_size_cal, text="W/H:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.calibration_size_label_var = tk.StringVar()
        ttk.Label(blk_size_cal, textvariable=self.calibration_size_label_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Button(blk_size_cal, text="Calibrate Size", command=self.calibrate_ocr_size).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

        # Other Calibrations
        blk_other_cal = ttk.LabelFrame(tab, text="Other Calibrations")
        blk_other_cal.grid(row=2, column=0, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))

        btn_calibrate_compass = ttk.Button(blk_other_cal, text="Calibrate Compass", command=self.calibrate_compass_callback)
        btn_calibrate_compass.pack(side=tk.LEFT, padx=5, pady=5)

        btn_calibrate_target = ttk.Button(blk_other_cal, text="Calibrate Target", command=self.calibrate_callback)
        btn_calibrate_target.pack(side=tk.LEFT, padx=5, pady=5)

        self.checkboxvar['CUDA OCR'] = tk.BooleanVar()
        cb_cuda_ocr = ttk.Checkbutton(blk_other_cal, text='CUDA OCR', variable=self.checkboxvar['CUDA OCR'], command=(lambda field='CUDA OCR': self.check_cb(field)))
        cb_cuda_ocr.pack(side=tk.LEFT, padx=5, pady=5)
        tip_cuda_ocr = ToolTip(cb_cuda_ocr, msg=self.tooltips['CUDA OCR'], delay=1.0, bg="#808080", fg="#FFFFFF")

        # Value Calibration
        blk_value_cal = ttk.LabelFrame(tab, text="Value Calibration")
        blk_value_cal.grid(row=3, column=0, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_value_cal.columnconfigure(1, weight=1)

        ttk.Label(blk_value_cal, text="Nav Panel Deskew Angle:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.deskew_angle_var = tk.DoubleVar(value=self.ocr_calibration_data.get("EDNavigationPanel.deskew_angle", 0.0))
        self.deskew_angle_spinbox = ttk.Spinbox(blk_value_cal, from_=-45.0, to=45.0, increment=0.1, textvariable=self.deskew_angle_var, command=self.on_value_change)
        self.deskew_angle_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.deskew_angle_spinbox.bind('<FocusOut>', self.on_value_change)


        # Button Frame
        button_frame = ttk.Frame(tab)
        button_frame.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        ttk.Button(button_frame, text="Save All Calibrations", command=self.save_ocr_calibration_data, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset All to Default", command=self.reset_all_calibrations).pack(side=tk.LEFT, padx=5)

    def on_value_change(self, event=None):
        try:
            angle = self.deskew_angle_var.get()
            self.ocr_calibration_data["EDNavigationPanel.deskew_angle"] = angle
            self.log_msg(f"Nav Panel Deskew Angle set to: {angle}")
        except tk.TclError:
            # This can happen if the spinbox is empty during input
            pass

    def on_size_select(self, event):
        selected_size = self.calibration_size_var.get()
        if selected_size in self.ocr_calibration_data:
            size = self.ocr_calibration_data[selected_size]
            self.calibration_size_label_var.set(f"W: {size['width']}, H: {size['height']}")

    def calibrate_ocr_size(self):
        selected_size = self.calibration_size_var.get()
        if not selected_size:
            messagebox.showerror("Error", "Please select a size to calibrate.")
            return

        self.log_msg(f"Starting size calibration for: {selected_size}")

        self.calibration_overlay = tk.Toplevel(self.root)
        self.calibration_overlay.overrideredirect(True)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.calibration_overlay.geometry(f"{screen_w}x{screen_h}+0+0")

        self.calibration_overlay.attributes('-alpha', 0.3)

        self.calibration_canvas = tk.Canvas(self.calibration_overlay, highlightthickness=0, bg='black')
        self.calibration_canvas.pack(fill=tk.BOTH, expand=True)

        # Scale and display the current size for reference
        ref_w = 1920.0
        x_scale = screen_w / ref_w

        current_size = self.ocr_calibration_data[selected_size]
        current_w = current_size['width'] * x_scale
        current_h = current_size['height'] * x_scale

        # Center the reference box
        center_x = screen_w / 2
        center_y = screen_h / 2
        x1 = center_x - current_w / 2
        y1 = center_y - current_h / 2
        x2 = center_x + current_w / 2
        y2 = center_y + current_h / 2
        self.calibration_canvas.create_rectangle(x1, y1, x2, y2, outline='yellow', width=2)

        self.start_x = None
        self.start_y = None
        self.current_rect = None

        self.calibration_canvas.bind("<ButtonPress-1>", self.on_size_cal_press)
        self.calibration_canvas.bind("<B1-Motion>", self.on_size_cal_drag)
        self.calibration_canvas.bind("<ButtonRelease-1>", self.on_size_cal_release)
        self.calibration_overlay.bind("<Escape>", lambda e: self.calibration_overlay.destroy())

    def on_size_cal_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.current_rect = self.calibration_canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='green', width=2)

    def on_size_cal_drag(self, event):
        if self.current_rect:
            self.calibration_canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)

    def on_size_cal_release(self, event):
        end_x = event.x
        end_y = event.y

        # Un-scale the captured pixel size back to 1080p reference
        screen_w = self.root.winfo_screenwidth()
        ref_w = 1920.0
        x_scale = screen_w / ref_w

        captured_width = abs(self.start_x - end_x)
        captured_height = abs(self.start_y - end_y)

        base_width = int(captured_width / x_scale)
        base_height = int(captured_height / x_scale)

        selected_size = self.calibration_size_var.get()
        self.ocr_calibration_data[selected_size]['width'] = base_width
        self.ocr_calibration_data[selected_size]['height'] = base_height
        self.log_msg(f"New size for {selected_size}: W={base_width}, H={base_height}")

        # Update label
        self.on_size_select(None)

        self.calibration_overlay.destroy()

    def calibrate_ocr_region(self):
        selected_region = self.calibration_region_var.get()
        if not selected_region:
            messagebox.showerror("Error", "Please select a region to calibrate.")
            return

        self.log_msg(f"Starting calibration for: {selected_region}")

        self.calibration_overlay = tk.Toplevel(self.root)
        self.calibration_overlay.overrideredirect(True)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.calibration_overlay.geometry(f"{screen_w}x{screen_h}+0+0")

        self.calibration_overlay.attributes('-alpha', 0.3)

        self.calibration_canvas = tk.Canvas(self.calibration_overlay, highlightthickness=0, bg='black')
        self.calibration_canvas.pack(fill=tk.BOTH, expand=True)

        # Draw current region
        rect_pct = self.ocr_calibration_data[selected_region]['rect']

        # Regions that require special scaling normalization to a 1920x1080 reference resolution
        station_scaled_regions = [
            "EDGalaxyMap.cartographics",
            "EDSystemMap.cartographics"
        ]

        # For display, we need to reverse the normalization for station-scaled regions
        if selected_region.startswith("EDStationServicesInShip.") or selected_region in station_scaled_regions:
            # The stored rect is normalized, so we scale it to the current screen resolution for an accurate display.
            scl_reg = reg_scale_for_station({'rect': rect_pct}, screen_w, screen_h)
            display_rect_pct = scl_reg['rect']
            self.log_msg(f"Applying station-style scaling for display of {selected_region}.")
        else:
            display_rect_pct = rect_pct

        x1 = display_rect_pct[0] * screen_w
        y1 = display_rect_pct[1] * screen_h
        x2 = display_rect_pct[2] * screen_w
        y2 = display_rect_pct[3] * screen_h
        self.calibration_canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2)

        self.start_x = None
        self.start_y = None
        self.current_rect = None

        self.calibration_canvas.bind("<ButtonPress-1>", self.on_calibration_press)
        self.calibration_canvas.bind("<B1-Motion>", self.on_calibration_drag)
        self.calibration_canvas.bind("<ButtonRelease-1>", self.on_calibration_release)
        self.calibration_overlay.bind("<Escape>", lambda e: self.calibration_overlay.destroy())

    def on_calibration_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.current_rect = self.calibration_canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='blue', width=2)

    def on_calibration_drag(self, event):
        if self.current_rect:
            self.calibration_canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)

    def _normalize_for_station(self, rect_pct, screen_w, screen_h):
        """
        Normalizes captured rectangle percentages for station-style regions
        to a 1920x1080 reference resolution.
        """
        ref_w = 1920.0
        ref_h = 1080.0

        if screen_w > 0 and screen_h > 0:
            x_scale = screen_w / ref_w
            y_scale = screen_h / ref_h

            if x_scale > 0 and y_scale > 0:
                top_pct = rect_pct[1]
                bottom_pct = rect_pct[3]
                
                # This formula "un-applies" the scaling of the current resolution and applies the reference
                # scaling, effectively normalizing the calibrated percentages to a 1920x1080 base.
                norm_top_pct = 0.5 + (top_pct - 0.5) * y_scale / x_scale
                norm_bottom_pct = 0.5 + (bottom_pct - 0.5) * y_scale / x_scale

                return [rect_pct[0], norm_top_pct, rect_pct[2], norm_bottom_pct]

        # Return original if scaling is not possible
        return rect_pct

    def on_calibration_release(self, event):
        end_x = event.x
        end_y = event.y

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        # Ensure coordinates are ordered correctly
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        right = max(self.start_x, end_x)
        bottom = max(self.start_y, end_y)

        left_pct = left / screen_w
        top_pct = top / screen_h
        right_pct = right / screen_w
        bottom_pct = bottom / screen_h

        selected_region = self.calibration_region_var.get()

        # Regions that require special scaling normalization to a 1920x1080 reference resolution
        station_scaled_regions = [
            "EDGalaxyMap.cartographics",
            "EDSystemMap.cartographics"
        ]

        # Get the raw percentages from the drawn box
        raw_rect_pct = [left_pct, top_pct, right_pct, bottom_pct]

        if selected_region.startswith("EDStationServicesInShip.") or selected_region in station_scaled_regions:
            new_rect_pct = self._normalize_for_station(raw_rect_pct, screen_w, screen_h)
            if new_rect_pct != raw_rect_pct:
                self.log_msg(f"Applying station-style normalization for {selected_region}.")
        else:
            new_rect_pct = raw_rect_pct

        self.ocr_calibration_data[selected_region]['rect'] = new_rect_pct
        self.log_msg(f"New rect for {selected_region}: [{new_rect_pct[0]:.4f}, {new_rect_pct[1]:.4f}, {new_rect_pct[2]:.4f}, {new_rect_pct[3]:.4f}]")

        # Update label
        self.on_region_select(None)

        self.calibration_overlay.destroy()

    def reset_all_calibrations(self):
        if messagebox.askyesno("Reset All Calibrations", "Are you sure you want to reset all OCR calibrations to their default values? This cannot be undone."):
            calibration_file = 'configs/ocr_calibration.json'
            if os.path.exists(calibration_file):
                os.remove(calibration_file)
                self.log_msg("Removed existing ocr_calibration.json.")

            # This will recreate the file with defaults
            self.load_ocr_calibration_data()

            # --- Repopulate UI ---
            # Clear current selections
            self.calibration_region_var.set('')
            self.calibration_size_var.set('')
            self.calibration_rect_label_var.set('')
            self.calibration_size_label_var.set('')

            # Repopulate region dropdown
            region_keys = sorted([key for key in self.ocr_calibration_data.keys() if '.size.' not in key and 'compass' not in key and 'target' not in key])
            self.calibration_region_combo['values'] = region_keys

            # Repopulate size dropdown
            size_keys = sorted([key for key in self.ocr_calibration_data.keys() if '.size.' in key])
            self.calibration_size_combo['values'] = size_keys

            self.log_msg("All OCR calibrations have been reset to default.")
            messagebox.showinfo("Reset Complete", "All calibrations have been reset to default. Please restart the application for all changes to take effect.")

    def create_wing_mining_tab(self, tab):
        tab.columnconfigure(0, weight=1)

        # Wing Mining settings block
        blk_wing_mining = ttk.LabelFrame(tab, text="Wing Mining Settings", padding=(10, 5))
        blk_wing_mining.grid(row=0, column=0, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_wing_mining.columnconfigure(1, weight=1)

        # Station A
        ttk.Label(blk_wing_mining, text="Station A:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_station_a'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_station_a'].grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(blk_wing_mining, text="Bertrandite FC:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_fc_a_bertrandite'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_fc_a_bertrandite'].grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(blk_wing_mining, text="Gold FC:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_fc_a_gold'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_fc_a_gold'].grid(row=2, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(blk_wing_mining, text="Indite FC:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_fc_a_indite'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_fc_a_indite'].grid(row=3, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(blk_wing_mining, text="Silver FC:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_fc_a_silver'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_fc_a_silver'].grid(row=4, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        # Station B
        ttk.Label(blk_wing_mining, text="Station B:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_station_b'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_station_b'].grid(row=5, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(blk_wing_mining, text="Bertrandite FC:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_fc_b_bertrandite'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_fc_b_bertrandite'].grid(row=6, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(blk_wing_mining, text="Gold FC:").grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_fc_b_gold'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_fc_b_gold'].grid(row=7, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(blk_wing_mining, text="Indite FC:").grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_fc_b_indite'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_fc_b_indite'].grid(row=8, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(blk_wing_mining, text="Silver FC:").grid(row=9, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_fc_b_silver'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_fc_b_silver'].grid(row=9, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(blk_wing_mining, text="Discord Data Path:").grid(row=10, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_discord_data_path'] = ttk.Entry(blk_wing_mining, width=30)
        self.entries['wing_mining_discord_data_path'].grid(row=10, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        # Separator
        ttk.Separator(blk_wing_mining, orient='horizontal').grid(row=11, column=0, columnspan=2, sticky='ew', pady=10)

        # Skip Depot Checkbox
        self.checkboxvar['WingMining_SkipDepotCheck'] = tk.BooleanVar()
        cb_skip_depot = ttk.Checkbutton(blk_wing_mining, text='Skip Mission Depot Check', variable=self.checkboxvar['WingMining_SkipDepotCheck'])
        cb_skip_depot.grid(row=11, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Mission Scanner Mode Checkbox
        self.checkboxvar['WingMining_MissionScannerMode'] = tk.BooleanVar()
        cb_mission_scanner_mode = ttk.Checkbutton(blk_wing_mining, text='Mission Scanner Mode', variable=self.checkboxvar['WingMining_MissionScannerMode'])
        cb_mission_scanner_mode.grid(row=12, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Mission Counter
        blk_mission_counter = ttk.LabelFrame(tab, text="Mission Counter", padding=(10, 5))
        blk_mission_counter.grid(row=1, column=0, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_mission_counter.columnconfigure(1, weight=1)

        ttk.Label(blk_mission_counter, text="Completed Missions:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.completed_missions_var = tk.StringVar()
        self.completed_missions_var.set("0")
        ttk.Label(blk_mission_counter, textvariable=self.completed_missions_var).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(blk_mission_counter, text="Set Mission Count:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.entries['wing_mining_mission_count'] = ttk.Entry(blk_mission_counter, width=10)
        self.entries['wing_mining_mission_count'].grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        btn_reset_counter = ttk.Button(blk_mission_counter, text="Reset Counter", command=self.reset_mission_counter)
        btn_reset_counter.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

        # Save Button
        btn_save = ttk.Button(tab, text='Save All Settings', command=self.save_settings, style="Accent.TButton")
        btn_save.grid(row=2, column=0, padx=10, pady=10, sticky=(tk.N, tk.E, tk.W, tk.S))

    def reset_mission_counter(self):
        self.completed_missions_var.set("0")
        self.entries['wing_mining_mission_count'].delete(0, tk.END)
        self.entries['wing_mining_mission_count'].insert(0, "0")
        self.config['WingMining_CompletedMissions'] = 0
        self.save_settings() # Save the updated config to the server
        self.log_msg("Wing Mining mission counter reset.")

    def gui_gen(self, win):

        modes_check_fields = ('FSD Route Assist', 'Supercruise Assist', 'Waypoint Assist', 'Robigo Assist', 'AFK Combat Assist', 'DSS Assist', 'Fleet Carrier Assist', 'Wing Mining Assist')
        ship_entry_fields = ('RollRate', 'PitchRate', 'YawRate')
        autopilot_entry_fields = ('Sun Bright Threshold', 'Nav Align Tries', 'Jump Tries', 'Docking Retries', 'Wait For Autodock')
        buttons_entry_fields = ('Start FSD', 'Start SC', 'Start Robigo', 'Stop All')
        refuel_entry_fields = ('Refuel Threshold', 'Scoop Timeout', 'Fuel Threshold Abort')
        overlay_entry_fields = ('X Offset', 'Y Offset', 'Font Size')


        # notebook pages
        nb = ttk.Notebook(win)
        nb.grid()
        page0 = ttk.Frame(nb)
        page1 = ttk.Frame(nb)
        page2 = ttk.Frame(nb)
        nb.add(page0, text="Main")  # main page
        nb.add(page1, text="Settings")  # options page
        nb.add(page2, text="Debug/Test")  # debug/test page
        page3 = ttk.Frame(nb)
        nb.add(page3, text="Calibration")
        self.create_calibration_tab(page3)

        page4 = ttk.Frame(nb)
        nb.add(page4, text="Waypoint Editor")
        self.waypoint_editor_tab = WaypointEditorTab(page4, self.autopilot_server_url)
        self.waypoint_editor_tab.frame.pack(fill="both", expand=True)

        page5 = ttk.Frame(nb)
        nb.add(page5, text="Wing Mining")
        self.create_wing_mining_tab(page5)


        # main options block
        blk_main = ttk.Frame(page0)
        blk_main.grid(row=0, column=0, padx=10, pady=5, sticky=(tk.E, tk.W))
        blk_main.columnconfigure([0, 1], weight=1, minsize=100, uniform="group1")

        # ap mode checkboxes block
        blk_modes = ttk.LabelFrame(blk_main, text="MODE", padding=(10, 5))
        blk_modes.grid(row=0, column=0, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.makeform(blk_modes, FORM_TYPE_CHECKBOX, modes_check_fields)

        # ship values block
        blk_ship = ttk.LabelFrame(blk_main, text="SHIP", padding=(10, 5))
        blk_ship.grid(row=0, column=1, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.entries['ship'] = self.makeform(blk_ship, FORM_TYPE_SPINBOX, ship_entry_fields, 0, 0.5)

        lbl_sun_pitch_up = ttk.Label(blk_ship, text='SunPitchUp +/- Time:')
        lbl_sun_pitch_up.grid(row=3, column=0, pady=3, sticky=tk.W)
        spn_sun_pitch_up = ttk.Spinbox(blk_ship, width=10, from_=-100, to=100, increment=0.5, justify=tk.RIGHT)
        spn_sun_pitch_up.grid(row=3, column=1, padx=2, pady=2, sticky=tk.E)
        spn_sun_pitch_up.bind('<FocusOut>', self.entry_update)
        self.entries['ship']['SunPitchUp+Time'] = spn_sun_pitch_up

        # Separator
        sep = ttk.Separator(blk_ship, orient='horizontal')
        sep.grid(row=4, column=0, columnspan=2, sticky='ew', pady=5)

        # Auto-Docking settings
        self.checkboxvar['AutoDockBoost'] = tk.BooleanVar()
        cb_auto_dock_boost = ttk.Checkbutton(blk_ship, text='Auto-Dock Boost', variable=self.checkboxvar['AutoDockBoost'], command=(lambda field='AutoDockBoost': self.check_cb(field)))
        cb_auto_dock_boost.grid(row=5, column=0, columnspan=2, sticky=tk.W)
        ToolTip(cb_auto_dock_boost, msg=self.tooltips['Auto-Dock Boost'], delay=1.0, bg="#808080", fg="#FFFFFF")

        lbl_fwd_time = ttk.Label(blk_ship, text='Auto-Dock Fwd Time:')
        lbl_fwd_time.grid(row=6, column=0, pady=3, sticky=tk.W)
        spn_fwd_time = ttk.Spinbox(blk_ship, width=10, from_=0, to=60, increment=1, justify=tk.RIGHT)
        spn_fwd_time.grid(row=6, column=1, padx=2, pady=2, sticky=tk.E)
        spn_fwd_time.bind('<FocusOut>', self.entry_update)
        self.entries['ship']['AutoDockForwardTime'] = spn_fwd_time
        ToolTip(lbl_fwd_time, msg=self.tooltips['Auto-Dock Fwd Time'], delay=1.0, bg="#808080", fg="#FFFFFF")

        lbl_delay_time = ttk.Label(blk_ship, text='Auto-Dock Delay:')
        lbl_delay_time.grid(row=7, column=0, pady=3, sticky=tk.W)
        spn_delay_time = ttk.Spinbox(blk_ship, width=10, from_=0, to=60, increment=1, justify=tk.RIGHT)
        spn_delay_time.grid(row=7, column=1, padx=2, pady=2, sticky=tk.E)
        spn_delay_time.bind('<FocusOut>', self.entry_update)
        self.entries['ship']['AutoDockDelayTime'] = spn_delay_time
        ToolTip(lbl_delay_time, msg=self.tooltips['Auto-Dock Delay'], delay=1.0, bg="#808080", fg="#FFFFFF")

        btn_tst_roll = ttk.Button(blk_ship, text='Test Roll Rate', command=self.ship_tst_roll)
        btn_tst_roll.grid(row=8, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))
        btn_tst_pitch = ttk.Button(blk_ship, text='Test Pitch Rate', command=self.ship_tst_pitch)
        btn_tst_pitch.grid(row=9, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))
        btn_tst_yaw = ttk.Button(blk_ship, text='Test Yaw Rate', command=self.ship_tst_yaw)
        btn_tst_yaw.grid(row=10, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))

        # waypoints button block
        blk_wp_buttons = ttk.LabelFrame(page0, text="Waypoints", padding=(10, 5))
        blk_wp_buttons.grid(row=1, column=0, padx=10, pady=5, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_wp_buttons.columnconfigure([0, 1], weight=1, minsize=100, uniform="group1")

        self.wp_filelabel = tk.StringVar()
        self.wp_filelabel.set("<no list loaded>")
        btn_wp_file = ttk.Button(blk_wp_buttons, textvariable=self.wp_filelabel, command=self.open_wp_file)
        btn_wp_file.grid(row=0, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))
        tip_wp_file = ToolTip(btn_wp_file, msg=self.tooltips['Waypoint List Button'], delay=1.0, bg="#808080", fg="#FFFFFF")

        btn_reset = ttk.Button(blk_wp_buttons, text='Reset List', command=self.reset_wp_file)
        btn_reset.grid(row=1, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))
        tip_reset = ToolTip(btn_reset, msg=self.tooltips['Reset Waypoint List'], delay=1.0, bg="#808080", fg="#FFFFFF")

        # log window
        log = ttk.LabelFrame(page0, text="LOG", padding=(10, 5))
        log.grid(row=3, column=0, padx=12, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        scrollbar = ttk.Scrollbar(log)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        mylist = tk.Listbox(log, width=72, height=10, yscrollcommand=scrollbar.set)
        mylist.grid(row=0, column=0)
        scrollbar.config(command=mylist.yview)

        # settings block
        blk_settings = ttk.Frame(page1)
        blk_settings.grid(row=0, column=0, padx=10, pady=5, sticky=(tk.E, tk.W))
        blk_main.columnconfigure([0, 1], weight=1, minsize=100, uniform="group1")

        # autopilot settings block
        blk_ap = ttk.LabelFrame(blk_settings, text="AUTOPILOT", padding=(10, 5))
        blk_ap.grid(row=0, column=0, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.entries['autopilot'] = self.makeform(blk_ap, FORM_TYPE_SPINBOX, autopilot_entry_fields)
        self.checkboxvar['Enable Randomness'] = tk.BooleanVar()
        cb_random = ttk.Checkbutton(blk_ap, text='Enable Randomness', variable=self.checkboxvar['Enable Randomness'], command=(lambda field='Enable Randomness': self.check_cb(field)))
        cb_random.grid(row=5, column=0, columnspan=2, sticky=(tk.W))
        self.checkboxvar['Activate Elite for each key'] = tk.BooleanVar()
        cb_activate_elite = ttk.Checkbutton(blk_ap, text='Activate Elite for each key', variable=self.checkboxvar['Activate Elite for each key'], command=(lambda field='Activate Elite for each key': self.check_cb(field)))
        cb_activate_elite.grid(row=6, column=0, columnspan=2, sticky=(tk.W))
        self.checkboxvar['Automatic logout'] = tk.BooleanVar()
        cb_logout = ttk.Checkbutton(blk_ap, text='Automatic logout', variable=self.checkboxvar['Automatic logout'], command=(lambda field='Automatic logout': self.check_cb(field)))
        cb_logout.grid(row=7, column=0, columnspan=2, sticky=(tk.W))

        # buttons settings block
        blk_buttons = ttk.LabelFrame(blk_settings, text="BUTTONS", padding=(10, 5))
        blk_buttons.grid(row=0, column=1, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_dss = ttk.Frame(blk_buttons)
        blk_dss.grid(row=0, column=0, columnspan=2, padx=0, pady=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        lb_dss = ttk.Label(blk_dss, text="DSS Button: ")
        lb_dss.grid(row=0, column=0, sticky=(tk.W))
        self.radiobuttonvar['dss_button'] = tk.StringVar()
        rb_dss_primary = ttk.Radiobutton(blk_dss, text="Primary", variable=self.radiobuttonvar['dss_button'], value="Primary", command=(lambda field='dss_button': self.check_cb(field)))
        rb_dss_primary.grid(row=0, column=1, sticky=(tk.W))
        rb_dss_secandary = ttk.Radiobutton(blk_dss, text="Secondary", variable=self.radiobuttonvar['dss_button'], value="Secondary", command=(lambda field='dss_button': self.check_cb(field)))
        rb_dss_secandary.grid(row=1, column=1, sticky=(tk.W))
        self.entries['buttons'] = self.makeform(blk_buttons, FORM_TYPE_ENTRY, buttons_entry_fields, 2)

        # refuel settings block
        blk_fuel = ttk.LabelFrame(blk_settings, text="FUEL", padding=(10, 5))
        blk_fuel.grid(row=1, column=0, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.entries['refuel'] = self.makeform(blk_fuel, FORM_TYPE_SPINBOX, refuel_entry_fields)

        # overlay settings block
        blk_overlay = ttk.LabelFrame(blk_settings, text="OVERLAY", padding=(10, 5))
        blk_overlay.grid(row=1, column=1, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.checkboxvar['Enable Overlay'] = tk.BooleanVar()
        cb_enable = ttk.Checkbutton(blk_overlay, text='Enable (requires restart)', variable=self.checkboxvar['Enable Overlay'], command=(lambda field='Enable Overlay': self.check_cb(field)))
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=(tk.W))
        self.entries['overlay'] = self.makeform(blk_overlay, FORM_TYPE_SPINBOX, overlay_entry_fields, 1, 1.0, 0.0, 3000.0)

        # tts / voice settings block
        blk_voice = ttk.LabelFrame(blk_settings, text="VOICE", padding=(10, 5))
        blk_voice.grid(row=2, column=0, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.checkboxvar['Enable Voice'] = tk.BooleanVar()
        cb_enable = ttk.Checkbutton(blk_voice, text='Enable', variable=self.checkboxvar['Enable Voice'], command=(lambda field='Enable Voice': self.check_cb(field)))
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=(tk.W))

        # Scanner settings block
        blk_voice = ttk.LabelFrame(blk_settings, text="ELW SCANNER", padding=(10, 5))
        blk_voice.grid(row=2, column=1, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.checkboxvar['ELW Scanner'] = tk.BooleanVar()
        cb_enable = ttk.Checkbutton(blk_voice, text='Enable', variable=self.checkboxvar['ELW Scanner'], command=(lambda field='ELW Scanner': self.check_cb(field)))
        cb_enable.grid(row=0, column=0, columnspan=2, sticky=(tk.W))

        # ocr settings block
        blk_ocr = ttk.LabelFrame(blk_settings, text="OCR", padding=(10, 5))
        blk_ocr.grid(row=1, column=2, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_ocr.columnconfigure(1, weight=1)
        lbl_ocr_url = ttk.Label(blk_ocr, text="Server URL:")
        lbl_ocr_url.grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        ent_ocr_url = ttk.Entry(blk_ocr, width=40)
        ent_ocr_url.grid(row=0, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))
        ent_ocr_url.bind('<FocusOut>', self.entry_update)
        if 'ocr' not in self.entries:
            self.entries['ocr'] = {}
        self.entries['ocr']['OcrServerUrl'] = ent_ocr_url

        # autopilot server settings block
        blk_ap_server = ttk.LabelFrame(blk_settings, text="Autopilot Server", padding=(10, 5))
        blk_ap_server.grid(row=0, column=2, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_ap_server.columnconfigure(1, weight=1)
        lbl_ap_server_url = ttk.Label(blk_ap_server, text="Server URL:")
        lbl_ap_server_url.grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        ent_ap_server_url = ttk.Entry(blk_ap_server, width=40, textvariable=self.autopilot_server_url)
        ent_ap_server_url.grid(row=0, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))

        # discord settings block
        blk_discord = ttk.LabelFrame(blk_settings, text="DISCORD", padding=(10, 5))
        blk_discord.grid(row=2, column=2, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.checkboxvar['DiscordWebhook'] = tk.BooleanVar()
        cb_enable_discord = ttk.Checkbutton(blk_discord, text='Enable Webhook', variable=self.checkboxvar['DiscordWebhook'], command=(lambda field='DiscordWebhook': self.check_cb(field)))
        cb_enable_discord.grid(row=0, column=0, columnspan=2, sticky=(tk.W))
        self.entries['discord'] = self.makeform(blk_discord, FORM_TYPE_ENTRY, ('Webhook URL', 'User ID'), 1)


        # settings button block
        blk_settings_buttons = ttk.Frame(page1)
        blk_settings_buttons.grid(row=3, column=0, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_settings_buttons.columnconfigure([0, 1], weight=1, minsize=100)
        btn_save = ttk.Button(blk_settings_buttons, text='Save All Settings', command=self.save_settings, style="Accent.TButton")
        btn_save.grid(row=0, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))

        # File Actions
        blk_file_actions = ttk.LabelFrame(page2, text="File Actions", padding=(10, 5))
        blk_file_actions.grid(row=0, column=0, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.checkboxvar['Enable CV View'] = tk.IntVar()
        self.checkboxvar['Enable CV View'].set(int(self.config.get('Enable_CV_View', 0)))
        cb_enable_cv_view = ttk.Checkbutton(blk_file_actions, text='Enable CV View', variable=self.checkboxvar['Enable CV View'], command=(lambda field='Enable CV View': self.check_cb(field)))
        cb_enable_cv_view.grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        btn_restart = ttk.Button(blk_file_actions, text="Restart", command=self.restart_program)
        btn_restart.grid(row=3, column=0, padx=2, pady=2, sticky=tk.W)
        btn_exit = ttk.Button(blk_file_actions, text="Exit", command=self.close_window)
        btn_exit.grid(row=4, column=0, padx=2, pady=2, sticky=tk.W)


        # Help Actions
        blk_help_actions = ttk.LabelFrame(page2, text="Help Actions", padding=(10, 5))
        blk_help_actions.grid(row=0, column=1, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        btn_check_updates = ttk.Button(blk_help_actions, text="Check for Updates", command=self.check_updates)
        btn_check_updates.grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        btn_view_changelog = ttk.Button(blk_help_actions, text="View Changelog", command=self.open_changelog)
        btn_view_changelog.grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        btn_join_discord = ttk.Button(blk_help_actions, text="Join Discord", command=self.open_discord)
        btn_join_discord.grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        btn_about = ttk.Button(blk_help_actions, text="About", command=self.about)
        btn_about.grid(row=3, column=0, padx=2, pady=2, sticky=tk.W)

        # debug block
        blk_debug = ttk.Frame(page2)
        blk_debug.grid(row=1, column=0, padx=10, pady=5, sticky=(tk.E, tk.W))
        blk_debug.columnconfigure([0, 1], weight=1, minsize=100, uniform="group2")

        # debug settings block
        blk_debug_settings = ttk.LabelFrame(blk_debug, text="DEBUG", padding=(10, 5))
        blk_debug_settings.grid(row=0, column=0, padx=2, pady=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.radiobuttonvar['debug_mode'] = tk.StringVar()
        rb_debug_debug = ttk.Radiobutton(blk_debug_settings, text="Debug + Info + Errors", variable=self.radiobuttonvar['debug_mode'], value="Debug", command=(lambda field='debug_mode': self.check_cb(field)))
        rb_debug_debug.grid(row=0, column=1, columnspan=2, sticky=(tk.W))
        rb_debug_info = ttk.Radiobutton(blk_debug_settings, text="Info + Errors", variable=self.radiobuttonvar['debug_mode'], value="Info", command=(lambda field='debug_mode': self.check_cb(field)))
        rb_debug_info.grid(row=1, column=1, columnspan=2, sticky=(tk.W))
        rb_debug_error = ttk.Radiobutton(blk_debug_settings, text="Errors only (default)", variable=self.radiobuttonvar['debug_mode'], value="Error", command=(lambda field='debug_mode': self.check_cb(field)))
        rb_debug_error.grid(row=2, column=1, columnspan=2, sticky=(tk.W))
        btn_open_logfile = ttk.Button(blk_debug_settings, text='Open Log File', command=self.open_logfile)
        btn_open_logfile.grid(row=3, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))
        self.checkboxvar['DisableLogFile'] = tk.BooleanVar()
        cb_disable_log = ttk.Checkbutton(blk_debug_settings, text='Disable Log File', variable=self.checkboxvar['DisableLogFile'], command=(lambda field='DisableLogFile': self.check_cb(field)))
        cb_disable_log.grid(row=4, column=0, columnspan=2, sticky=(tk.W))

        # debug settings block
        blk_single_waypoint_asst = ttk.LabelFrame(page2, text="Single Waypoint Assist", padding=(10, 5))
        blk_single_waypoint_asst.grid(row=1, column=1, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_single_waypoint_asst.columnconfigure(0, weight=1, minsize=10, uniform="group1")
        blk_single_waypoint_asst.columnconfigure(1, weight=3, minsize=10, uniform="group1")

        lbl_system = ttk.Label(blk_single_waypoint_asst, text='System:')
        lbl_system.grid(row=0, column=0, padx=2, pady=2, columnspan=1, sticky=(tk.N, tk.E, tk.W, tk.S))
        txt_system = ttk.Entry(blk_single_waypoint_asst, textvariable=self.single_waypoint_system)
        txt_system.grid(row=0, column=1, padx=2, pady=2, columnspan=1, sticky=(tk.N, tk.E, tk.W, tk.S))
        lbl_station = ttk.Label(blk_single_waypoint_asst, text='Station:')
        lbl_station.grid(row=1, column=0, padx=2, pady=2, columnspan=1, sticky=(tk.N, tk.E, tk.W, tk.S))
        txt_station = ttk.Entry(blk_single_waypoint_asst, textvariable=self.single_waypoint_station)
        txt_station.grid(row=1, column=1, padx=2, pady=2, columnspan=1, sticky=(tk.N, tk.E, tk.W, tk.S))
        self.checkboxvar['Single Waypoint Assist'] = tk.BooleanVar()
        cb_single_waypoint = ttk.Checkbutton(blk_single_waypoint_asst, text='Single Waypoint Assist', variable=self.checkboxvar['Single Waypoint Assist'], command=(lambda field='Single Waypoint Assist': self.check_cb(field)))
        cb_single_waypoint.grid(row=2, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))

        lbl_tce = ttk.Label(blk_single_waypoint_asst, text='Trade Computer Extension (TCE)', style="Link.TLabel")
        lbl_tce.bind("<Button-1>", lambda e: hyperlink_callback("https://forums.frontier.co.uk/threads/trade-computer-extension-mk-ii.223056/"))
        lbl_tce.grid(row=3, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))
        lbl_tce_dest = ttk.Label(blk_single_waypoint_asst, text='TCE Dest json:')
        lbl_tce_dest.grid(row=4, column=0, padx=2, pady=2, columnspan=1, sticky=(tk.N, tk.E, tk.W, tk.S))
        txt_tce_dest = ttk.Entry(blk_single_waypoint_asst, textvariable=self.TCE_Destination_Filepath)
        txt_tce_dest.bind('<FocusOut>', self.entry_update)
        txt_tce_dest.grid(row=4, column=1, padx=2, pady=2, columnspan=1, sticky=(tk.N, tk.E, tk.W, tk.S))

        btn_load_tce = ttk.Button(blk_single_waypoint_asst, text='Load TCE Destination', command=self.load_tce_dest)
        btn_load_tce.grid(row=5, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))

        blk_debug_buttons = ttk.Frame(page2)
        blk_debug_buttons.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        blk_debug_buttons.columnconfigure([0, 1], weight=1, minsize=100)

        self.checkboxvar['Debug Overlay'] = tk.BooleanVar()
        cb_debug_overlay = ttk.Checkbutton(blk_debug_buttons, text='Debug Overlay', variable=self.checkboxvar['Debug Overlay'], command=(lambda field='Debug Overlay': self.check_cb(field)))
        cb_debug_overlay.grid(row=6, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))

        btn_save = ttk.Button(blk_debug_buttons, text='Save All Settings', command=self.save_settings, style="Accent.TButton")
        btn_save.grid(row=7, column=0, padx=2, pady=2, columnspan=2, sticky=(tk.N, tk.E, tk.W, tk.S))

        # Statusbar
        statusbar = ttk.Frame(win)
        statusbar.grid(row=4, column=0)
        self.status = ttk.Label(win, text="Status: ", relief=tk.SUNKEN, anchor=tk.W, justify=tk.LEFT, width=29)
        self.jumpcount = ttk.Label(statusbar, text="<info> ", relief=tk.SUNKEN, anchor=tk.W, justify=tk.LEFT, width=40)
        self.status.pack(in_=statusbar, side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.jumpcount.pack(in_=statusbar, side=tk.RIGHT, fill=tk.Y, expand=False)

        return mylist

    def restart_program(self):
        logger.debug("Entered: restart_program")
        print("restart now")

        self.stop_all_assists()
        # self.ed_ap.quit()
        sleep(0.1)

        import sys
        print("argv was", sys.argv)
        print("sys.executable was", sys.executable)
        print("restart now")

        import os
        os.execv(sys.executable, ['python'] + sys.argv)

def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        # Set the title bar color to the background color on Windows 11 for better appearance
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")

        # A hacky way to update the title bar's color on Windows 10 (it doesn't update instantly like on Windows 11)
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

def main():
    #   handle = win32gui.FindWindow(0, "Elite - Dangerous (CLIENT)")
    #   if handle != None:
    #       win32gui.SetForegroundWindow(handle)  # put the wind8ow in foreground

    root = tk.Tk()
    app = APGui(root)

    sv_ttk.set_theme("dark")

    # Remove focus outline from tabs by setting focuscolor to the background color
    style = ttk.Style()
    bg_color = "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa"
    style.configure("TNotebook.Tab", focuscolor=bg_color)

    if sys.platform == "win32":
        apply_theme_to_titlebar(root)
    root.mainloop()


if __name__ == "__main__":
    main()
