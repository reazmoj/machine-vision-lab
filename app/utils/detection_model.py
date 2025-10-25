from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
import cv2

from app.utils.detection_factory import DetectionModelFactory

class DetctionModelInfrence(QThread):
    """AI Model Thread Runing"""

    detection_finished = pyqtSignal(object)

    def __init__(self, model_path: str, input_image: str, model_type:str, device='cpu', parent=None):

        super().__init__(parent=parent)
        self.input_image = input_image
        self.device = device
        self.model = DetectionModelFactory.create(model_type, model_path, device)
    
    def run(self):
        image = cv2.imread(self.input_image)

        # Run inference
        detected_image = self.model.predict(image)

        # Convert to QImage
        q_image = self.model.to_qimage(detected_image)

        self.detection_finished.emit(q_image)