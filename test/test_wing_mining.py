import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from WingMining import WingMining, STATE_SCAN_FOR_MISSIONS, STATE_PROCESS_QUEUE

class TestWingMining(unittest.TestCase):

    def setUp(self):
        # Create a mock for the main application object
        self.mock_ed_ap = MagicMock()

        # Mock dependencies that WingMining uses
        self.mock_ed_ap.config = {
            'WingMining_StationA': 'SystemA/StationA',
            'WingMining_StationB': 'SystemB/StationB',
            'WingMining_CompletedMissions': 0
        }
        self.mock_ed_ap.stn_svcs_in_ship = MagicMock()
        self.mock_ed_ap.keys = MagicMock()
        self.mock_ed_ap.jn = MagicMock()

        # Instantiate WingMining with the mocked dependencies
        with patch('StateManager.load_state', return_value=None):
            self.wing_mining = WingMining(self.mock_ed_ap)

    def test_check_depot_when_no_missions_and_no_current_mission(self):
        """
        Verify that the mission depot is checked if the initial scan finds no missions
        and there is no current mission being processed.
        """
        # Arrange
        self.wing_mining.state = STATE_SCAN_FOR_MISSIONS
        self.wing_mining.current_mission = None
        self.mock_ed_ap.stn_svcs_in_ship.scan_wing_missions.return_value = []

        mock_depot_mission = {"commodity": "Gold", "tonnage": 200, "reward": 50000000, "mission_id": "123", "ocr_text": "Mine 200 units of Gold"}
        self.mock_ed_ap.stn_svcs_in_ship.check_mission_depot_for_wing_missions.return_value = [mock_depot_mission]

        # Act
        self.wing_mining._handle_scan_for_missions()

        # Assert
        self.mock_ed_ap.stn_svcs_in_ship.scan_wing_missions.assert_called_once()
        self.mock_ed_ap.stn_svcs_in_ship.check_mission_depot_for_wing_missions.assert_called_once()
        self.assertEqual(len(self.wing_mining.mission_queue), 1)
        self.assertEqual(self.wing_mining.mission_queue[0]['commodity'], "Gold")
        self.assertEqual(self.wing_mining.state, STATE_PROCESS_QUEUE)

    def test_do_not_check_depot_if_missions_are_found(self):
        """
        Verify that the mission depot is NOT checked if the initial scan finds missions.
        """
        # Arrange
        self.wing_mining.state = STATE_SCAN_FOR_MISSIONS
        self.wing_mining.current_mission = None

        mock_new_mission = {"commodity": "Silver", "tonnage": 300, "reward": 50000000, "mission_id": "456", "ocr_text": "Mine 300 units of Silver"}
        self.mock_ed_ap.stn_svcs_in_ship.scan_wing_missions.return_value = [mock_new_mission]

        # Act
        self.wing_mining._handle_scan_for_missions()

        # Assert
        self.mock_ed_ap.stn_svcs_in_ship.scan_wing_missions.assert_called_once()
        self.mock_ed_ap.stn_svcs_in_ship.check_mission_depot_for_wing_missions.assert_not_called()
        self.assertEqual(len(self.wing_mining.mission_queue), 1)
        self.assertEqual(self.wing_mining.mission_queue[0]['commodity'], "Silver")

    def test_do_not_check_depot_if_current_mission_exists(self):
        """
        Verify that the mission depot is NOT checked if there is a current mission,
        even if the initial scan finds no new missions.
        """
        # Arrange
        self.wing_mining.state = STATE_SCAN_FOR_MISSIONS
        self.wing_mining.current_mission = {"commodity": "Indite", "tonnage": 700, "reward": 50000000, "mission_id": "789", "ocr_text": "Mine 700 units of Indite"}
        self.mock_ed_ap.stn_svcs_in_ship.scan_wing_missions.return_value = []

        # Act
        self.wing_mining._handle_scan_for_missions()

        # Assert
        self.mock_ed_ap.stn_svcs_in_ship.scan_wing_missions.assert_called_once()
        self.mock_ed_ap.stn_svcs_in_ship.check_mission_depot_for_wing_missions.assert_not_called()
        self.assertEqual(len(self.wing_mining.mission_queue), 0)

if __name__ == '__main__':
    unittest.main()
