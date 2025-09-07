import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import theme
from nicegui import ui
from main_tab import create_main_tab
from settings_tab import create_settings_tab
from debug_tab import create_debug_tab
from calibration_tab import create_calibration_tab
from waypoint_editor_tab import create_waypoint_editor_tab
from wing_mining_tab import create_wing_mining_tab
from ED_AP import EDAutopilot
from datetime import datetime
import json
import os
import collections

# App state
app_state = {
    'ocr_calibration_data': {},
}

def load_ocr_calibration_data():
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
        with open(calibration_file, 'w') as f:
            json.dump(default_regions, f, indent=4)
        app_state['ocr_calibration_data'] = default_regions
    else:
        with open(calibration_file, 'r') as f:
            app_state['ocr_calibration_data'] = json.load(f)
        updated = False
        for key, value in default_regions.items():
            if key not in app_state['ocr_calibration_data']:
                app_state['ocr_calibration_data'][key] = value
                updated = True
        if updated:
            save_ocr_calibration_data()

def save_ocr_calibration_data():
    calibration_file = 'configs/ocr_calibration.json'
    with open(calibration_file, 'w') as f:
        json.dump(app_state['ocr_calibration_data'], f, indent=4)

app_state['load_ocr_calibration_data'] = load_ocr_calibration_data
app_state['save_ocr_calibration_data'] = save_ocr_calibration_data
load_ocr_calibration_data()


# Centralized log display
log_history = collections.deque(maxlen=100)
log_container = {'log': None, 'history': log_history}

# Centralized status label
status_label = ui.label("Status: Idle")

# UI elements that need to be updated by callbacks
assist_checkboxes = {}
ship_data = {}

def callback(msg, body=None):
    """Callback function to handle messages from EDAutopilot."""
    if msg == 'log' or msg == 'log+vce':
        message = datetime.now().strftime("%H:%M:%S: ") + body
        log_container['history'].append(message)
        if log_container['log']:
            log_container['log'].push(message)
    elif msg == 'statusline':
        status_label.set_text("Status: " + body)
        message = f"Status update: {body}"
        log_container['history'].append(message)
        if log_container['log']:
            log_container['log'].push(message)
    elif msg == 'fsd_stop':
        if 'FSD Route Assist' in assist_checkboxes: assist_checkboxes['FSD Route Assist'].value = False
    elif msg == 'sc_stop':
        if 'Supercruise Assist' in assist_checkboxes: assist_checkboxes['Supercruise Assist'].value = False
    elif msg == 'waypoint_stop':
        if 'Waypoint Assist' in assist_checkboxes: assist_checkboxes['Waypoint Assist'].value = False
    elif msg == 'robigo_stop':
        if 'Robigo Assist' in assist_checkboxes: assist_checkboxes['Robigo Assist'].value = False
    elif msg == 'afk_stop':
        if 'AFK Combat Assist' in assist_checkboxes: assist_checkboxes['AFK Combat Assist'].value = False
    elif msg == 'dss_stop':
        if 'DSS Assist' in assist_checkboxes: assist_checkboxes['DSS Assist'].value = False
    elif msg == 'fc_stop':
        if 'Fleet Carrier Assist' in assist_checkboxes: assist_checkboxes['Fleet Carrier Assist'].value = False
    elif msg == 'wing_mining_stop':
        if 'Wing Mining Assist' in assist_checkboxes: assist_checkboxes['Wing Mining Assist'].value = False
    elif msg == 'update_ship_cfg':
        ship_data['rollrate'] = ed_ap.rollrate
        ship_data['pitchrate'] = ed_ap.pitchrate
        ship_data['yawrate'] = ed_ap.yawrate
        ship_data['sunpitchuptime'] = ed_ap.sunpitchuptime
        ship_data['autodock_boost'] = ed_ap.autodock_boost
        ship_data['autodock_forward_time'] = ed_ap.autodock_forward_time
        ship_data['autodock_delay_time'] = ed_ap.autodock_delay_time
    else:
        print(f"Unhandled Callback: {msg}, {body}")

# Instantiate EDAutopilot
ed_ap = EDAutopilot(cb=callback, use_gpu_ocr=app_state['ocr_calibration_data'].get('use_gpu_ocr', False))

# Initialize ship_data with default values from ed_ap
ship_data = {
    'rollrate': ed_ap.rollrate,
    'pitchrate': ed_ap.pitchrate,
    'yawrate': ed_ap.yawrate,
    'sunpitchuptime': ed_ap.sunpitchuptime,
    'autodock_boost': ed_ap.autodock_boost,
    'autodock_forward_time': ed_ap.autodock_forward_time,
    'autodock_delay_time': ed_ap.autodock_delay_time,
}

@ui.page('/')
def index_page() -> None:
    with theme.frame('Main', status_label=status_label):
        ship_controls = {}
        create_main_tab(ed_ap, log_container, assist_checkboxes, ship_controls, ship_data)

@ui.page('/settings')
def settings_page() -> None:
    with theme.frame('Settings', status_label=status_label):
        create_settings_tab(ed_ap)

@ui.page('/debug')
def debug_page() -> None:
    with theme.frame('Debug/Test', status_label=status_label):
        create_debug_tab(ed_ap)

@ui.page('/calibration')
def calibration_page() -> None:
    with theme.frame('Calibration', status_label=status_label):
        create_calibration_tab(app_state, ed_ap)

@ui.page('/waypoint-editor')
def waypoint_editor_page() -> None:
    with theme.frame('Waypoint Editor', status_label=status_label):
        create_waypoint_editor_tab(ed_ap.waypoint)

@ui.page('/wing-mining')
def wing_mining_page() -> None:
    with theme.frame('Wing Mining', status_label=status_label):
        create_wing_mining_tab(ed_ap)

def load_server_config():
    config_file = 'configs/nicegui.json'
    defaults = {'server': {'host': '0.0.0.0', 'port': 8080}}
    if not os.path.exists(config_file):
        with open(config_file, 'w') as f:
            json.dump(defaults, f, indent=4)
        return defaults['server']
    else:
        with open(config_file, 'r') as f:
            config = json.load(f)
        # Merge with defaults to ensure all keys are present
        if 'server' not in config:
            config['server'] = defaults['server']
        for key, value in defaults['server'].items():
            if key not in config['server']:
                config['server'][key] = value

        # Save back the updated config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)

        return config['server']

server_config = load_server_config()
ui.run(title='EDAP', host=server_config['host'], port=server_config['port'])
