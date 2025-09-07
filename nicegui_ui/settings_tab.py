from nicegui import ui

def create_settings_tab(ed_ap):
    with ui.grid(columns=4):
        with ui.card():
            ui.label('AUTOPILOT').classes('text-h6')
            ui.number('Sun Bright Threshold', value=ed_ap.config.get('SunBrightThreshold', 0), on_change=lambda e: ed_ap.config.update({'SunBrightThreshold': e.value}))
            ui.number('Nav Align Tries', value=ed_ap.config.get('NavAlignTries', 0), on_change=lambda e: ed_ap.config.update({'NavAlignTries': e.value}))
            ui.number('Jump Tries', value=ed_ap.config.get('JumpTries', 0), on_change=lambda e: ed_ap.config.update({'JumpTries': e.value}))
            ui.number('Docking Retries', value=ed_ap.config.get('DockingRetries', 0), on_change=lambda e: ed_ap.config.update({'DockingRetries': e.value}))
            ui.number('Wait For Autodock', value=ed_ap.config.get('WaitForAutoDockTimer', 0), on_change=lambda e: ed_ap.config.update({'WaitForAutoDockTimer': e.value}))
            ui.checkbox('Enable Randomness', value=ed_ap.config.get('EnableRandomness', False), on_change=lambda e: ed_ap.config.update({'EnableRandomness': e.value}))
            ui.checkbox('Activate Elite for each key', value=ed_ap.config.get('ActivateEliteEachKey', False), on_change=lambda e: ed_ap.config.update({'ActivateEliteEachKey': e.value}))
            ui.checkbox('Automatic logout', value=ed_ap.config.get('AutomaticLogout', False), on_change=lambda e: ed_ap.config.update({'AutomaticLogout': e.value}))

        with ui.card():
            ui.label('BUTTONS').classes('text-h6')
            ui.radio(['Primary', 'Secondary'], value=ed_ap.config.get('DSSButton', 'Primary'), on_change=lambda e: ed_ap.config.update({'DSSButton': e.value}))
            ui.label('DSS Button')
            ui.input('Start FSD', value=ed_ap.config.get('HotKey_StartFSD', ''), on_change=lambda e: ed_ap.config.update({'HotKey_StartFSD': e.value}))
            ui.input('Start SC', value=ed_ap.config.get('HotKey_StartSC', ''), on_change=lambda e: ed_ap.config.update({'HotKey_StartSC': e.value}))
            ui.input('Start Robigo', value=ed_ap.config.get('HotKey_StartRobigo', ''), on_change=lambda e: ed_ap.config.update({'HotKey_StartRobigo': e.value}))
            ui.input('Stop All', value=ed_ap.config.get('HotKey_StopAllAssists', ''), on_change=lambda e: ed_ap.config.update({'HotKey_StopAllAssists': e.value}))

        with ui.card():
            ui.label('FUEL').classes('text-h6')
            ui.number('Refuel Threshold', value=ed_ap.config.get('RefuelThreshold', 0), on_change=lambda e: ed_ap.config.update({'RefuelThreshold': e.value}))
            ui.number('Scoop Timeout', value=ed_ap.config.get('FuelScoopTimeOut', 0), on_change=lambda e: ed_ap.config.update({'FuelScoopTimeOut': e.value}))
            ui.number('Fuel Threshold Abort', value=ed_ap.config.get('FuelThreasholdAbortAP', 0), on_change=lambda e: ed_ap.config.update({'FuelThreasholdAbortAP': e.value}))

        with ui.card():
            ui.label('OVERLAY').classes('text-h6')
            ui.checkbox('Enable (requires restart)', value=ed_ap.config.get('OverlayTextEnable', False), on_change=lambda e: ed_ap.config.update({'OverlayTextEnable': e.value}))
            ui.number('X Offset', value=ed_ap.config.get('OverlayTextXOffset', 0), on_change=lambda e: ed_ap.config.update({'OverlayTextXOffset': e.value}))
            ui.number('Y Offset', value=ed_ap.config.get('OverlayTextYOffset', 0), on_change=lambda e: ed_ap.config.update({'OverlayTextYOffset': e.value}))
            ui.number('Font Size', value=ed_ap.config.get('OverlayTextFontSize', 0), on_change=lambda e: ed_ap.config.update({'OverlayTextFontSize': e.value}))

        with ui.card().classes('w-full col-span-4'):
            ui.label('INTEGRATIONS').classes('text-h6')
            with ui.grid(columns=2):
                with ui.card():
                    ui.label('VOICE').classes('text-h6')
                    ui.checkbox('Enable', value=ed_ap.config.get('VoiceEnable', False), on_change=lambda e: ed_ap.config.update({'VoiceEnable': e.value}))

                with ui.card():
                    ui.label('ELW SCANNER').classes('text-h6')
                    ui.checkbox('Enable', value=ed_ap.config.get('FSSScan', False), on_change=lambda e: ed_ap.config.update({'FSSScan': e.value}))

                with ui.card():
                    ui.label('OCR').classes('text-h6')
                    ui.input('Server URL', value=ed_ap.config.get('OcrServerUrl', 'http://127.0.0.1:8000/ocr'), on_change=lambda e: ed_ap.config.update({'OcrServerUrl': e.value}))

                with ui.card():
                    ui.label('DISCORD').classes('text-h6')
                    ui.checkbox('Enable Webhook', value=ed_ap.config.get('DiscordWebhook', False), on_change=lambda e: ed_ap.config.update({'DiscordWebhook': e.value}))
                    ui.input('Webhook URL', value=ed_ap.config.get('DiscordWebhookURL', ''), on_change=lambda e: ed_ap.config.update({'DiscordWebhookURL': e.value}))
                    ui.input('User ID', value=ed_ap.config.get('DiscordUserID', ''), on_change=lambda e: ed_ap.config.update({'DiscordUserID': e.value}))

    ui.button('Save All Settings', on_click=lambda: (ed_ap.update_config(), ed_ap.update_ship_configs(), ui.notify('Settings Saved!')))
