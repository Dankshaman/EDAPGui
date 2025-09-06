from nicegui import ui

def create_main_tab(ed_ap, log_display, assist_checkboxes):
    with ui.row():
        with ui.card().classes('w-1/2'):
            ui.label('MODE').classes('text-h6')
            for checkbox in assist_checkboxes.values():
                checkbox  # This will render the checkbox

        with ui.card().classes('w-1/2'):
            ui.label('SHIP').classes('text-h6')
            ui.number('RollRate', value=ed_ap.rollrate, on_change=lambda e: setattr(ed_ap, 'rollrate', e.value))
            ui.number('PitchRate', value=ed_ap.pitchrate, on_change=lambda e: setattr(ed_ap, 'pitchrate', e.value))
            ui.number('YawRate', value=ed_ap.yawrate, on_change=lambda e: setattr(ed_ap, 'yawrate', e.value))
            ui.number('SunPitchUp+Time', value=ed_ap.sunpitchuptime, on_change=lambda e: setattr(ed_ap, 'sunpitchuptime', e.value))

            ui.separator()

            ui.checkbox('Auto-Dock Boost', value=ed_ap.autodock_boost, on_change=lambda e: setattr(ed_ap, 'autodock_boost', e.value))
            ui.number('Auto-Dock Fwd Time', value=ed_ap.autodock_forward_time, on_change=lambda e: setattr(ed_ap, 'autodock_forward_time', e.value))
            ui.number('Auto-Dock Delay', value=ed_ap.autodock_delay_time, on_change=lambda e: setattr(ed_ap, 'autodock_delay_time', e.value))

            ui.button('Test Roll Rate', on_click=ed_ap.ship_tst_roll)
            ui.button('Test Pitch Rate', on_click=ed_ap.ship_tst_pitch)
            ui.button('Test Yaw Rate', on_click=ed_ap.ship_tst_yaw)

    with ui.row():
        with ui.card().classes('w-full'):
            ui.label('Waypoints').classes('text-h6')

            def handle_wp_upload(e):
                try:
                    content = e.content.read().decode('utf-8')
                    # The original code uses a file path, but with upload we have content.
                    # The load_waypoint_file method in EDWayPoint.py reads from a file path.
                    # I will need to save the uploaded content to a temporary file and pass the path.
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                        f.write(content)
                        filepath = f.name

                    if ed_ap.waypoint.load_waypoint_file(filepath):
                        ui.notify(f"Loaded waypoint file: {e.name}")
                    else:
                        ui.notify(f"Failed to load waypoint file: {e.name}", type='negative')
                except Exception as ex:
                    ui.notify(f"Error: {ex}", type='negative')

            ui.upload(on_upload=handle_wp_upload, auto_upload=True, label="Load Waypoint File").props('icon=folder')

            def reset_wp():
                if not ed_ap.waypoint_assist_enabled:
                    ed_ap.waypoint.mark_all_waypoints_not_complete()
                    ui.notify("Waypoint list reset.")
                else:
                    ui.notify("Waypoint Assist must be disabled before you can reset the list.", type='negative')

            ui.button('Reset Waypoint List', on_click=reset_wp)

    with ui.row():
        with ui.card().classes('w-full'):
            ui.label('LOG').classes('text-h6')
            log_display.classes('w-full')
            log_display.push('Log messages will appear here.')
