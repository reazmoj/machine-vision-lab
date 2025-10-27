from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QScrollArea, QApplication, QFrame, QGridLayout
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
from qfluentwidgets import (
    PushButton, MessageBox, StrongBodyLabel, FlowLayout,
    CardWidget, IconWidget, FluentIcon, SubtitleLabel,
    TransparentToolButton, ScrollArea, ImageLabel, Theme,
    HorizontalFlipView, ToolButton, ToolTipPosition
)
import os
import glob
from pathlib import Path
import re
from ..common.style_sheet import StyleSheet


class DataManagementInterface(QWidget):
    """Modern data management interface with grid and slideshow views.
    
    Features:
    - Grid view of image thumbnails
    - Slideshow viewer with prev/next navigation
    - Single-click selection in both views
    - Delete selected images
    - Selection synced between grid and slideshow
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('dataManagementInterface')

        # State tracking
        self.current_directory = ""
        self.image_list = []  # ordered list of image paths
        self.current_index = -1  # current slideshow index
        self.image_cards = []  # list of ImageCard widgets
        self.selected_images = set()  # paths of selected images
        
        self.initUI()
        
    def initUI(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        # Dark theme header bar
        header = QFrame(self)
        header.setObjectName('headerFrame')
        header.setStyleSheet("""
            #headerFrame {
                background-color: #1e1e1e;
                border-bottom: 1px solid #333333;
            }
        """)
        header.setFixedHeight(50)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        # Header bar buttons
        self.select_folder_btn = ToolButton(FluentIcon.FOLDER_ADD, self)
        self.select_folder_btn.setIconSize(QSize(20, 20))
        self.select_folder_btn.setToolTip("Select Folder")
        self.select_folder_btn.setFixedSize(40, 40)
        self.select_folder_btn.clicked.connect(self.selectFolder)
        
        self.selected_count = StrongBodyLabel("0 Selected", self)
        self.selected_count.setStyleSheet("color: #ffffff")
        
        self.delete_selected_btn = ToolButton(FluentIcon.DELETE, self)
        self.delete_selected_btn.setIconSize(QSize(20, 20))
        self.delete_selected_btn.setToolTip("Delete Selected")
        self.delete_selected_btn.setFixedSize(40, 40)
        self.delete_selected_btn.setEnabled(False)
        self.delete_selected_btn.clicked.connect(self.deleteSelected)

        header_layout.addWidget(self.select_folder_btn)
        header_layout.addStretch()
        header_layout.addWidget(self.selected_count)
        header_layout.addWidget(self.delete_selected_btn)
        
        root.addWidget(header)

        # Image viewer area
        viewer_container = QFrame(self)
        viewer_container.setObjectName('viewerContainer')
        viewer_container.setStyleSheet("""
            #viewerContainer {
                background-color: #1e1e1e;
            }
        """)
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)
        
        # Main image display
        self.viewer_frame = QFrame()
        self.viewer_frame.setObjectName('imageViewer')
        self.viewer_frame.setFixedHeight(500)  # Fixed height for stability
        self.viewer_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        viewer_inner = QVBoxLayout(self.viewer_frame)
        viewer_inner.setContentsMargins(0, 0, 0, 0)
        viewer_inner.setSpacing(0)
        
        # Container for image to maintain aspect ratio
        self.image_container = QFrame(self.viewer_frame)
        self.image_container.setObjectName('imageContainer')
        self.image_container.setStyleSheet("""
            #imageContainer {
                background-color: #1a1a1a;
            }
        """)
        
        container_layout = QHBoxLayout(self.image_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_label = ImageLabel(self.image_container)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(QSize(400, 400))
        self.image_label.mousePressEvent = self.onImageLabelClicked  # Add click handler
        container_layout.addWidget(self.image_label)
        
        viewer_inner.addWidget(self.image_container, 1)
        
        # Navigation overlay
        nav_overlay = QHBoxLayout()
        nav_overlay.setContentsMargins(16, 0, 16, 0)
        
        self.prev_btn = TransparentToolButton(FluentIcon.LEFT_ARROW, self)
        self.prev_btn.setIconSize(QSize(32, 32))
        self.prev_btn.clicked.connect(self.showPreviousImage)
        
        self.next_btn = TransparentToolButton(FluentIcon.RIGHT_ARROW, self)
        self.next_btn.setIconSize(QSize(32, 32))
        self.next_btn.clicked.connect(self.showNextImage)
        
        nav_overlay.addWidget(self.prev_btn)
        nav_overlay.addStretch()
        nav_overlay.addWidget(self.next_btn)
        
        viewer_inner.addLayout(nav_overlay)
        
        # Image counter
        counter = QHBoxLayout()
        self.position_label = SubtitleLabel("0 / 0")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_label.setStyleSheet("color: #ffffff")
        counter.addWidget(self.position_label)
        
        viewer_layout.addWidget(self.viewer_frame)
        viewer_layout.addLayout(counter)
        viewer_layout.addSpacing(8)
        
        root.addWidget(viewer_container)

        # Grid view of thumbnails
        grid_container = QFrame(self)
        grid_container.setObjectName('gridContainer')
        grid_container.setStyleSheet("""
            #gridContainer {
                background-color: #1e1e1e;
                border-top: 1px solid #333333;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(16, 16, 16, 16)
        grid_layout.setSpacing(0)
        
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        scroll_content = QWidget(scroll)
        scroll_content.setObjectName('gridContent')
        
        self.grid_layout = FlowLayout(scroll_content)
        self.grid_layout.setHorizontalSpacing(16)
        self.grid_layout.setVerticalSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        scroll.setWidget(scroll_content)
        grid_layout.addWidget(scroll)
        
        root.addWidget(grid_container, 1)
        self.setLayout(root)

    def _on_viewer_clicked(self, event):
        """Toggle selection when clicking the viewer image."""
        if event.button() == Qt.MouseButton.LeftButton and self.current_index >= 0:
            card = self.image_cards[self.current_index]
            card.setSelected(not card.isSelected())
            self.updateDeleteButtonState()

    # ---------- Folder / loading ----------
    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if folder:
            self.current_directory = folder
            self.loadImages()

    def _create_item_icon(self, image_path, selected=False):
        """Create a QIcon for a thumbnail. If selected=True, draw a small check badge."""
        # Local imports to avoid touching top-level imports
        from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont
        from PyQt6.QtCore import QRect

        pix = QPixmap(image_path)
        if pix.isNull():
            return QIcon()
        thumb = pix.scaled(320, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        if selected:
            try:
                painter = QPainter(thumb)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                badge_size = int(min(thumb.width(), thumb.height()) * 0.28)
                margin = 8
                rect = QRect(thumb.width() - badge_size - margin, margin, badge_size, badge_size)
                color = QColor(0, 120, 215, 220)  # accent blue semi-transparent
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(rect)
                # draw checkmark
                painter.setPen(QColor(255, 255, 255))
                font = QFont()
                font.setBold(True)
                font.setPointSize(int(badge_size * 0.55))
                painter.setFont(font)
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "✓")
                painter.end()
            except Exception:
                # if anything fails, ignore overlay
                pass

        return QIcon(thumb)

    def loadImages(self):
        """Load images from current_directory into the grid and viewer."""
        # Clear existing state
        for card in self.image_cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.image_cards.clear()
        self.image_list.clear()
        self.selected_images.clear()
        self.current_index = -1

        # Find image files
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp']
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(self.current_directory, ext)))
        files = sorted(files)

        # Create cards and collect paths
        from ..components.image_card import ImageCard
        for path in files:
            card = ImageCard(path, self)
            card.clicked.connect(lambda p=path: self.onImageClicked(p))
            card.selectionChanged.connect(lambda sel, p=path: self.onImageSelectionChanged(p, sel))
            self.grid_layout.addWidget(card)
            self.image_cards.append(card)
            self.image_list.append(path)

        # Show first image if any loaded
        if self.image_list:
            self.showImage(self.image_list[0])
        else:
            self.position_label.setText("0 / 0")
            self.image_label.clear()

        self.updateUI()

    def showImage(self, path):
        """Show an image in the viewer and update current index."""
        try:
            idx = self.image_list.index(path)
        except ValueError:
            return

        self.current_index = idx
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            # Get container size for proper scaling
            container_size = self.image_container.size()
            # Scale image to fit container while preserving aspect ratio
            scaled = pixmap.scaled(
                container_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
            
            # Add selection overlay if image is selected
            if path in self.selected_images:
                self.showSelectionOverlay()
        else:
            self.image_label.clear()
            self.image_label.setText("Failed to load image")

        self.position_label.setText(f"{idx + 1} / {len(self.image_list)}")

    def showSelectionOverlay(self):
        """Show selection overlay on the current image."""
        if not self.image_label.pixmap():
            return
            
        # Create a new pixmap with selection overlay
        pixmap = self.image_label.pixmap()
        overlay = QPixmap(pixmap.size())
        overlay.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(overlay)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw semi-transparent blue overlay
        overlay_color = QColor(0, 120, 212, 40)
        painter.fillRect(overlay.rect(), overlay_color)
        
        # Draw border
        border_color = QColor(0, 120, 212)
        painter.setPen(border_color)
        painter.drawRect(0, 0, overlay.width()-1, overlay.height()-1)
        
        painter.end()
        
        # Combine original image with overlay
        result = QPixmap(pixmap.size())
        result.fill(Qt.GlobalColor.transparent)
        
        final_painter = QPainter(result)
        final_painter.drawPixmap(0, 0, pixmap)
        final_painter.drawPixmap(0, 0, overlay)
        final_painter.end()
        
        self.image_label.setPixmap(result)
        
    def showPreviousImage(self):
        """Show the previous image in the list."""
        if not self.image_list or self.current_index <= 0:
            return
        self.showImage(self.image_list[self.current_index - 1])
        
    def showNextImage(self):
        """Show the next image in the list."""
        if not self.image_list or self.current_index >= len(self.image_list) - 1:
            return
        self.showImage(self.image_list[self.current_index + 1])

    def onImageClicked(self, path):
        """Handle click on an image in the grid view."""
        self.showImage(path)  # Show the image in viewer
        
    def onImageLabelClicked(self, event):
        """Handle click on the image in the slider view."""
        if event.button() == Qt.MouseButton.LeftButton and self.current_index >= 0:
            path = self.image_list[self.current_index]
            is_selected = path in self.selected_images
            self.toggleImageSelection(path, not is_selected)

    def toggleImageSelection(self, path, selected):
        """Toggle selection state of an image."""
        # Update internal state
        if selected:
            self.selected_images.add(path)
        else:
            self.selected_images.discard(path)
            
        # Update grid view
        try:
            idx = self.image_list.index(path)
            card = self.image_cards[idx]
            card.setSelected(selected)
        except (ValueError, IndexError):
            pass
            
        # Update slider view if this is the current image
        if self.current_index >= 0 and path == self.image_list[self.current_index]:
            self.showImage(path)  # This will handle showing selection state
            
        self.updateUI()
        
    def onImageSelectionChanged(self, path, selected):
        """Handle selection change from a card."""
        self.toggleImageSelection(path, selected)

    def updateUI(self):
        """Update UI elements based on current state."""
        # Update selection count and delete button
        count = len(self.selected_images)
        self.selected_count.setText(f"{count} Selected")
        self.delete_selected_btn.setEnabled(count > 0)
        
        # Update current image selection state if needed
        if self.current_index >= 0:
            current_path = self.image_list[self.current_index]
            if current_path in self.selected_images:
                self.showSelectionOverlay()

    def resizeEvent(self, e):
        """Handle resize - update current image scaling."""
        super().resizeEvent(e)
        # On resize, rescale the current image if one is shown
        if self.current_index >= 0 and self.image_list:
            current_path = self.image_list[self.current_index]
            self.showImage(current_path)

    # ---------- Deletion logic ----------
    def deleteSelected(self):
        """Delete selected images and their related files."""
        if not self.selected_images:
            return

        # Collect all related files
        files_to_delete = set()
        base_numbers = set()
        
        # First, extract base numbers from selected files
        for path in self.selected_images:
            filename = Path(path).stem  # Get filename without extension
            # Try to find the number pattern (assumes number at end of filename)
            match = re.search(r'(\d+)$', filename)
            if match:
                base_numbers.add(match.group(1))
        
        # Find all related files with the same base numbers
        if base_numbers:
            dir_path = Path(self.current_directory)
            for file_path in dir_path.glob('*'):
                if file_path.is_file():
                    filename = file_path.stem
                    for base_num in base_numbers:
                        if filename.endswith(base_num):
                            files_to_delete.add(str(file_path))
                            break

        # Ask for confirmation
        count = len(files_to_delete)
        dlg = MessageBox(
            "Confirm Delete",
            f"Delete {count} file(s)?\nThis will delete all related files with the same base numbers.",
            self
        )
        if dlg.exec():
            # Delete the files
            errors = []
            for path in files_to_delete:
                try:
                    Path(path).unlink()
                except Exception as e:
                    errors.append(f"Failed to delete {path}: {str(e)}")
            
            # Show any errors
            if errors:
                MessageBox(
                    "Delete Results",
                    "Some files could not be deleted:\n" + "\n".join(errors),
                    self
                ).exec()

            # Reload the view
            self.loadImages()
