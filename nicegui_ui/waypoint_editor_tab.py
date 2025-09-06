from nicegui import ui
from EDAPWaypointEditor import ALL_COMMODITIES
import json
import csv
import io

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

    internal_waypoints = []

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

    def convert_to_raw_waypoints():
        raw_waypoints = {}
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

    def update_waypoints_table():
        waypoints_table.rows = [
            {
                'name': wp.name,
                'system_name': wp.system_name,
                'station_name': wp.station_name,
                'skip': "✓" if wp.skip else "",
                'completed': "✓" if wp.completed else ""
            } for wp in internal_waypoints
        ]
        waypoints_table.update()

    def new_file():
        nonlocal internal_waypoints
        internal_waypoints = []
        update_waypoints_table()
        ui.notify("New waypoint list created. Don't forget to save.")

    def save_file():
        if ed_waypoint.filename:
            raw_waypoints = convert_to_raw_waypoints()
            ed_waypoint.write_waypoints(raw_waypoints, ed_waypoint.filename)
            ui.notify(f"Saved to {ed_waypoint.filename}")
        else:
            save_as_file()

    def save_as_file():
        raw_waypoints = convert_to_raw_waypoints()
        ui.download(json.dumps(raw_waypoints, indent=4).encode(), 'waypoints.json')
        ui.notify("Waypoint file is being downloaded to your computer.")

    def add_waypoint():
        new_waypoint = NiceGuiWaypoint(name="New Waypoint", system_name="New System")
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
        update_waypoints_table()
        ui.notify(f"Waypoint '{selected_name}' deleted.")

    async def move_waypoint(direction):
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            ui.notify("No waypoint selected.", type='negative')
            return

        selected_name = selection[0]['name']
        index = next((i for i, wp in enumerate(internal_waypoints) if wp.name == selected_name), -1)

        if index == -1:
            return

        if direction == 'up' and index > 0:
            internal_waypoints.insert(index - 1, internal_waypoints.pop(index))
        elif direction == 'down' and index < len(internal_waypoints) - 1:
            internal_waypoints.insert(index + 1, internal_waypoints.pop(index))

        update_waypoints_table()

    with ui.row():
        ui.button('New', on_click=new_file)
        ui.button('Save', on_click=save_file)
        ui.button('Save As', on_click=save_as_file)
        # ... (upload and other buttons)

    with ui.row():
        waypoints_columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
            {'name': 'system_name', 'label': 'System Name', 'field': 'system_name', 'sortable': True},
            {'name': 'station_name', 'label': 'Station Name', 'field': 'station_name', 'sortable': True},
            {'name': 'skip', 'label': 'Skip', 'field': 'skip'},
            {'name': 'completed', 'label': 'Completed', 'field': 'completed'},
        ]
        waypoints_table = ui.table(columns=waypoints_columns, rows=[], row_key='name', selection='single').classes('w-full h-64')

    with ui.row():
        ui.button('Up', on_click=lambda: move_waypoint('up'))
        ui.button('Down', on_click=lambda: move_waypoint('down'))
        ui.button('Add', on_click=add_waypoint)
        ui.button('Del', on_click=delete_waypoint)
        ui.button('Edit', on_click=lambda: open_edit_dialog())

    async def open_edit_dialog():
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            ui.notify("No waypoint selected.", type='negative')
            return

        selected_name = selection[0]['name']
        wp_to_edit = next((wp for wp in internal_waypoints if wp.name == selected_name), None)

        if not wp_to_edit:
            return

        with ui.dialog() as dialog, ui.card():
            ui.label('Edit Waypoint').classes('text-h6')
            ui.input('Name', value=wp_to_edit.name, on_change=lambda e: setattr(wp_to_edit, 'name', e.value))
            ui.input('System Name', value=wp_to_edit.system_name, on_change=lambda e: setattr(wp_to_edit, 'system_name', e.value))
            ui.input('Station Name', value=wp_to_edit.station_name, on_change=lambda e: setattr(wp_to_edit, 'station_name', e.value))
            ui.input('Galaxy Bookmark Type', value=wp_to_edit.galaxy_bookmark_type, on_change=lambda e: setattr(wp_to_edit, 'galaxy_bookmark_type', e.value))
            ui.number('Galaxy Bookmark Number', value=wp_to_edit.galaxy_bookmark_number, on_change=lambda e: setattr(wp_to_edit, 'galaxy_bookmark_number', e.value))
            ui.input('System Bookmark Type', value=wp_to_edit.system_bookmark_type, on_change=lambda e: setattr(wp_to_edit, 'system_bookmark_type', e.value))
            ui.number('System Bookmark Number', value=wp_to_edit.system_bookmark_number, on_change=lambda e: setattr(wp_to_edit, 'system_bookmark_number', e.value))
            ui.checkbox('Update Commodity Count', value=wp_to_edit.update_commodity_count, on_change=lambda e: setattr(wp_to_edit, 'update_commodity_count', e.value))
            ui.checkbox('Fleet Carrier Transfer', value=wp_to_edit.fleet_carrier_transfer, on_change=lambda e: setattr(wp_to_edit, 'fleet_carrier_transfer', e.value))
            ui.checkbox('Skip', value=wp_to_edit.skip, on_change=lambda e: setattr(wp_to_edit, 'skip', e.value))
            ui.checkbox('Completed', value=wp_to_edit.completed, on_change=lambda e: setattr(wp_to_edit, 'completed', e.value))
            ui.checkbox('Scan Missions', value=wp_to_edit.scan_missions, on_change=lambda e: setattr(wp_to_edit, 'scan_missions', e.value))
            ui.textarea('Comment', value=wp_to_edit.comment, on_change=lambda e: setattr(wp_to_edit, 'comment', e.value))

            with ui.row():
                ui.button('Save', on_click=lambda: (update_waypoints_table(), dialog.close()))
                ui.button('Cancel', on_click=dialog.close)

        await dialog

    # Commodity lists
    with ui.row():
        with ui.card().classes('w-1/2'):
            ui.label('Buy Commodities').classes('text-h6')
            buy_commodities_columns = [
                {'name': 'name', 'label': 'Name', 'field': 'name'},
                {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity'}
            ]
            buy_commodities_table = ui.table(columns=buy_commodities_columns, rows=[], row_key='name', selection='single').classes('w-full h-32')
            with ui.row():
                ui.button('Add', on_click=lambda: add_commodity('buy'))
                ui.button('Del', on_click=lambda: delete_commodity('buy'))

        with ui.card().classes('w-1/2'):
            ui.label('Sell Commodities').classes('text-h6')
            sell_commodities_columns = [
                {'name': 'name', 'label': 'Name', 'field': 'name'},
                {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity'}
            ]
            sell_commodities_table = ui.table(columns=sell_commodities_columns, rows=[], row_key='name', selection='single').classes('w-full h-32')
            with ui.row():
                ui.button('Add', on_click=lambda: add_commodity('sell'))
                ui.button('Del', on_click=lambda: delete_commodity('sell'))

    async def update_commodity_tables():
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            buy_commodities_table.rows = []
            sell_commodities_table.rows = []
        else:
            selected_name = selection[0]['name']
            wp = next((wp for wp in internal_waypoints if wp.name == selected_name), None)
            if wp:
                buy_commodities_table.rows = [{'name': item.name, 'quantity': item.quantity} for item in wp.buy_commodities]
                sell_commodities_table.rows = [{'name': item.name, 'quantity': item.quantity} for item in wp.sell_commodities]
        buy_commodities_table.update()
        sell_commodities_table.update()

    waypoints_table.on('selection', update_commodity_tables)

    async def add_commodity(list_type):
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            ui.notify("No waypoint selected.", type='negative')
            return

        selected_name = selection[0]['name']
        wp = next((wp for wp in internal_waypoints if wp.name == selected_name), None)
        if wp:
            if list_type == 'buy':
                wp.buy_commodities.append(NiceGuiShoppingItem("New Commodity", 1))
            else:
                wp.sell_commodities.append(NiceGuiShoppingItem("New Commodity", 1))
            await update_commodity_tables()

    async def delete_commodity(list_type):
        selection = await waypoints_table.get_selected_rows()
        if not selection:
            ui.notify("No waypoint selected.", type='negative')
            return

        selected_name = selection[0]['name']
        wp = next((wp for wp in internal_waypoints if wp.name == selected_name), None)
        if wp:
            if list_type == 'buy':
                commodity_selection = await buy_commodities_table.get_selected_rows()
                if commodity_selection:
                    wp.buy_commodities = [item for item in wp.buy_commodities if item.name != commodity_selection[0]['name']]
            else:
                commodity_selection = await sell_commodities_table.get_selected_rows()
                if commodity_selection:
                    wp.sell_commodities = [item for item in wp.sell_commodities if item.name != commodity_selection[0]['name']]
            await update_commodity_tables()

    populate_internal_waypoints()
