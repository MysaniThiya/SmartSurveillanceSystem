import cv2
from ultralytics import YOLO


class AnimalDetector:
    def __init__(self, model_path="best.pt"):
        self.model = YOLO(model_path)
        self.class_names = ["Elephant", "Cow", "Dog"]
        self.animal_currently_detected = False

    def detect(self, frame, conf_threshold):
        results = self.model(frame, conf=conf_threshold)
        detected = False
        animal_name = None
        box_coords = None

        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            animal_name = self.class_names[cls_id]  # or self.model.names[cls_id]
            x1, y1, x2, y2 = box.xyxy[0]
            box_coords = (int(x1), int(y1), int(x2), int(y2))
            detected = True
            break  # only first detection

        if detected and not self.animal_currently_detected:
            self.animal_currently_detected = True
            return True, animal_name, box_coords

        elif not detected:
            self.animal_currently_detected = False

        return False, None, None