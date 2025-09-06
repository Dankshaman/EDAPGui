from nicegui import ui

def create_calibration_tab(app_state, ed_ap):

    def save_and_notify():
        app_state['save_ocr_calibration_data']()
        ui.notify("OCR calibration data saved.\nPlease restart the application for changes to take effect.")

    async def reset_and_notify():
        with ui.dialog() as dialog, ui.card():
            ui.label('Are you sure you want to reset all OCR calibrations to their default values? This cannot be undone.')
            with ui.row():
                ui.button('Yes', on_click=lambda: dialog.submit(True))
                ui.button('No', on_click=lambda: dialog.submit(False))

        if await dialog:
            app_state['ocr_calibration_data'].clear()
            app_state['load_ocr_calibration_data']()
            ui.notify("All OCR calibrations have been reset to default. Please restart the application.")
            # This requires a refresh of the page to see the changes in the UI

    with ui.grid(columns=2):
        with ui.card().classes('w-full col-span-2'):
            ui.label('Region Calibration').classes('text-h6')
            region_keys = sorted([key for key, value in app_state['ocr_calibration_data'].items() if isinstance(value, dict) and 'rect' in value])
            region_select = ui.select(region_keys, label='Region')

            with ui.row():
                rect_inputs = [ui.number(f'R{i}', on_change=save_and_notify) for i in range(4)]

            def update_rect_inputs(region_name):
                if region_name and region_name in app_state['ocr_calibration_data']:
                    rect = app_state['ocr_calibration_data'][region_name].get('rect', [0,0,0,0])
                    for i, val in enumerate(rect):
                        rect_inputs[i].value = val

            region_select.on('change', lambda e: update_rect_inputs(e.value))

            ui.button('Calibrate Region', on_click=lambda: ui.notify('Not available in this UI. Please use the original GUI for calibration.'))

        with ui.card().classes('w-full col-span-2'):
            ui.label('Size Calibration').classes('text-h6')
            size_keys = sorted([key for key in app_state['ocr_calibration_data'].keys() if '.size.' in key])
            size_select = ui.select(size_keys, label='Size')

            with ui.row():
                width_input = ui.number('Width', on_change=save_and_notify)
                height_input = ui.number('Height', on_change=save_and_notify)

            def update_size_inputs(size_name):
                if size_name and size_name in app_state['ocr_calibration_data']:
                    size = app_state['ocr_calibration_data'][size_name]
                    width_input.value = size.get('width', 0)
                    height_input.value = size.get('height', 0)

            size_select.on('change', lambda e: update_size_inputs(e.value))
            ui.button('Calibrate Size', on_click=lambda: ui.notify('Not available in this UI. Please use the original GUI for calibration.'))

        with ui.card():
            ui.label('Other Calibrations').classes('text-h6')
            ui.button('Calibrate Compass', on_click=ed_ap.calibrate_compass)
            ui.button('Calibrate Target', on_click=ed_ap.calibrate_target)
            ui.checkbox('CUDA OCR', value=app_state['ocr_calibration_data'].get('use_gpu_ocr', False),
                        on_change=lambda e: (app_state['ocr_calibration_data'].update({'use_gpu_ocr': e.value}), save_and_notify()))

        with ui.card():
            ui.label('Value Calibration').classes('text-h6')
            ui.number('Nav Panel Deskew Angle', value=app_state['ocr_calibration_data'].get('EDNavigationPanel.deskew_angle', 0.0),
                      on_change=lambda e: (app_state['ocr_calibration_data'].update({'EDNavigationPanel.deskew_angle': e.value}), save_and_notify()))

        with ui.row().classes('w-full col-span-2'):
            ui.button('Save All Calibrations', on_click=save_and_notify)
            ui.button('Reset All to Default', on_click=reset_and_notify)
