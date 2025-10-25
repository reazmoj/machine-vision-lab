from PyQt6.QtCore import Qt, pyqtSignal

from PyQt6.QtWidgets import QLabel

class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = None  # Add an image attribute

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def setPixmap(self, pixmap):
        super().setPixmap(pixmap)
        self.image = pixmap  # Store the pixmap in the image attribute