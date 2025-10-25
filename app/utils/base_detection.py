from abc import ABC, abstractmethod
from PyQt6.QtGui import QImage

class BaseDetectionModel(ABC):
    """Abstract base class for detection models."""

    def __init__(self, model_path: str, device: str = 'cpu'):
        self.model_path = model_path
        self.device = device
        self.model = None
        self._load_model()

    @abstractmethod
    def _load_model(self):
        """Load the model. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def predict(self, image):
        """Run prediction on the given image. Must be implemented by subclasses."""
        pass

    def to_qimage(self, detected_image):
        """Convert the detected image (numpy array) to QImage."""
        h, w, c = detected_image.shape
        bytes_per_line = w * c
        return QImage(detected_image.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
