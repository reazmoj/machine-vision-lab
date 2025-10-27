from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QFrame

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
        self.vBoxLayout.setContentsMargins(8, 8, 8, 8)
        self.vBoxLayout.setSpacing(4)
        
        # Image container for centering
        self.image_container = QFrame(self)
        self.image_container.setFixedSize(320, 240)
        self.image_container.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 4px;
            }
        """)
        
        # Image label - no layout, we'll position it manually
        self.imageLabel = QLabel(self.image_container)
        self.imageLabel.setStyleSheet("background: transparent;")
        
        # File name label
        self.nameLabel = QLabel(self)
        self.nameLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nameLabel.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
                padding: 4px;
                background-color: transparent;
            }
        """)
        import os
        self.nameLabel.setText(os.path.basename(image_path))
        self.nameLabel.setFixedWidth(320)  # Match image width
        self.nameLabel.setWordWrap(True)  # Enable word wrap for long names
        
        self.vBoxLayout.addWidget(self.image_container)
        self.vBoxLayout.addWidget(self.nameLabel)
        
        # Delete icon overlay (only shown when selected)
        self.deleteIcon = IconWidget(FluentIcon.DELETE, self)
        self.deleteIcon.setFixedSize(32, 32)
        icon_color = QColor(255, 255, 255)  # White icon
        self.deleteIcon.setIcon(FluentIcon.DELETE)
        self.deleteIcon.hide()
        
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
            # Get the container size (parent of imageLabel)
            container_size = self.imageLabel.parent().size()
            
            # Scale image to fit container
            scaled = pixmap.scaled(
                container_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Calculate position to center the image
            x = (container_size.width() - scaled.width()) // 2
            y = (container_size.height() - scaled.height()) // 2
            
            # Set geometry to position the image label
            self.imageLabel.setGeometry(x, y, scaled.width(), scaled.height())
            self.imageLabel.setPixmap(scaled)
            
            # Position the delete icon
            if self.deleteIcon:
                self.deleteIcon.move(
                    (self.width() - self.deleteIcon.width()) // 2,
                    (self.height() - self.deleteIcon.height()) // 2)

    def setSelected(self, selected: bool):
        """Set the selection state and update visuals."""
        if self._selected == selected:
            return
            
        self._selected = selected
        self.deleteIcon.setVisible(selected)
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