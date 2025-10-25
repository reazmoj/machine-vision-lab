from ultralytics import YOLO
from app.utils.base_detection import BaseDetectionModel

class YOLOv8Model(BaseDetectionModel):
    def _load_model(self):
        self.model = YOLO(self.model_path)

    def predict(self, image):
        result = self.model.predict(image)
        return result[0].plot()
