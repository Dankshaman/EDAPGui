from nicegui import ui

def create_wing_mining_tab(ed_ap):
    with ui.grid(columns=2):
        with ui.card().classes('w-full col-span-2'):
            ui.label('Wing Mining Settings').classes('text-h6')
            with ui.grid(columns=2):
                with ui.column():
                    ui.input('Station A', value=ed_ap.config.get('WingMining_StationA', ''), on_change=lambda e: ed_ap.config.update({'WingMining_StationA': e.value}))
                    ui.input('Bertrandite FC (A)', value=ed_ap.config.get('WingMining_FC_A_Bertrandite', ''), on_change=lambda e: ed_ap.config.update({'WingMining_FC_A_Bertrandite': e.value}))
                    ui.input('Gold FC (A)', value=ed_ap.config.get('WingMining_FC_A_Gold', ''), on_change=lambda e: ed_ap.config.update({'WingMining_FC_A_Gold': e.value}))
                    ui.input('Indite FC (A)', value=ed_ap.config.get('WingMining_FC_A_Indite', ''), on_change=lambda e: ed_ap.config.update({'WingMining_FC_A_Indite': e.value}))
                    ui.input('Silver FC (A)', value=ed_ap.config.get('WingMining_FC_A_Silver', ''), on_change=lambda e: ed_ap.config.update({'WingMining_FC_A_Silver': e.value}))
                with ui.column():
                    ui.input('Station B', value=ed_ap.config.get('WingMining_StationB', ''), on_change=lambda e: ed_ap.config.update({'WingMining_StationB': e.value}))
                    ui.input('Bertrandite FC (B)', value=ed_ap.config.get('WingMining_FC_B_Bertrandite', ''), on_change=lambda e: ed_ap.config.update({'WingMining_FC_B_Bertrandite': e.value}))
                    ui.input('Gold FC (B)', value=ed_ap.config.get('WingMining_FC_B_Gold', ''), on_change=lambda e: ed_ap.config.update({'WingMining_FC_B_Gold': e.value}))
                    ui.input('Indite FC (B)', value=ed_ap.config.get('WingMining_FC_B_Indite', ''), on_change=lambda e: ed_ap.config.update({'WingMining_FC_B_Indite': e.value}))
                    ui.input('Silver FC (B)', value=ed_ap.config.get('WingMining_FC_B_Silver', ''), on_change=lambda e: ed_ap.config.update({'WingMining_FC_B_Silver': e.value}))

            ui.input('Discord Data Path', value=ed_ap.config.get('WingMiningDiscordDataPath', 'discord_data.json'), on_change=lambda e: ed_ap.config.update({'WingMiningDiscordDataPath': e.value}))
            ui.checkbox('Skip Mission Depot Check', value=ed_ap.config.get('WingMining_SkipDepotCheck', False), on_change=lambda e: ed_ap.config.update({'WingMining_SkipDepotCheck': e.value}))
            ui.checkbox('Mission Scanner Mode', value=ed_ap.config.get('WingMining_MissionScannerMode', False), on_change=lambda e: ed_ap.config.update({'WingMining_MissionScannerMode': e.value}))

        with ui.card():
            ui.label('Mission Counter').classes('text-h6')
            completed_missions_label = ui.label(f"Completed Missions: {ed_ap.config.get('WingMining_CompletedMissions', 0)}")
            mission_count_input = ui.number('Set Mission Count', value=ed_ap.config.get('WingMining_CompletedMissions', 0),
                                            on_change=lambda e: ed_ap.config.update({'WingMining_CompletedMissions': e.value}))

            def reset_counter():
                ed_ap.config['WingMining_CompletedMissions'] = 0
                mission_count_input.value = 0
                completed_missions_label.text = "Completed Missions: 0"
                ui.notify("Wing Mining mission counter reset.")

            ui.button('Reset Counter', on_click=reset_counter)

        with ui.row():
            ui.button('Save All Settings', on_click=lambda: (ed_ap.update_config(), ed_ap.update_ship_configs(), ui.notify('Settings Saved!')))
