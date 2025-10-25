import torch

from app.utils.base_detection import BaseDetectionModel

class YOLOv9Model(BaseDetectionModel):
    def _load_model(self):
        self.model = torch.hub.load('WongKinYiu/yolov9', 
                                    'custom', 
                                    path=self.model_path, 
                                    device=self.device)

    def predict(self, image):
        results = self.model(image)
        return results.render()[0]
