from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
import torch
import os
from app.utils.reid_utils import *
from ultralytics import YOLO

class ReIdModelInfrence(QThread):
    """AI Model Thread Runing"""

    process_finished = pyqtSignal(object)

    def __init__(self, model_path: str, input_image: str, gallery_path: str, device='cpu', parent=None):

        super().__init__(parent=parent)
        self.input_image = input_image
        self.gallery_path = gallery_path
        self.device = device
        self.gallery_features = []
        self.yolo_model = YOLO('app/models/bestyolo11n.pt')
        self.geo_model = torch.load(model_path, weights_only=False)
    

        self.geo_model = self.geo_model.eval()
    def run(self):
        # self.result = 'D:/projects/pyqt6/project/app/view/resource/images/detection_images'
        
        frame = cv2.imread(self.input_image)
        frame_shape = frame.shape[:2]

        detect_result = self.yolo_model.predict(source=frame, conf=0.3)

        buildings, metadata = extract_buildings(detect_result, frame, frame_shape)

        self.extract_gallery_features()

        distance = process_buildings(buildings, 
                                     self.gallery_features, 
                                     metadata, 
                                     frame,
                                     self.geo_model)

        metadata = [
        {**m, "distance": d.item()} 
        for d, m in zip(distance, metadata)
        ]

        final = add_distance_to_image(frame,metadata)

        final = self.to_qimage(final)

        self.process_finished.emit(final)

    def extract_gallery_features(self):
        for i in os.listdir(self.gallery_path):
            name = os.path.join(self.gallery_path,i)
            sat_tensor = read_image(name)
            print(sat_tensor.shape)
            with torch.no_grad():
                _, base_features = self.geo_model(None,sat_tensor)
            self.gallery_features.append(normalize_and_flatten(base_features).view(-1,1))

    
    def to_qimage(self, detected_image):
        """Convert the detected image (numpy array) to QImage."""
        h, w, c = detected_image.shape
        bytes_per_line = w * c
        return QImage(detected_image.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        
    def setModel(self):
        pass 