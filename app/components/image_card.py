from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QLabel, QVBoxLayout

from qfluentwidgets import CardWidget, IconWidget, FluentIcon
from ..common.style_sheet import StyleSheet


class ImageCard(CardWidget):
    """A card widget that displays an image with selection overlay."""

    clicked = pyqtSignal()  # emitted when card is clicked
    selectionChanged = pyqtSignal(bool)  # emitted when selection changes

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self._selected = False
        
        # Main layout
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        
        # Image label
        self.imageLabel = QLabel(self)
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imageLabel.setMinimumSize(200, 150)  # adjust as needed
        self.vBoxLayout.addWidget(self.imageLabel)
        
        # Download icon overlay (only shown when selected)
        self.downloadIcon = IconWidget(FluentIcon.DOWNLOAD, self)
        self.downloadIcon.setFixedSize(32, 32)
        self.downloadIcon.hide()
        
        # Load and display the image
        self.loadImage()
        
        # Set object name for styling
        self.setObjectName('imageCard')
        StyleSheet.HOME_INTERFACE.apply(self)
        
        # Make card clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def loadImage(self):
        """Load and scale the image to fit the card."""
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.imageLabel.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.imageLabel.setPixmap(scaled)
            # Position the download icon in the bottom right
            if self.downloadIcon:
                self.downloadIcon.move(
                    self.width() - self.downloadIcon.width() - 8,
                    self.height() - self.downloadIcon.height() - 8
                )

    def setSelected(self, selected: bool):
        """Set the selection state and update visuals."""
        if self._selected == selected:
            return
            
        self._selected = selected
        self.downloadIcon.setVisible(selected)
        self.update()  # force repaint for selection effect
        self.selectionChanged.emit(selected)

    def isSelected(self) -> bool:
        """Get current selection state."""
        return self._selected

    def mousePressEvent(self, e):
        """Handle mouse press - toggle selection on left click."""
        super().mousePressEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            self.setSelected(not self._selected)

    def resizeEvent(self, e):
        """Handle resize - update image scaling."""
        super().resizeEvent(e)
        self.loadImage()

    def paintEvent(self, e):
        """Custom paint to show selection state."""
        super().paintEvent(e)
        if self._selected:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw semi-transparent overlay
            overlay = QColor(0, 120, 212, 40)  # fluent blue, semi-transparent
            painter.fillRect(self.rect(), overlay)
            
            # Draw border
            border = QColor(0, 120, 212)  # fluent blue
            painter.setPen(border)
            painter.drawRect(0, 0, self.width()-1, self.height()-1)