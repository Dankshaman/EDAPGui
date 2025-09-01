import tkinter as tk
from tkinter import messagebox
import json
from DiscordScreen import DiscordScreen
from PIL import Image, ImageTk
import cv2


class CalibrationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord OCR Calibration")

        try:
            self.screen = DiscordScreen()
            self.screenshot = self.screen.get_full_screen()
            self.screenshot_pil = Image.fromarray(cv2.cvtColor(self.screenshot, cv2.COLOR_BGR2RGB))
        except Exception as e:
            messagebox.showerror("Error", f"Could not capture Discord window: {e}")
            self.root.destroy()
            return

        self.image_tk = ImageTk.PhotoImage(self.screenshot_pil)

        self.canvas = tk.Canvas(root, width=self.screen.screen_width, height=self.screen.screen_height)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)

        self.rect = None
        self.start_x = None
        self.start_y = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.save_button = tk.Button(root, text="Save Region", command=self.save_region)
        self.save_button.pack()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)

    def on_mouse_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline='red', width=2)

    def on_button_release(self, event):
        self.end_x = event.x
        self.end_y = event.y

    def save_region(self):
        if not self.start_x or not self.start_y or not self.end_x or not self.end_y:
            messagebox.showwarning("Warning", "Please select a region first.")
            return

        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)

        abs_rect = [x1, y1, x2, y2]
        pct_rect = self.screen.abs_rect_to_pct(abs_rect)

        config_data = {
            "region": {
                "rect": pct_rect
            }
        }

        with open("discord_config.json", "w") as f:
            json.dump(config_data, f, indent=4)

        messagebox.showinfo("Success", "Region saved to discord_config.json")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CalibrationTool(root)
    root.mainloop()
