# Fleet Carrier Assist

The Fleet Carrier Assist feature automates the process of jumping your fleet carrier along a pre-defined route. This guide will walk you through the entire process, from creating a route on spansh.co.uk to executing the jumps in-game using the autopilot.

## Step 1: Creating a Route on Spansh.co.uk

The first step is to plan your fleet carrier route using the excellent online tool, [spansh.co.uk](https://spansh.co.uk/fleet-carrier).

1.  Navigate to the [Fleet Carrier Router](https://spansh.co.uk/fleet-carrier) on spansh.co.uk.
2.  Enter your **Source System** and **Destination System**.
3.  Adjust the **Tritium Capacity** and **Tritium in Tank** to match your carrier's current status.
4.  Click **"Calculate Route"**.
5.  Once the route is calculated, you will see a list of jumps. At the top of the results, click the **"Export as CSV"** button to download the route to your computer. Save this file in a location you can easily access.

## Step 2: Importing the Route into EDAP-GUI

With the CSV file downloaded, you can now import it into the EDAP-GUI application.

1.  Launch the EDAP-GUI application.
2.  Navigate to the **"Waypoint Editor"** tab.
3.  Click the **"Import Spansh CSV"** button. This will open a file dialog.
4.  In the file dialog, navigate to the location where you saved the CSV file from spansh.co.uk and select it.
5.  The application will parse the CSV file and populate the waypoint list with the systems from your planned route. Each system will be a separate waypoint.
6.  Click the **"Save As"** button to save this new list of waypoints as a JSON file (e.g., `my_fc_route.json`) in the `waypoints` directory.

## Step 3: Engaging the Fleet Carrier Assist

Now that your route is loaded and saved, you can engage the Fleet Carrier Assist autopilot.

1.  In the EDAP-GUI application, navigate to the **"Main"** tab.
2.  Click the button that says **"<no list loaded>"** or shows the currently loaded waypoint file. This will open a file dialog.
3.  Select the JSON waypoint file you saved in the previous step (e.g., `my_fc_route.json`).
4.  Ensure you are in your ship and docked at your fleet carrier in Elite Dangerous.
5.  Check the **"Fleet Carrier Assist"** checkbox in the "MODE" section.

The autopilot will now take over. It will perform the following actions for each waypoint in your list:

1.  **Refuel Tritium:** The autopilot will automatically transfer tritium from your ship's inventory to the fleet carrier's tank.
2.  **Plot Route and Jump:** It will navigate the in-game menus to the fleet carrier management screen, open the galaxy map, plot a course to the next system in the waypoint list, and initiate the jump.
3.  **Wait for Jump:** The autopilot will monitor the game's journal files to detect when the carrier jump is complete. This has a timeout of 60 minutes.
4.  **Verify Jump:** After the jump, it will verify that the carrier has arrived in the correct system.
5.  **Cooldown:** The autopilot will wait for the 5-minute post-jump cooldown period before starting the process for the next waypoint.

The autopilot will continue this process until all waypoints in the list have been completed. To stop the Fleet Carrier Assist at any time, simply uncheck the "Fleet Carrier Assist" checkbox.
