from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QMessageBox, QListWidget, QListWidgetItem, QSlider, QAbstractItemView, QComboBox
)
from qfluentwidgets import PushButton
from PyQt6.QtGui import QPixmap, QIcon
import os
import glob
from pathlib import Path
import re
from ..common.style_sheet import StyleSheet


class DataManagementInterface(QWidget):
    """A two-pane data manager: left is a thumbnail list, right is a slideshow viewer.

    Features:
    - Select folder to load images
    - Thumbnail list with multi-selection (Ctrl/Shift)
    - Viewer with prev/next and slider
    - View mode: All images or Selected images
    - Delete selected images and all related files that share the same identifier
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('dataManagementInterface')  # required by qfluentwidgets

        self.current_directory = ""
        self.image_list = []  # ordered list of image paths

        self.initUI()

    def initUI(self):
        root = QVBoxLayout(self)

        # Top controls
        top = QHBoxLayout()
        self.select_folder_btn = PushButton(self.tr("Select Folder"), self)
        self.select_folder_btn.clicked.connect(self.selectFolder)

        self.view_mode = QComboBox()
        self.view_mode.addItems(["All Images", "Selected Images"])
        self.view_mode.currentIndexChanged.connect(self.onViewModeChanged)

        self.delete_selected_btn = PushButton(self.tr("Delete Selected"), self)
        self.delete_selected_btn.clicked.connect(self.deleteSelected)
        self.delete_selected_btn.setEnabled(False)

        top.addWidget(self.select_folder_btn)
        top.addWidget(self.view_mode)
        top.addStretch()
        top.addWidget(self.delete_selected_btn)

        # Main area: thumbnails on left, viewer on right
        main = QHBoxLayout()

        # Thumbnail list
        self.thumb_list = QListWidget()
        self.thumb_list.setObjectName('thumbnailList')
        self.thumb_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.thumb_list.setIconSize(QSize(160, 120))
        self.thumb_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.thumb_list.setMovement(QListWidget.Movement.Static)
        self.thumb_list.setSpacing(8)
        self.thumb_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.thumb_list.itemSelectionChanged.connect(self.onSelectionChanged)
        self.thumb_list.itemDoubleClicked.connect(self.onItemDoubleClicked)

        # Viewer area
        viewer_layout = QVBoxLayout()
        self.viewer_label = QLabel("No image")
        self.viewer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viewer_label.setMinimumSize(320, 240)

        controls = QHBoxLayout()
        self.prev_btn = PushButton("◀", self)
        self.prev_btn.clicked.connect(self.showPrev)
        self.next_btn = PushButton("▶", self)
        self.next_btn.clicked.connect(self.showNext)

        self.index_slider = QSlider(Qt.Orientation.Horizontal)
        self.index_slider.setMinimum(0)
        self.index_slider.setSingleStep(1)
        self.index_slider.valueChanged.connect(self.onSliderMoved)

        controls.addWidget(self.prev_btn)
        controls.addWidget(self.index_slider)
        controls.addWidget(self.next_btn)

        viewer_layout.addWidget(self.viewer_label)
        viewer_layout.addLayout(controls)

        main.addWidget(self.thumb_list, 40)
        main.addLayout(viewer_layout, 60)

        root.addLayout(top)
        root.addLayout(main)

        self.setLayout(root)
        StyleSheet.HOME_INTERFACE.apply(self)

    # ---------- Folder / loading ----------
    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if folder:
            self.current_directory = folder
            self.loadImages()

    def loadImages(self):
        self.thumb_list.clear()
        self.image_list = []
        # common image extensions
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp']
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(self.current_directory, ext)))
        files = sorted(files)

        for p in files:
            item = QListWidgetItem()
            qpix = QPixmap(p)
            if not qpix or qpix.isNull():
                icon = QIcon()
            else:
                icon = QIcon(qpix.scaled(320, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            item.setIcon(icon)
            item.setText(os.path.basename(p))
            item.setData(Qt.ItemDataRole.UserRole, p)
            item.setToolTip(p)
            self.thumb_list.addItem(item)
            self.image_list.append(p)

        # slider range
        self.index_slider.setMaximum(max(0, len(self.image_list) - 1))
        if self.image_list:
            self.showImageAt(0)
        self.updateDeleteButtonState()

    # ---------- Selection / view mode ----------
    def onSelectionChanged(self):
        selected = self.getSelectedImagePaths()
        self.updateDeleteButtonState()
        # If in 'Selected Images' view and there is selection, jump viewer to first selected
        if self.view_mode.currentText() == 'Selected Images' and selected:
            try:
                idx = self.image_list.index(selected[0])
                self.index_slider.blockSignals(True)
                self.index_slider.setValue(idx)
                self.index_slider.blockSignals(False)
                self.showImageAt(idx)
            except ValueError:
                pass

    def onItemDoubleClicked(self, item):
        p = item.data(Qt.ItemDataRole.UserRole)
        try:
            idx = self.image_list.index(p)
            self.index_slider.setValue(idx)
            self.showImageAt(idx)
        except ValueError:
            pass

    def onViewModeChanged(self, _):
        # If switched to Selected Images but none selected, disable viewer controls
        self.updateDeleteButtonState()

    def getSelectedImagePaths(self):
        items = self.thumb_list.selectedItems()
        return [it.data(Qt.ItemDataRole.UserRole) for it in items]

    def updateDeleteButtonState(self):
        self.delete_selected_btn.setEnabled(len(self.getSelectedImagePaths()) > 0)

    # ---------- Viewer controls ----------
    def showImageAt(self, index):
        if not self.image_list:
            self.viewer_label.setText('No image')
            return
        index = max(0, min(index, len(self.image_list) - 1))
        path = self.image_list[index]
        pix = QPixmap(path)
        if pix and not pix.isNull():
            scaled = pix.scaled(self.viewer_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.viewer_label.setPixmap(scaled)
        else:
            self.viewer_label.setText('Unable to load image')

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # refresh current image to fit new size
        self.showImageAt(self.index_slider.value())

    def showPrev(self):
        v = max(0, self.index_slider.value() - 1)
        self.index_slider.setValue(v)
        self.showImageAt(v)

    def showNext(self):
        v = min(self.index_slider.maximum(), self.index_slider.value() + 1)
        self.index_slider.setValue(v)
        self.showImageAt(v)

    def onSliderMoved(self, value):
        self.showImageAt(value)

    # ---------- Deletion logic ----------
    def deleteSelected(self):
        selected = self.getSelectedImagePaths()
        if not selected:
            return
        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f'Are you sure you want to delete {len(selected)} selected image(s) and their related files?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Build set of identifiers to delete (trailing digits or full stem)
        to_delete_ids = set()
        for p in selected:
            stem = Path(p).stem
            m = re.search(r"(\d+)$", stem)
            if m:
                to_delete_ids.add(m.group(1))
            else:
                to_delete_ids.add(stem)

        errors = []
        deleted_files = 0
        for file in Path(self.current_directory).iterdir():
            name = file.stem
            for ident in to_delete_ids:
                if name.endswith(ident) or name == ident:
                    try:
                        file.unlink()
                        deleted_files += 1
                    except Exception as e:
                        errors.append((str(file), str(e)))

        # show summary
        msg = f'Deleted {deleted_files} files.'
        if errors:
            msg += '\nSome files failed to delete:\n' + '\n'.join(f'{p}: {err}' for p, err in errors)
        QMessageBox.information(self, 'Deletion Result', msg)

        # reload
        self.loadImages()
