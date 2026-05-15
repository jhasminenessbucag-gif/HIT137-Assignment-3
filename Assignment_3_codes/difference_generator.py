import cv2
import numpy as np
import random

# Base class for all difference types. This defines the polymorphic interface
# Inheritance is used so each subclass provides its own apply() implementation
class Difference:
    def apply(self, img, region):
        raise NotImplementedError

    def get_name(self):
        raise NotImplementedError

# THREE ALTERATION TYPES USED: each modifies the image in a distinct way to create a difference

# 1. SaturationDiff changes the saturation channel of a rectangular patch
class SaturationDiff(Difference):
    def apply(self, img, region):
        x, y, w, h = region
        patch = img[y:y+h, x:x+w].copy()
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).astype(int) # convert to int for safe manipulation
        drain = random.choice([45, 55, -45, -55]) # randomly increase or decrease saturation by a noticeable amount
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] + drain, 0, 255) # apply the saturation change and clip to valid range
        img[y:y+h, x:x+w] = cv2.cvtColor(hsv.astype('uint8'), cv2.COLOR_HSV2BGR) # convert back to BGR and place it in the modified image

    def get_name(self):
        return "Saturation"

# 2. SharpenDiff applies a subtle sharpening filter to a patch
class SharpenDiff(Difference):
    def apply(self, img, region):
        x, y, w, h = region
        patch = img[y:y+h, x:x+w].copy()
        kernel = np.array([[ 0, -1,  0], # 
                           [-1,  5, -1],
                           [ 0, -1,  0]], dtype=np.float32) # a common sharpening kernel that emphasizes edges
        sharpened = cv2.filter2D(patch, -1, kernel) # apply the sharpening filter to the patch
        # Blend at ~60% strength so it's visible but not too obvious
        img[y:y+h, x:x+w] = cv2.addWeighted(patch, 0.4, sharpened, 0.6, 0) # blend the sharpened patch with the original to create a more natural difference

    def get_name(self):
        return "Sharpen"

# 3. GammaDiff changes brightness using gamma correction inside the patch
class GammaDiff(Difference):
    def apply(self, img, region):
        x, y, w, h = region
        patch = img[y:y+h, x:x+w].copy()
        gamma = random.choice([1.45, 1.55, 0.60, 0.65]) # randomly brighten (gamma > 1) or darken (gamma < 1) the patch by a noticeable amount
        inv_gamma = 1.0 / gamma # calculate the inverse gamma for the LUT
        lut = np.array([    # create a lookup table for gamma correction to apply to the patch
            ((i / 255.0) ** inv_gamma) * 255
            for i in range(256)
        ], dtype='uint8') # apply the gamma correction using the LUT, which is much faster than per-pixel operations
        img[y:y+h, x:x+w] = cv2.LUT(patch, lut) # apply the gamma correction to the patch and place it in the modified image

    def get_name(self):
        return "Gamma"

# DifferenceGenerator places 5 non-overlapping regions and applies random alterations
class DifferenceGenerator:
    PATCH_W = 38
    PATCH_H = 38
    NUM_DIFFS = 5

    def __init__(self):
        # constructor builds a list of polymorphic Difference objects
        # each object shares the same interface but implements apply() differently
        self.preset_types = [
            SaturationDiff(),
            SharpenDiff(),
            GammaDiff(),
            SaturationDiff(),  # reused so there are exactly 5 alterations
            SharpenDiff(),     # reused so there are exactly 5 alterations
        ]

    def _overlaps(self, r1, r2, margin=20):
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2
        # return True if two regions overlap or are too close
        return not (
            x1 + w1 + margin <= x2 or
            x2 + w2 + margin <= x1 or
            y1 + h1 + margin <= y2 or
            y2 + h2 + margin <= y1
        )

    def _pick_regions(self, img_h, img_w):
        placed = []
        attempts = 0
        # pick up to NUM_DIFFS random locations, ensuring they don't overlap
        while len(placed) < self.NUM_DIFFS and attempts < 1000:
            attempts += 1
            x = random.randint(0, img_w - self.PATCH_W)
            y = random.randint(0, img_h - self.PATCH_H)
            region = (x, y, self.PATCH_W, self.PATCH_H)
            if all(not self._overlaps(region, p) for p in placed):
                placed.append(region)
        return placed

    def generate(self, original_img):
        # generate exactly NUM_DIFFS altered regions on a modified copy of the original
        modified = original_img.copy()
        h, w = modified.shape[:2]
        regions = self._pick_regions(h, w)
        active_diffs = self.preset_types.copy()
        random.shuffle(active_diffs)
        used_types = []
        for i, region in enumerate(regions): 
            diff = active_diffs[i]
            diff.apply(modified, region)
            used_types.append(diff)
        return modified, regions, used_types