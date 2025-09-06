"""
File: NiceGUI.py

Description:
New user interface for controlling the ED Autopilot, built with NiceGUI.
"""

from nicegui import ui

def main():
    """The main function to create the GUI."""
    with ui.header(elevated=True):
        ui.label("ED Autopilot")

    with ui.tabs().classes('w-full') as tabs:
        main_tab = ui.tab('Main')
        settings_tab = ui.tab('Settings')
        debug_tab = ui.tab('Debug/Test')
        calibration_tab = ui.tab('Calibration')
        waypoint_editor_tab = ui.tab('Waypoint Editor')
        wing_mining_tab = ui.tab('Wing Mining')

    with ui.tab_panels(tabs, value=main_tab).classes('w-full'):
        with ui.tab_panel(main_tab):
            with ui.row():
                with ui.card().classes('w-1/2'):
                    ui.label("MODE").classes('text-lg font-bold')
                    ui.checkbox('FSD Route Assist')
                    ui.checkbox('Supercruise Assist')
                    ui.checkbox('Waypoint Assist')
                    ui.checkbox('Robigo Assist')
                    ui.checkbox('AFK Combat Assist')
                    ui.checkbox('DSS Assist')
                    ui.checkbox('Fleet Carrier Assist')
                    ui.checkbox('Wing Mining Assist')
                with ui.card().classes('w-1/2'):
                    ui.label("SHIP").classes('text-lg font-bold')
                    ui.number(label='RollRate', value=0.0, format='%.2f')
                    ui.number(label='PitchRate', value=0.0, format='%.2f')
                    ui.number(label='YawRate', value=0.0, format='%.2f')
                    ui.number(label='SunPitchUp +/- Time:', value=0.0, format='%.2f')
                    ui.separator()
                    ui.checkbox('Auto-Dock Boost')
                    ui.number(label='Auto-Dock Fwd Time:', value=0)
                    ui.number(label='Auto-Dock Delay:', value=0)
                    with ui.row():
                        ui.button('Test Roll Rate')
                        ui.button('Test Pitch Rate')
                        ui.button('Test Yaw Rate')

            with ui.card().classes('w-full'):
                ui.label("Waypoints").classes('text-lg font-bold')
                with ui.row():
                    ui.button('<no list loaded>')
                    ui.button('Reset List')

            with ui.card().classes('w-full'):
                ui.label("LOG").classes('text-lg font-bold')
                log = ui.log(max_lines=10).classes('w-full h-40')


        with ui.tab_panel(settings_tab):
            with ui.row():
                with ui.card():
                    ui.label("AUTOPILOT").classes('text-lg font-bold')
                    ui.number(label='Sun Bright Threshold', value=0)
                    ui.number(label='Nav Align Tries', value=0)
                    ui.number(label='Jump Tries', value=0)
                    ui.number(label='Docking Retries', value=0)
                    ui.number(label='Wait For Autodock', value=0)
                    ui.checkbox('Enable Randomness')
                    ui.checkbox('Activate Elite for each key')
                    ui.checkbox('Automatic logout')

                with ui.card():
                    ui.label("BUTTONS").classes('text-lg font-bold')
                    ui.label("DSS Button:")
                    ui.radio(['Primary', 'Secondary'], value='Primary')
                    ui.input(label='Start FSD')
                    ui.input(label='Start SC')
                    ui.input(label='Start Robigo')
                    ui.input(label='Stop All')

                with ui.card():
                    ui.label("FUEL").classes('text-lg font-bold')
                    ui.number(label='Refuel Threshold', value=0)
                    ui.number(label='Scoop Timeout', value=0)
                    ui.number(label='Fuel Threshold Abort', value=0)

            with ui.row():
                with ui.card():
                    ui.label("OVERLAY").classes('text-lg font-bold')
                    ui.checkbox('Enable (requires restart)')
                    ui.number(label='X Offset', value=0)
                    ui.number(label='Y Offset', value=0)
                    ui.number(label='Font Size', value=0)

                with ui.card():
                    ui.label("VOICE").classes('text-lg font-bold')
                    ui.checkbox('Enable')

                with ui.card():
                    ui.label("ELW SCANNER").classes('text-lg font-bold')
                    ui.checkbox('Enable')

                with ui.card():
                    ui.label("OCR").classes('text-lg font-bold')
                    ui.input(label='Server URL')

                with ui.card():
                    ui.label("DISCORD").classes('text-lg font-bold')
                    ui.checkbox('Enable Webhook')
                    ui.input(label='Webhook URL')
                    ui.input(label='User ID')

            with ui.row():
                ui.button('Save All Settings')

        with ui.tab_panel(debug_tab):
            with ui.row():
                with ui.card():
                    ui.label("File Actions").classes('text-lg font-bold')
                    ui.checkbox('Enable CV View')
                    ui.button('Restart')
                    ui.button('Exit')
                with ui.card():
                    ui.label("Help Actions").classes('text-lg font-bold')
                    ui.button('Check for Updates')
                    ui.button('View Changelog')
                    ui.button('Join Discord')
                    ui.button('About')
            with ui.row():
                with ui.card():
                    ui.label("DEBUG").classes('text-lg font-bold')
                    ui.radio(['Debug + Info + Errors', 'Info + Errors', 'Errors only (default)'], value='Errors only (default)')
                    ui.button('Open Log File')
                    ui.checkbox('Disable Log File')
                with ui.card():
                    ui.label("Single Waypoint Assist").classes('text-lg font-bold')
                    ui.input(label='System')
                    ui.input(label='Station')
                    ui.checkbox('Single Waypoint Assist')
                    ui.link('Trade Computer Extension (TCE)', 'https://forums.frontier.co.uk/threads/trade-computer-extension-mk-ii.223056/')
                    ui.input(label='TCE Dest json:')
                    ui.button('Load TCE Destination')
            with ui.row():
                with ui.card():
                    ui.checkbox('Debug Overlay')
                    ui.button('Save All Settings')

        with ui.tab_panel(calibration_tab):
            with ui.card():
                ui.label("Region Calibration").classes('text-lg font-bold')
                ui.select(options=[], label='Region')
                ui.label("Rect: [0.0000, 0.0000, 0.0000, 0.0000]")
                ui.button('Calibrate Region')
            with ui.card():
                ui.label("Size Calibration").classes('text-lg font-bold')
                ui.select(options=[], label='Size')
                ui.label("W/H: W: 0, H: 0")
                ui.button('Calibrate Size')
            with ui.card():
                ui.label("Other Calibrations").classes('text-lg font-bold')
                with ui.row():
                    ui.button('Calibrate Compass')
                    ui.button('Calibrate Target')
                    ui.checkbox('CUDA OCR')
            with ui.card():
                ui.label("Value Calibration").classes('text-lg font-bold')
                ui.number(label='Nav Panel Deskew Angle', value=0.0, format='%.1f')
            with ui.card():
                with ui.row():
                    ui.button('Save All Calibrations')
                    ui.button('Reset All to Default')

        with ui.tab_panel(waypoint_editor_tab):
            with ui.row():
                ui.button('New')
                ui.button('Open')
                ui.button('Save')
                ui.button('Save As')
                ui.button('Import Spansh CSV')
                ui.button('Import from Inara')

            with ui.row():
                with ui.card().classes('w-2/3'):
                    ui.label("Waypoints").classes('text-lg font-bold')
                    # Placeholder for waypoints list
                    ui.table(columns=[
                        {'name': 'system_name', 'label': 'System Name', 'field': 'system_name'},
                        {'name': 'station_name', 'label': 'Station Name', 'field': 'station_name'},
                        {'name': 'skip', 'label': 'Skip', 'field': 'skip'},
                        {'name': 'completed', 'label': 'Completed', 'field': 'completed'},
                    ], rows=[])
                with ui.card().classes('w-1/3'):
                    ui.button('Up')
                    ui.button('Down')
                    ui.button('Add')
                    ui.button('Del')

            with ui.card():
                ui.label("Waypoint Options").classes('text-lg font-bold')
                with ui.card():
                    ui.label("Station Options").classes('text-lg font-bold')
                    with ui.row():
                        ui.select(options=["", "Favorite", "System", "Body", "Station", "Settlement"], label="Galaxy Bookmark Type")
                        ui.number(label="Galaxy Bookmark Number")
                    with ui.row():
                        ui.select(options=["", "Favorite", "Body", "Station", "Settlement", "Nav-OCR", "Navigation Panel"], label="System Bookmark Type")
                        ui.number(label="System Bookmark Number")
                    with ui.row():
                        ui.checkbox("Update Commodity Count")
                        ui.checkbox("Fleet Carrier Transfer")
                        ui.checkbox("Scan Missions")

            with ui.row():
                with ui.card():
                    ui.label("Buy Commodities").classes('text-lg font-bold')
                    # Placeholder for buy commodities list
                    ui.table(columns=[
                        {'name': 'name', 'label': 'Name', 'field': 'name'},
                        {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity'},
                    ], rows=[])
                    with ui.row():
                        ui.button('Up')
                        ui.button('Down')
                        ui.button('Add')
                        ui.button('Del')

                with ui.card():
                    ui.label("Sell Commodities").classes('text-lg font-bold')
                    # Placeholder for sell commodities list
                    ui.table(columns=[
                        {'name': 'name', 'label': 'Name', 'field': 'name'},
                        {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity'},
                    ], rows=[])
                    with ui.row():
                        ui.button('Up')
                        ui.button('Down')
                        ui.button('Add')
                        ui.button('Del')

        with ui.tab_panel(wing_mining_tab):
            with ui.card():
                ui.label("Wing Mining Settings").classes('text-lg font-bold')
                ui.input(label='Station A')
                ui.input(label='Bertrandite FC')
                ui.input(label='Gold FC')
                ui.input(label='Indite FC')
                ui.input(label='Silver FC')
                ui.separator()
                ui.input(label='Station B')
                ui.input(label='Bertrandite FC')
                ui.input(label='Gold FC')
                ui.input(label='Indite FC')
                ui.input(label='Silver FC')
                ui.separator()
                ui.input(label='Discord Data Path')
                ui.checkbox('Skip Mission Depot Check')
                ui.checkbox('Mission Scanner Mode')
            with ui.card():
                ui.label("Mission Counter").classes('text-lg font-bold')
                ui.label("Completed Missions: 0")
                ui.input(label='Set Mission Count')
                ui.button('Reset Counter')

            ui.button('Save All Settings')


if __name__ in {"__main__", "__mp_main__"}:
    main()
    ui.run(title="EDAutopilot")
