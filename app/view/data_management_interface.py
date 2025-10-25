from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFileDialog, QScrollArea, QMessageBox)
from PyQt6.QtGui import QPixmap, QImage
import os
import glob
from pathlib import Path
from ..common.style_sheet import StyleSheet

class ImageThumbnail(QWidget):
    clicked = pyqtSignal(bool)
    
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.is_selected = False
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Image label
        self.image_label = QLabel()
        pixmap = QPixmap(self.image_path)
        scaled_pixmap = pixmap.scaled(QSize(150, 150), Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label.setPixmap(scaled_pixmap)
        
        # Filename label
        filename = os.path.basename(self.image_path)
        name_label = QLabel(filename)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.image_label)
        layout.addWidget(name_label)
        self.setLayout(layout)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selected = not self.is_selected
            self.setStyleSheet(
                "ImageThumbnail { background-color: %s; border: 2px solid %s }" 
                % ("#e0e0e0" if self.is_selected else "transparent",
                   "#2196F3" if self.is_selected else "transparent")
            )
            self.clicked.emit(self.is_selected)

class DataManagementInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_directory = ""
        self.selected_images = set()
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        self.select_folder_btn = QPushButton("Select Folder")
        self.select_folder_btn.clicked.connect(self.selectFolder)
        
        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.clicked.connect(self.deleteSelected)
        self.delete_selected_btn.setEnabled(False)
        
        controls_layout.addWidget(self.select_folder_btn)
        controls_layout.addWidget(self.delete_selected_btn)
        controls_layout.addStretch()
        
        # Scroll area for images
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container for image thumbnails
        self.image_container = QWidget()
        self.image_layout = QHBoxLayout()
        self.image_layout.setSpacing(10)
        self.image_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.image_container.setLayout(self.image_layout)
        
        self.scroll_area.setWidget(self.image_container)
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
        StyleSheet.HOME_INTERFACE.apply(self)
        
    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if folder:
            self.current_directory = folder
            self.loadImages()
            
    def loadImages(self):
        # Clear previous images
        for i in reversed(range(self.image_layout.count())):
            self.image_layout.itemAt(i).widget().setParent(None)
        
        self.selected_images.clear()
        
        # Load all image files
        image_extensions = ['*.png', '*.jpg', '*.jpeg']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(self.current_directory, ext)))
        
        # Create thumbnails
        for image_path in sorted(image_files):
            thumbnail = ImageThumbnail(image_path)
            thumbnail.clicked.connect(lambda checked, path=image_path: self.onImageSelected(path, checked))
            self.image_layout.addWidget(thumbnail)
            
        # Add stretch to keep images left-aligned
        self.image_layout.addStretch()
        
    def onImageSelected(self, image_path, is_selected):
        if is_selected:
            self.selected_images.add(image_path)
        else:
            self.selected_images.discard(image_path)
            
        self.delete_selected_btn.setEnabled(len(self.selected_images) > 0)
        
    def deleteSelected(self):
        if not self.selected_images:
            return
            
        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f'Are you sure you want to delete {len(self.selected_images)} selected items and their related files?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for image_path in self.selected_images:
                self.deleteRelatedFiles(image_path)
            
            self.loadImages()  # Refresh the view
            
    def deleteRelatedFiles(self, image_path):
        # Get the base name without extension
        path = Path(image_path)
        base_name = path.stem
        
        # Find the common part of the filename (e.g., "0001" from "rgb_0001.png")
        # This assumes the base number is at the end of the filename
        import re
        number_match = re.search(r'\d+$', base_name)
        if number_match:
            common_part = number_match.group()
            # Find all files in the directory with this number
            directory = path.parent
            for file_path in directory.glob(f'*{common_part}.*'):
                try:
                    os.remove(str(file_path))
                except Exception as e:
                    QMessageBox.warning(
                        self, 'Deletion Error',
                        f'Error deleting {file_path}: {str(e)}'
                    )