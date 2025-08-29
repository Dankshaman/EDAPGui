import unittest
import tkinter as tk
from unittest.mock import MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from EDAPGui import APGui

class TestWingMiningGUI(unittest.TestCase):
    def test_wing_mining_tab_creation(self):
        root = tk.Tk()
        app = APGui(root)

        # Check if the Wing Mining tab exists
        notebook = root.winfo_children()[0]
        self.assertIsInstance(notebook, tk.ttk.Notebook)
        tab_text_list = [notebook.tab(i, "text") for i in range(notebook.index("end"))]
        self.assertIn("Wing Mining", tab_text_list)

        # Check if the widgets on the tab exist
        self.assertIn('wing_mining_station_a', app.entries)
        self.assertIn('wing_mining_station_b', app.entries)
        self.assertIn('wing_mining_fc_a_bertrandite', app.entries)
        self.assertIn('wing_mining_fc_a_gold', app.entries)
        self.assertIn('wing_mining_fc_a_indite', app.entries)
        self.assertIn('wing_mining_fc_a_silver', app.entries)
        self.assertIn('wing_mining_fc_b_bertrandite', app.entries)
        self.assertIn('wing_mining_fc_b_gold', app.entries)
        self.assertIn('wing_mining_fc_b_indite', app.entries)
        self.assertIn('wing_mining_fc_b_silver', app.entries)
        self.assertIn('wing_mining_mission_count', app.entries)
        self.assertIn('Wing Mining Assist', app.checkboxvar)

        # Simulate checking the Wing Mining Assist checkbox
        app.ed_ap.set_wing_mining_assist = MagicMock()
        app.checkboxvar['Wing Mining Assist'].set(1)
        app.check_cb('Wing Mining Assist')
        app.ed_ap.set_wing_mining_assist.assert_called_with(True)

        root.destroy()

if __name__ == '__main__':
    unittest.main()
