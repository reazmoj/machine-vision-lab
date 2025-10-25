from app.utils.rcnn_model import FasterRCNNModel
from app.utils.yolov5_model import YOLOv5Model
from app.utils.yolov8_model import YOLOv8Model
from app.utils.yolov9_model import YOLOv9Model


class DetectionModelFactory:
    @staticmethod
    def create(model_type: str, model_path: str, device: str = 'cpu'):
        if model_type == 'yolov8':
            return YOLOv8Model(model_path, device)
        elif model_type == 'yolov5':
            return YOLOv5Model(model_path, device)
        elif model_type == 'yolov9':
            return YOLOv9Model(model_path, device)
        elif model_type == 'rcnn':
            return FasterRCNNModel(model_path, device)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
