# OCR Region Calibration

This document provides a detailed guide to calibrating the OCR (Optical Character Recognition) regions used by the Elite Dangerous Autopilot (GUI). Proper calibration of these regions is crucial for the autopilot to correctly read information from the game's user interface.

Because of scaling issues with different resolutions and FOV's, the calibration tab allows you to calibrate all OCR regions.

## Calibration Process

1.  Navigate to the in-game screen corresponding to the region you want to calibrate.
2.  In the EDAPGui application, go to the "Calibration" tab.
3.  From the dropdown menu, select the OCR region you wish to adjust.
4.  Click the "Calibrate Region" button.
5.  Click and drag on your screen to draw a box that precisely covers the area shown in the example images below.
6.  Once you are satisfied with all your calibrated regions, click the "Save All" button at the bottom of the calibration tab.
7.  Restart EDAPGui for the changes to take effect.

**Note:** No commands will be sent to Elite Dangerous during this calibration process; it only performs screen grabs.

---

## Calibration Regions

Below are the different OCR regions that require calibration, along with examples of where they should be located.

### Galaxy Map - Cartographics

*   **Region:** `EDGalaxyMap.cartographics`
*   **Description:** This region is used to read information from the cartographics panel in the Galaxy Map.
*   **Example:**
    ![Galaxy Map Cartographics](Calibration%20Images/EDGalaxyMap.cartographics.png)

### System Map - Cartographics

*   **Region:** `EDSystemMap.cartographics`
*   **Description:** This region is used to read information from the cartographics panel in the System Map.
*   **Example:**
    ![System Map Cartographics](Calibration%20Images/EDSystemMap.cartographics.png)

### Navigation Panel - Tab Bar

*   **Region:** `EDNavigationPanel.tab_bar`
*   **Description:** This region covers the tabs in the main navigation panel (e.g., Navigation, Transactions, Contacts).
*   **Example:**
    ![Navigation Panel Tab Bar](Calibration%20Images/EDNavigationPanel.tab_bar.png)

### Navigation Panel - List

*   **Region:** `EDNavigationPanel.nav_list`
*   **Description:** This region is for the list of destinations that appears in the navigation tab.
*   **Example:**
    ![Navigation Panel List](Calibration%20Images/EDNavigationPanel.nav_list.png)

### Internal Status Panel - Tab Bar

*   **Region:** `EDInternalStatusPanel.tab_bar`
*   **Description:** This region covers the tabs in the internal status panel (the right-hand panel in your cockpit), such as Inventory, Status, etc.
*   **Example:**
    ![Internal Status Panel Tab Bar](Calibration%20Images/EDInternalStatusPanel.tab_bar.png)

### Internal Status Panel - Inventory List

*   **Region:** `EDInternalStatusPanel.inventory_list`
*   **Description:** This region is for the list of items in your ship's inventory.
*   **Example:**
    ![Internal Status Panel Inventory List](Calibration%20Images/EDInternalStatusPanel.inventory_list.png)

### Station Services - Connected To

*   **Region:** `EDStationServicesInShip.connected_to`
*   **Description:** This region reads the name of the station you are currently docked at.
*   **Example:**
    ![Station Services Connected To](Calibration%20Images/EDStationServicesInShip.connected_to.png)

### Station Services - Carrier Admin Header

*   **Region:** `EDStationServicesInShip.carrier_admin_header`
*   **Description:** This region is for the header of the carrier administration screen.
*   **Example:**
    ![Station Services Carrier Admin Header](Calibration%20Images/EDStationServicesInShip.carrier_admin_header.png)

### Station Services - Commodities List

*   **Region:** `EDStationServicesInShip.commodities_list`
*   **Description:** This region covers the list of commodities available in the market.
*   **Example:**
    ![Station Services Commodities List](Calibration%20Images/EDStationServicesInShip.commodities_list.png)

### Station Services - Commodity Quantity

*   **Region:** `EDStationServicesInShip.commodity_quantity`
*   **Description:** This region is used to read the quantity of a selected commodity.
*   **Example:**
    ![Station Services Commodity Quantity](Calibration%20Images/EDStationServicesInShip.commodity_quantity.png)
