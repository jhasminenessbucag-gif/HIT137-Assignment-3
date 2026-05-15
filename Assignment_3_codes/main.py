import tkinter as tk # For GUI
import ctypes # For DPI awareness on Windows
from game_app import GameApp

# Set DPI awareness for better scaling on high-DPI displays (Windows)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Main entry point
def main():
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()

# Run the application when the script is executed directly
if __name__ == "__main__":
    main()