from contextlib import contextmanager
from nicegui import ui
from menu import menu

@contextmanager
def frame(navtitle: str):
    """Custom page frame to share the same styling and behavior across all pages."""
    ui.colors(primary='#a13900', secondary='#FB8C00', accent='#111B1E', positive='#FB8C00')
    with ui.header().classes(replace='row items-center') as header:
        ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
        ui.label('EDAP').classes('font-bold')
        ui.label(navtitle).classes('font-bold')

    with ui.left_drawer().classes('bg-grey-9') as left_drawer:
        ui.label('Menu')
        with ui.column():
            menu()

    with ui.column().classes('absolute-center items-center min-h-screen no-wrap p-9 pb-32 w-full'):
        yield
