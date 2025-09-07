from contextlib import contextmanager
from nicegui import ui
from menu import menu

@contextmanager
def frame(navtitle: str, status_label: ui.label):
    """Custom page frame to share the same styling and behavior across all pages."""
    ui.colors(primary='#6E93D6', secondary='#53B689', accent='#111B1E', positive='#53B689')
    with ui.header().classes(replace='row items-center') as header:
        ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
        ui.label('EDAP').classes('font-bold')
        ui.label(navtitle).classes('font-bold')

    with ui.left_drawer().classes('bg-blue-100') as left_drawer:
        ui.label('Menu')
        with ui.column():
            menu()

    with ui.column().classes('absolute-center items-center min-h-screen no-wrap p-9 pb-32 w-full'):
        yield

    with ui.footer(value=True) as footer:
        status_label.classes('w-full text-center')

    with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
        ui.button(on_click=footer.toggle, icon='contact_support').props('fab')
