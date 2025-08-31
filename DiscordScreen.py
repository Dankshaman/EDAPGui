from __future__ import annotations
import cv2
import win32gui
from numpy import array
import mss


def find_discord_hwnd():
    """
    Finds the hwnd of the Discord window.
    """
    def enum_windows_proc(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "discord" in title.lower():
                lParam.append(hwnd)

    hwnds = []
    win32gui.EnumWindows(enum_windows_proc, hwnds)
    return hwnds[0] if hwnds else None


class DiscordScreen:
    def __init__(self):
        self.mss = mss.mss()
        self.hwnd = find_discord_hwnd()
        if self.hwnd is None:
            raise Exception("Could not find Discord window. Please make sure Discord is running.")

        self.rect = win32gui.GetWindowRect(self.hwnd)
        self.screen_width = self.rect[2] - self.rect[0]
        self.screen_height = self.rect[3] - self.rect[1]

    def get_screen_rect_pct(self, rect_pct):
        """ Grabs a screenshot of the window and returns the selected region as an image.
        @param rect_pct: A rect array ([L, T, R, B]) in percent (0.0 - 1.0)
        @return: An image defined by the region.
        """
        abs_rect = self.screen_rect_to_abs(rect_pct)

        monitor = {
            "top": self.rect[1] + abs_rect[1],
            "left": self.rect[0] + abs_rect[0],
            "width": abs_rect[2] - abs_rect[0],
            "height": abs_rect[3] - abs_rect[1],
        }

        image = array(self.mss.grab(monitor))
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        return image
    
    def get_full_screen(self):
        """ Grabs a screenshot of the full window and returns the image.
        """
        monitor = {
            "top": self.rect[1],
            "left": self.rect[0],
            "width": self.screen_width,
            "height": self.screen_height,
        }
        image = array(self.mss.grab(monitor))
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        return image

    def screen_rect_to_abs(self, rect):
        """ Converts and array of real percentage screen values to int absolutes.
        @param rect: A rect array ([L, T, R, B]) in percent (0.0 - 1.0)
        @return: A rect array ([L, T, R, B]) in pixels
        """
        abs_rect = [int(rect[0] * self.screen_width), int(rect[1] * self.screen_height),
                    int(rect[2] * self.screen_width), int(rect[3] * self.screen_height)]
        return abs_rect
    
    def abs_rect_to_pct(self, rect):
        """ Converts and array of absolute pixel values to percentage screen values.
        @param rect: A rect array ([L, T, R, B]) in pixels
        @return: A rect array ([L, T, R, B]) in percent (0.0 - 1.0)
        """
        pct_rect = [rect[0] / self.screen_width, rect[1] / self.screen_height,
                    rect[2] / self.screen_width, rect[3] / self.screen_height]
        return pct_rect
