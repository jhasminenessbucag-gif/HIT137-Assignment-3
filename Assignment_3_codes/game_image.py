import cv2 # OpenCV for image processing
import numpy as np # NumPy for array manipulation
from PIL import Image, ImageTk # PIL for image conversion to Tkinter format

# GameImage encapsulates image data, difference regions, and click validation
# This class uses a constructor to initialize the image model and internal state
class GameImage:
    PROXIMITY = 30 

    def __init__(self, filepath):
        self.filepath = filepath
        raw = cv2.imread(filepath)
        if raw is None: raise ValueError(f"Cannot load image: {filepath}")
        self.original = self._resize(raw, target_w=520, target_h=420)
        self.modified = None
        self.regions = []
        self.found = []

    def _resize(self, img, target_w, target_h):
        # scale the image to fit the GUI canvas while preserving aspect ratio
        h, w = img.shape[:2]
        scale = min(target_w / w, target_h / h)
        return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    def apply_differences(self, generator):
        # class interaction: GameImage delegates generation to a DifferenceGenerator object
        # this method updates internal state with the modified image and random regions
        self.modified, self.regions, self.diff_types = generator.generate(self.original)
        self.found = [False] * len(self.regions)

    def check_click(self, cx, cy):
        # return the index of a difference region if the click is close enough
        for i, (x, y, w, h) in enumerate(self.regions):
            if self.found[i]: continue
            dist = ((cx - (x + w // 2)) ** 2 + (cy - (y + h // 2)) ** 2) ** 0.5
            if dist <= self.PROXIMITY + max(w, h) // 2: return i
        return -1

    def mark_found(self, index, color):
        # draw a marker circle around the found difference on both displays
        x, y, w, h = self.regions[index]
        center = (x + w // 2, y + h // 2)
        radius = max(w, h) // 2 + 5
        cv2.circle(self.original, center, radius, color, 2, lineType=cv2.LINE_AA)
        cv2.circle(self.modified, center, radius, color, 2, lineType=cv2.LINE_AA)
        self.found[index] = True

    def reveal_all(self):
        # reveal all remaining regions by drawing markers on both images
        for i in range(len(self.regions)):
            if not self.found[i]: 
                self.mark_found(i, (255, 0, 0))

    def all_found(self): return all(self.found)
    def count_found(self): return sum(self.found)

    def to_tk_image(self, cv_img, display_w, display_h):
        # convert the OpenCV image to a Tkinter PhotoImage and preserve aspect ratio
        h, w = cv_img.shape[:2]
        scale = min(display_w / w, display_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(cv_img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        bg = Image.new("RGB", (display_w, display_h), (245, 240, 248)) 
        ox, oy = (display_w - new_w) // 2, (display_h - new_h) // 2
        bg.paste(pil_img, (ox, oy))
        self._last_offset = (ox, oy, scale)
        return ImageTk.PhotoImage(bg)

    def canvas_to_image_coords(self, cx, cy, display_w, display_h):
        if not hasattr(self, '_last_offset'): return cx, cy
        ox, oy, scale = self._last_offset
        return int((cx - ox) / scale), int((cy - oy) / scale)