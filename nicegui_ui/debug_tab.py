from nicegui import ui

def create_debug_tab(ed_ap):
    with ui.row():
        with ui.card():
            ui.label('File Actions').classes('text-h6')
            ui.checkbox('Enable CV View', value=ed_ap.config.get('Enable_CV_View', False), on_change=lambda e: ed_ap.config.update({'Enable_CV_View': e.value}))
            ui.button('Restart', on_click=lambda: ed_ap.restart_program())
            ui.button('Exit', on_click=lambda: ed_ap.quit())

        with ui.card():
            ui.label('Help Actions').classes('text-h6')
            ui.button('Check for Updates', on_click=lambda: ed_ap.check_updates())
            ui.button('View Changelog', on_click=lambda: ed_ap.open_changelog())
            ui.button('Join Discord', on_click=lambda: ed_ap.open_discord())
            ui.button('About', on_click=lambda: ed_ap.about())

    with ui.row():
        with ui.card():
            ui.label('DEBUG').classes('text-h6')

            def set_log_level(value):
                if value == "Debug":
                    ed_ap.set_log_debug(True)
                elif value == "Info":
                    ed_ap.set_log_info(True)
                else:
                    ed_ap.set_log_error(True)

            ui.radio(['Debug', 'Info', 'Error'], value='Error', on_change=lambda e: set_log_level(e.value))
            ui.label('Log Level')
            ui.button('Open Log File', on_click=lambda: ed_ap.open_logfile())
            ui.checkbox('Disable Log File', value=ed_ap.config.get('DisableLogFile', False), on_change=lambda e: ed_ap.config.update({'DisableLogFile': e.value}))

        with ui.card():
            ui.label('Single Waypoint Assist').classes('text-h6')
            system_entry = ui.input('System')
            station_entry = ui.input('Station')

            def start_single_waypoint():
                system = system_entry.value
                station = station_entry.value
                if system != "" or station != "":
                    ed_ap.set_single_waypoint_assist(system, station, True)

            ui.checkbox('Single Waypoint Assist', on_change=lambda e: start_single_waypoint() if e.value else ed_ap.set_single_waypoint_assist("", "", False))
            ui.input('TCE Dest json:', value=ed_ap.config.get('TCEDestinationFilepath', ''), on_change=lambda e: ed_ap.config.update({'TCEDestinationFilepath': e.value}))
            ui.button('Load TCE Destination', on_click=lambda: ed_ap.load_tce_dest())

    with ui.row():
        with ui.card():
            ui.label('Debug Buttons').classes('text-h6')
            ui.checkbox('Debug Overlay', value=ed_ap.config.get('DebugOverlay', False), on_change=lambda e: ed_ap.config.update({'DebugOverlay': e.value}))
            ui.button('Save All Settings', on_click=lambda: (ed_ap.update_config(), ed_ap.update_ship_configs(), ui.notify('Settings Saved!')))
