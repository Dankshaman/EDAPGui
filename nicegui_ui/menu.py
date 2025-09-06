from nicegui import ui

def menu() -> None:
    ui.link('Main', '/').classes(replace='text-black')
    ui.link('Settings', '/settings').classes(replace='text-black')
    ui.link('Debug/Test', '/debug').classes(replace='text-black')
    ui.link('Calibration', '/calibration').classes(replace='text-black')
    ui.link('Waypoint Editor', '/waypoint-editor').classes(replace='text-black')
    ui.link('Wing Mining', '/wing-mining').classes(replace='text-black')
    # Add links to other pages here as they are created
