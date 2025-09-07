from nicegui import ui

def create_main_tab(ed_ap, log_container, assist_checkboxes, ship_controls, ship_data):
    with ui.grid(columns=3):
        with ui.card():
            ui.label('MODE').classes('text-h6')
            with ui.row().classes('w-full'):
                assist_checkbox_definitions = {
                    'FSD Route Assist': lambda e: ed_ap.set_fsd_assist(e.value),
                    'Supercruise Assist': lambda e: ed_ap.set_sc_assist(e.value),
                    'Waypoint Assist': lambda e: ed_ap.set_waypoint_assist(e.value),
                    'Robigo Assist': lambda e: ed_ap.set_robigo_assist(e.value),
                    'AFK Combat Assist': lambda e: ed_ap.set_afk_combat_assist(e.value),
                    'DSS Assist': lambda e: ed_ap.set_dss_assist(e.value),
                    'Fleet Carrier Assist': lambda e: ed_ap.set_fc_assist(e.value),
                    'Wing Mining Assist': lambda e: ed_ap.set_wing_mining_assist(e.value),
                }

                checkbox_list = list(assist_checkbox_definitions.keys())
                mid_point = (len(checkbox_list) + 1) // 2

                with ui.column().classes('w-1/2'):
                    for name in checkbox_list[:mid_point]:
                        assist_checkboxes[name] = ui.checkbox(name, on_change=assist_checkbox_definitions[name])
                with ui.column().classes('w-1/2'):
                    for name in checkbox_list[mid_point:]:
                        assist_checkboxes[name] = ui.checkbox(name, on_change=assist_checkbox_definitions[name])

        with ui.card():
            ui.label('SHIP').classes('text-h6')
            ship_controls['RollRate'] = ui.number('RollRate').bind_value(ship_data, 'rollrate').on('change', lambda e: setattr(ed_ap, 'rollrate', e.value))
            ship_controls['PitchRate'] = ui.number('PitchRate').bind_value(ship_data, 'pitchrate').on('change', lambda e: setattr(ed_ap, 'pitchrate', e.value))
            ship_controls['YawRate'] = ui.number('YawRate').bind_value(ship_data, 'yawrate').on('change', lambda e: setattr(ed_ap, 'yawrate', e.value))
            ship_controls['SunPitchUp+Time'] = ui.number('SunPitchUp+Time').bind_value(ship_data, 'sunpitchuptime').on('change', lambda e: setattr(ed_ap, 'sunpitchuptime', e.value))

            ui.separator()

            ship_controls['AutoDockBoost'] = ui.checkbox('Auto-Dock Boost').bind_value(ship_data, 'autodock_boost').on('change', lambda e: setattr(ed_ap, 'autodock_boost', e.value))
            ship_controls['AutoDockForwardTime'] = ui.number('Auto-Dock Fwd Time').bind_value(ship_data, 'autodock_forward_time').on('change', lambda e: setattr(ed_ap, 'autodock_forward_time', e.value))
            ship_controls['AutoDockDelayTime'] = ui.number('Auto-Dock Delay').bind_value(ship_data, 'autodock_delay_time').on('change', lambda e: setattr(ed_ap, 'autodock_delay_time', e.value))

            ui.button('Test Roll Rate', on_click=ed_ap.ship_tst_roll)
            ui.button('Test Pitch Rate', on_click=ed_ap.ship_tst_pitch)
            ui.button('Test Yaw Rate', on_click=ed_ap.ship_tst_yaw)

        with ui.column():
            with ui.card():
                ui.label('Waypoints').classes('text-h6')

                def handle_wp_upload(e):
                    try:
                        content = e.content.read().decode('utf-8')
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

            with ui.card():
                ui.label('LOG').classes('text-h6')
                log_container['log'] = ui.log(max_lines=100).classes('w-full')
                for message in log_container['history']:
                    log_container['log'].push(message)
