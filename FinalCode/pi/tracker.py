import math
from collections import deque

class CentroidTrack:
    """
    FR-12: Determine Current Movement.
    Stores centroid history to compute direction + speed from consecutive frames.
    """
    def __init__(self, maxlen=15):
        self.points = deque(maxlen=maxlen)
        self.last_box = None
        self.last_seen_frame = -1

    def update(self, cx, cy, box, frame_idx):
        """Update with new centroid from current frame"""
        self.points.append((cx, cy))
        self.last_box = box
        self.last_seen_frame = frame_idx

    def get_motion(self):
        """Calculate delta from last 2 frames"""
        if len(self.points) < 2:
            return 0, 0
        (x1, y1) = self.points[-2]
        (x2, y2) = self.points[-1]
        return (x2 - x1), (y2 - y1)

    def get_direction_label(self):
        """FR-12 Output: Current movement pattern"""
        dx, dy = self.get_motion()
        if abs(dx) < 2 and abs(dy) < 2:
            return "STATIONARY"
        if abs(dx) > abs(dy):
            return "RIGHT" if dx > 0 else "LEFT"
        else:
            return "DOWN" if dy > 0 else "UP"

    def get_speed_px_per_frame(self):
        """FR-12 Output: Current Speed"""
        dx, dy = self.get_motion()
        return math.sqrt(dx*dx + dy*dy)

def match_single_object(prev_track, new_cx, new_cy, max_dist=80):
    """Simple matching: if new centroid is close enough to previous, treat as same object"""
    if not prev_track.points:
        return True
    px, py = prev_track.points[-1]
    dist = math.sqrt((new_cx - px)**2 + (new_cy - py)**2)
    return dist < max_dist