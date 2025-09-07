from nicegui import ui
from nicegui.events import UploadEventArguments
from EDAPWaypointEditor import ALL_COMMODITIES
from EDAP_EDMesg_Interface import create_edap_client, LoadWaypointFileAction
import json
import csv
import io
import os

class NiceGuiShoppingItem:
    def __init__(self, name="", quantity=0):
        self.name = name
        self.quantity = quantity

class NiceGuiWaypoint:
    def __init__(self, name="", system_name="", station_name=""):
        self.name = name
        self.system_name = system_name
        self.station_name = station_name
        self.galaxy_bookmark_type = ""
        self.galaxy_bookmark_number = 0
        self.system_bookmark_type = ""
        self.system_bookmark_number = 0
        self.sell_commodities = []
        self.buy_commodities = []
        self.update_commodity_count = False
        self.fleet_carrier_transfer = False
        self.skip = False
        self.completed = False
        self.comment = ""
        self.scan_missions = False

def create_waypoint_editor_tab(ed_waypoint):

    # --- STATE ---
    internal_waypoints = []
    mesg_client = create_edap_client(15570, 15571)
    WAYPOINTS_DIR = './waypoints/'

    os.makedirs(WAYPOINTS_DIR, exist_ok=True)

    # --- DATA CONVERSION LOGIC ---
    def populate_internal_waypoints():
        nonlocal internal_waypoints
        internal_waypoints = []
        raw_waypoints = ed_waypoint.waypoints
        if not isinstance(raw_waypoints, dict):
            return

        for key, value in raw_waypoints.items():
            if key == "GlobalShoppingList":
                continue
            wp = NiceGuiWaypoint(name=key)
            wp.system_name = value.get('SystemName', '')
            wp.station_name = value.get('StationName', '')
            wp.galaxy_bookmark_type = value.get('GalaxyBookmarkType', '')
            wp.galaxy_bookmark_number = value.get('GalaxyBookmarkNumber', 0)
            wp.system_bookmark_type = value.get('SystemBookmarkType', '')
            wp.system_bookmark_number = value.get('SystemBookmarkNumber', 0)
            wp.update_commodity_count = value.get('UpdateCommodityCount', False)
            wp.fleet_carrier_transfer = value.get('FleetCarrierTransfer', False)
            wp.skip = value.get('Skip', False)
            wp.completed = value.get('Completed', False)
            wp.comment = value.get('Comment', '')
            wp.scan_missions = value.get('ScanMissions', False)
            wp.buy_commodities = [NiceGuiShoppingItem(k, v) for k, v in value.get('BuyCommodities', {}).items()]
            wp.sell_commodities = [NiceGuiShoppingItem(k, v) for k, v in value.get('SellCommodities', {}).items()]
            internal_waypoints.append(wp)
        update_waypoints_table()
        update_commodity_tables()

    def convert_to_raw_waypoints():
        raw_waypoints = {}
        if 'GlobalShoppingList' in ed_waypoint.waypoints:
             raw_waypoints['GlobalShoppingList'] = ed_waypoint.waypoints['GlobalShoppingList']

        for i, wp in enumerate(internal_waypoints):
            raw_wp = {
                'SystemName': wp.system_name,
                'StationName': wp.station_name,
                'GalaxyBookmarkType': wp.galaxy_bookmark_type,
                'GalaxyBookmarkNumber': wp.galaxy_bookmark_number,
                'SystemBookmarkType': wp.system_bookmark_type,
                'SystemBookmarkNumber': wp.system_bookmark_number,
                'UpdateCommodityCount': wp.update_commodity_count,
                'FleetCarrierTransfer': wp.fleet_carrier_transfer,
                'Skip': wp.skip,
                'Completed': wp.completed,
                'ScanMissions': wp.scan_missions,
                'Comment': wp.comment,
                'BuyCommodities': {item.name: item.quantity for item in wp.buy_commodities},
                'SellCommodities': {item.name: item.quantity for item in wp.sell_commodities}
            }
            raw_waypoints[wp.name or str(i)] = raw_wp
        return raw_waypoints

    # --- UI UPDATE LOGIC (pre-declare for use in handlers) ---
    waypoints_table = None
    buy_commodities_table = None
    sell_commodities_table = None
    waypoint_options_card = None
    gbt_input, gbn_input, sbt_input, sbn_input = None, None, None, None
    ucc_check, fct_check, sm_check, comment_area = None, None, None, None

    def update_waypoints_table():
        if not waypoints_table: return
        waypoints_table.rows = [
            {
                'name': wp.name,
                'system_name': wp.system_name,
                'station_name': wp.station_name,
                'skip': wp.skip,
                'completed': wp.completed,
            } for wp in internal_waypoints
        ]
        waypoints_table.update()

    async def update_commodity_tables():
        if not waypoints_table: return
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            if buy_commodities_table: buy_commodities_table.rows = []
            if sell_commodities_table: sell_commodities_table.rows = []
            if waypoint_options_card: waypoint_options_card.visible = False
        else:
            if waypoint_options_card: waypoint_options_card.visible = True
            selected_name = selection[0]['name']
            wp = next((wp for wp in internal_waypoints if wp.name == selected_name), None)
            if wp:
                gbt_input.value = wp.galaxy_bookmark_type
                gbn_input.value = wp.galaxy_bookmark_number
                sbt_input.value = wp.system_bookmark_type
                sbn_input.value = wp.system_bookmark_number
                ucc_check.value = wp.update_commodity_count
                fct_check.value = wp.fleet_carrier_transfer
                sm_check.value = wp.scan_missions
                comment_area.value = wp.comment

                if buy_commodities_table: buy_commodities_table.rows = [{'name': item.name, 'quantity': item.quantity} for item in wp.buy_commodities]
                if sell_commodities_table: sell_commodities_table.rows = [{'name': item.name, 'quantity': item.quantity} for item in wp.sell_commodities]

        if buy_commodities_table: buy_commodities_table.update()
        if sell_commodities_table: sell_commodities_table.update()
        if waypoint_options_card: waypoint_options_card.update()

    # --- EVENT HANDLERS & LOGIC ---
    def load_file(filepath):
        if ed_waypoint.load_waypoint_file(filepath):
            populate_internal_waypoints()
            mesg_client.publish(LoadWaypointFileAction(filepath=filepath))
            ui.notify(f"Loaded waypoint file: {os.path.basename(filepath)}")
        else:
            ui.notify(f"Failed to load invalid waypoint file: {os.path.basename(filepath)}", type='negative')

    def new_file():
        nonlocal internal_waypoints
        internal_waypoints = []
        ed_waypoint.waypoints = {}
        ed_waypoint.filename = None
        update_waypoints_table()
        update_commodity_tables()
        ui.notify("New waypoint list created. Don't forget to save.")

    async def open_file_dialog():
        with ui.dialog() as dialog, ui.card():
            ui.label('Open Waypoint File').classes('text-h6')
            file_select = None
            try:
                files = [f for f in os.listdir(WAYPOINTS_DIR) if f.endswith('.json')]
                if not files:
                    ui.label('No waypoint files found.')
                else:
                    file_select = ui.select(files, label="Select a file")
            except FileNotFoundError:
                ui.label(f"Directory not found: {WAYPOINTS_DIR}")

            with ui.row():
                ui.button('Open', on_click=lambda: dialog.submit(file_select.value if file_select and file_select.value else None))
                ui.button('Cancel', on_click=dialog.close)

        result = await dialog
        if result:
            filepath = os.path.join(WAYPOINTS_DIR, result)
            load_file(filepath)

    def handle_upload(e: UploadEventArguments, is_csv: bool = False):
        if is_csv:
            try:
                content = e.content.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(content))
                for row in reader:
                    system_name = row.get("System Name")
                    if system_name:
                        new_waypoint = NiceGuiWaypoint(name=system_name, system_name=system_name)
                        internal_waypoints.append(new_waypoint)
                update_waypoints_table()
                ui.notify(f"Imported waypoints from {e.name}")
            except Exception as ex:
                ui.notify(f"Failed to import CSV file: {ex}", type='negative')
            return

        try:
            filepath = os.path.join(WAYPOINTS_DIR, e.name)
            content_bytes = e.content.read()
            with open(filepath, 'wb') as f:
                f.write(content_bytes)
            load_file(filepath)
        except Exception as ex:
            ui.notify(f"Error uploading file: {ex}", type='negative')

    def save_file():
        if ed_waypoint.filename:
            raw_waypoints = convert_to_raw_waypoints()
            ed_waypoint.write_waypoints(raw_waypoints, ed_waypoint.filename)
            mesg_client.publish(LoadWaypointFileAction(filepath=ed_waypoint.filename))
            ui.notify(f"Saved to {os.path.basename(ed_waypoint.filename)}")
        else:
            save_as_file()

    async def save_as_file():
        with ui.dialog() as dialog, ui.card():
            ui.label('Save Waypoint File').classes('text-h6')
            filename_input = ui.input('Filename', placeholder='my_waypoints.json').on('keydown.enter', lambda: dialog.submit(filename_input.value))
            with ui.row():
                ui.button('Save', on_click=lambda: dialog.submit(filename_input.value))
                ui.button('Cancel', on_click=dialog.close)

        result = await dialog
        if result:
            if not result.endswith('.json'):
                result += '.json'
            filepath = os.path.join(WAYPOINTS_DIR, result)
            raw_waypoints = convert_to_raw_waypoints()
            ed_waypoint.write_waypoints(raw_waypoints, filepath)
            ed_waypoint.filename = filepath
            mesg_client.publish(LoadWaypointFileAction(filepath=filepath))
            ui.notify(f"Saved new file to {result}")

    def add_inara_route(text):
        try:
            lines = text.splitlines()
            from_waypoint = NiceGuiWaypoint()
            to_waypoint = NiceGuiWaypoint()
            from_buy, from_sell = True, True

            for line in lines:
                clean_line = line.strip()
                if clean_line.lower().startswith("from:"):
                    parts = clean_line[5:].strip().split('|')
                    if len(parts) >= 2:
                        from_waypoint.station_name = parts[0].strip()
                        from_waypoint.system_name = parts[1].strip()
                        from_waypoint.name = from_waypoint.station_name or from_waypoint.system_name
                elif clean_line.lower().startswith("to:"):
                    parts = clean_line[3:].strip().split('|')
                    if len(parts) >= 2:
                        to_waypoint.station_name = parts[0].strip()
                        to_waypoint.system_name = parts[1].strip()
                        to_waypoint.name = to_waypoint.station_name or to_waypoint.system_name
                elif clean_line.lower().startswith("buy"):
                    commodity = clean_line.split(maxsplit=1)[1].strip()
                    if from_buy: from_waypoint.buy_commodities.append(NiceGuiShoppingItem(commodity, 9999))
                    else: to_waypoint.buy_commodities.append(NiceGuiShoppingItem(commodity, 9999))
                    from_buy = False
                elif clean_line.lower().startswith("sell"):
                    commodity = clean_line.split(maxsplit=1)[1].strip()
                    if from_sell: from_waypoint.sell_commodities.append(NiceGuiShoppingItem(commodity, 9999))
                    else: to_waypoint.sell_commodities.append(NiceGuiShoppingItem(commodity, 9999))
                    from_sell = False

            if from_waypoint.name: internal_waypoints.append(from_waypoint)
            if to_waypoint.name: internal_waypoints.append(to_waypoint)
            update_waypoints_table()
            ui.notify("Inara route added.")
        except Exception as e:
            ui.notify(f"Failed to parse Inara data: {e}", type='negative')

    async def import_from_inara():
        with ui.dialog() as dialog, ui.card():
            ui.label('Import from Inara').classes('text-h6')
            ui.label('Paste Inara trade route data below:')
            inara_text = ui.textarea().classes('w-full')
            with ui.row():
                ui.button('Import', on_click=lambda: dialog.submit(inara_text.value))
                ui.button('Cancel', on_click=dialog.close)

        result = await dialog
        if result:
            add_inara_route(result)

    def add_waypoint():
        i = 1
        while f"New Waypoint {i}" in [wp.name for wp in internal_waypoints]:
            i += 1
        new_name = f"New Waypoint {i}"
        new_waypoint = NiceGuiWaypoint(name=new_name, system_name="New System")
        internal_waypoints.append(new_waypoint)
        update_waypoints_table()

    async def delete_waypoint():
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            ui.notify("No waypoint selected.", type='negative')
            return
        selected_name = selection[0]['name']
        nonlocal internal_waypoints
        internal_waypoints = [wp for wp in internal_waypoints if wp.name != selected_name]
        waypoints_table.selected = []
        update_waypoints_table()
        update_commodity_tables()
        ui.notify(f"Waypoint '{selected_name}' deleted.")

    async def move_waypoint(direction):
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            ui.notify("No waypoint selected.", type='negative')
            return
        selected_name = selection[0]['name']
        index = next((i for i, wp in enumerate(internal_waypoints) if wp.name == selected_name), -1)
        if index != -1:
            new_index = index
            if direction == 'up' and index > 0:
                new_index = index - 1
                internal_waypoints.insert(new_index, internal_waypoints.pop(index))
            elif direction == 'down' and index < len(internal_waypoints) - 1:
                new_index = index + 1
                internal_waypoints.insert(new_index, internal_waypoints.pop(index))

            update_waypoints_table()
            await ui.run_javascript(f'getElement({waypoints_table.id}).$props.selected = [getElement({waypoints_table.id}).$props.rows[{new_index}]]', respond=False)

    async def add_commodity(list_type):
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            ui.notify("No waypoint selected.", type='negative')
            return
        selected_name = selection[0]['name']
        wp = next((wp for wp in internal_waypoints if wp.name == selected_name), None)
        if wp:
            with ui.dialog() as dialog, ui.card():
                ui.label('Add Commodity').classes('text-h6')
                commodity_select = ui.select(ALL_COMMODITIES, with_input=True, label="Commodity Name")
                quantity_input = ui.number("Quantity", value=1, min=1)
                ui.button('Add', on_click=lambda: dialog.submit({'name': commodity_select.value, 'quantity': quantity_input.value}))

            result = await dialog
            if result and result.get('name'):
                if list_type == 'buy':
                    wp.buy_commodities.append(NiceGuiShoppingItem(result['name'], result['quantity']))
                else:
                    wp.sell_commodities.append(NiceGuiShoppingItem(result['name'], result['quantity']))
                await update_commodity_tables()

    async def delete_commodity(list_type):
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            ui.notify("No waypoint selected.", type='negative')
            return
        selected_name = selection[0]['name']
        wp = next((wp for wp in internal_waypoints if wp.name == selected_name), None)
        if wp:
            table_to_check = buy_commodities_table if list_type == 'buy' else sell_commodities_table
            commodity_selection = await table_to_check.get_selected_rows()
            if commodity_selection:
                commodity_name = commodity_selection[0]['name']
                if list_type == 'buy':
                    wp.buy_commodities = [item for item in wp.buy_commodities if item.name != commodity_name]
                else:
                    wp.sell_commodities = [item for item in wp.sell_commodities if item.name != commodity_name]
                await update_commodity_tables()
            else:
                ui.notify("No commodity selected.", type='negative')

    # --- UI LAYOUT ---
    with ui.row():
        ui.button('New', on_click=new_file)
        ui.button('Open', on_click=open_file_dialog).props('icon=folder_open')
        ui.upload(label="Upload", on_upload=handle_upload, auto_upload=True).props('icon=upload')
        ui.button('Save', on_click=save_file)
        ui.button('Save As', on_click=save_as_file)
        ui.upload(label="Import Spansh CSV", on_upload=lambda e: handle_upload(e, is_csv=True), auto_upload=True).props('icon=description')
        ui.button('Import from Inara', on_click=import_from_inara)

    with ui.row().classes('w-full'):
        with ui.card().classes('flex-grow'):
            waypoints_columns = [
                {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
                {'name': 'system_name', 'label': 'System Name', 'field': 'system_name', 'sortable': True, 'align': 'left'},
                {'name': 'station_name', 'label': 'Station Name', 'field': 'station_name', 'sortable': True, 'align': 'left'},
                {'name': 'skip', 'label': 'Skip', 'field': 'skip'},
                {'name': 'completed', 'label': 'Completed', 'field': 'completed'},
            ]
            waypoints_table = ui.table(columns=waypoints_columns, rows=[], row_key='name', selection='single').classes('w-full h-64')

            for col in ['name', 'system_name', 'station_name']:
                waypoints_table.add_slot(f'body-cell-{col}', f'''
                    <q-td :props="props">
                        {{{{ props.row.{col} }}}}
                        <q-popup-edit v-model="props.row.{col}" v-slot="scope"
                            @save="(val, initialValue) => $parent.$emit('cell-updated', {{ name: props.row.name, column: '{col}', value: val }})">
                            <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" />
                        </q-popup-edit>
                    </q-td>
                ''')

            waypoints_table.add_slot('body-cell-skip', '''
                <q-td :props="props">
                    <q-checkbox v-model="props.row.skip" @update:model-value="(val) => $parent.$emit('cell-updated', { name: props.row.name, column: 'skip', value: val })"/>
                </q-td>
            ''')
            waypoints_table.add_slot('body-cell-completed', '''
                <q-td :props="props">
                    <q-checkbox v-model="props.row.completed" @update:model-value="(val) => $parent.$emit('cell-updated', { name: props.row.name, column: 'completed', value: val })"/>
                </q-td>
            ''')

            def handle_cell_update(event):
                args = event.args
                row_name = args['name']
                column = args['column']
                new_value = args['value']

                wp = next((wp for wp in internal_waypoints if wp.name == row_name), None)
                if wp:
                    old_name = wp.name
                    setattr(wp, column, new_value)

                    if column == 'name':
                        for row in waypoints_table.rows:
                            if row['name'] == old_name:
                                row['name'] = new_value
                                break

                waypoints_table.update()

            waypoints_table.on('cell-updated', handle_cell_update)
            waypoints_table.on('selection', update_commodity_tables)

        with ui.column():
            ui.button('Up', on_click=lambda: move_waypoint('up')).props('icon=arrow_upward')
            ui.button('Down', on_click=lambda: move_waypoint('down')).props('icon=arrow_downward')
            ui.button('Add', on_click=add_waypoint).props('icon=add')
            ui.button('Del', on_click=delete_waypoint).props('icon=delete')

    with ui.row().classes('w-full'):
        with ui.card().classes('w-full').bind_visibility_from(waypoints_table, 'selected', value=lambda s: len(s) > 0) as waypoint_options_card:
            with ui.expansion('Waypoint Options', icon='settings').classes('w-full'):
                with ui.row():
                    gbt_input = ui.input('Galaxy Bookmark Type')
                    gbn_input = ui.number('Galaxy Bookmark Number')
                with ui.row():
                    sbt_input = ui.input('System Bookmark Type')
                    sbn_input = ui.number('System Bookmark Number')
                with ui.row():
                    ucc_check = ui.checkbox('Update Commodity Count')
                    fct_check = ui.checkbox('Fleet Carrier Transfer')
                    sm_check = ui.checkbox('Scan Missions')
                comment_area = ui.textarea('Comment').classes('w-full')

                def connect_options_to_data(e):
                    selection = waypoints_table.selected
                    if not selection: return
                    wp = next((wp for wp in internal_waypoints if wp.name == selection[0]['name']), None)
                    if wp:
                        wp.galaxy_bookmark_type = gbt_input.value
                        wp.galaxy_bookmark_number = gbn_input.value
                        wp.system_bookmark_type = sbt_input.value
                        wp.system_bookmark_number = sbn_input.value
                        wp.update_commodity_count = ucc_check.value
                        wp.fleet_carrier_transfer = fct_check.value
                        wp.scan_missions = sm_check.value
                        wp.comment = comment_area.value

                for ctrl in [gbt_input, gbn_input, sbt_input, sbn_input, ucc_check, fct_check, sm_check, comment_area]:
                    ctrl.on('update:model-value', connect_options_to_data)

    with ui.row().classes('w-full'):
        with ui.card().classes('w-1/2'):
            ui.label('Buy Commodities').classes('text-h6')
            buy_commodities_columns = [
                {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left'},
                {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity', 'align': 'right'}
            ]
            buy_commodities_table = ui.table(columns=buy_commodities_columns, rows=[], row_key='name', selection='single').classes('w-full h-32')
            with ui.row():
                ui.button('Add', on_click=lambda: add_commodity('buy'))
                ui.button('Del', on_click=lambda: delete_commodity('buy'))

        with ui.card().classes('w-1/2'):
            ui.label('Sell Commodities').classes('text-h6')
            sell_commodities_columns = [
                {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left'},
                {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity', 'align': 'right'}
            ]
            sell_commodities_table = ui.table(columns=sell_commodities_columns, rows=[], row_key='name', selection='single').classes('w-full h-32')
            with ui.row():
                ui.button('Add', on_click=lambda: add_commodity('sell'))
                ui.button('Del', on_click=lambda: delete_commodity('sell'))

    # Initial population
    populate_internal_waypoints()
