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
log_display = ui.log(max_lines=20)

# Centralized status label
status_label = ui.label("Status: Idle")

# UI elements that need to be updated by callbacks
assist_checkboxes = {}

def callback(msg, body=None):
    """Callback function to handle messages from EDAutopilot."""
    if msg == 'log' or msg == 'log+vce':
        message = datetime.now().strftime("%H:%M:%S: ") + body
        log_display.push(message)
    elif msg == 'statusline':
        status_label.set_text("Status: " + body)
        log_display.push(f"Status update: {body}")
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
    else:
        print(f"Unhandled Callback: {msg}, {body}")

# Instantiate EDAutopilot
ed_ap = EDAutopilot(cb=callback, use_gpu_ocr=app_state['ocr_calibration_data'].get('use_gpu_ocr', False))

@ui.page('/')
def index_page() -> None:
    with theme.frame('Main', status_label=status_label):
        # Create checkboxes here so they can be accessed by the callback
        assist_checkboxes['FSD Route Assist'] = ui.checkbox('FSD Route Assist', on_change=lambda e: ed_ap.set_fsd_assist(e.value))
        assist_checkboxes['Supercruise Assist'] = ui.checkbox('Supercruise Assist', on_change=lambda e: ed_ap.set_sc_assist(e.value))
        assist_checkboxes['Waypoint Assist'] = ui.checkbox('Waypoint Assist', on_change=lambda e: ed_ap.set_waypoint_assist(e.value))
        assist_checkboxes['Robigo Assist'] = ui.checkbox('Robigo Assist', on_change=lambda e: ed_ap.set_robigo_assist(e.value))
        assist_checkboxes['AFK Combat Assist'] = ui.checkbox('AFK Combat Assist', on_change=lambda e: ed_ap.set_afk_combat_assist(e.value))
        assist_checkboxes['DSS Assist'] = ui.checkbox('DSS Assist', on_change=lambda e: ed_ap.set_dss_assist(e.value))
        assist_checkboxes['Fleet Carrier Assist'] = ui.checkbox('Fleet Carrier Assist', on_change=lambda e: ed_ap.set_fc_assist(e.value))
        assist_checkboxes['Wing Mining Assist'] = ui.checkbox('Wing Mining Assist', on_change=lambda e: ed_ap.set_wing_mining_assist(e.value))

        create_main_tab(ed_ap, log_display, assist_checkboxes)

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

ui.run(title='EDAP')
