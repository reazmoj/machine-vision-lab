from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QListWidget, QListWidgetItem, QSlider, QAbstractItemView, QComboBox, QApplication
)
from qfluentwidgets import PushButton, MessageBox, StrongBodyLabel
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

        # selected count label (updates when selection changes)
        self.selected_count = StrongBodyLabel(self.tr("Selected: 0"), self)

        self.delete_selected_btn = PushButton(self.tr("Delete Selected"), self)
        self.delete_selected_btn.clicked.connect(self.deleteSelected)
        self.delete_selected_btn.setEnabled(False)

        top.addWidget(self.select_folder_btn)
        top.addWidget(self.view_mode)
        top.addStretch()
        top.addWidget(self.selected_count)
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
        # custom click behavior: toggle selection on single click (no Ctrl required)
        self.thumb_list.itemClicked.connect(self.onThumbClicked)
        self.thumb_list.itemSelectionChanged.connect(self.onSelectionChanged)
        self.thumb_list.itemDoubleClicked.connect(self.onItemDoubleClicked)

        # Viewer area
        viewer_layout = QVBoxLayout()
        # clickable viewer label (click image to toggle selection)
        class ClickableLabel(QLabel):
            clicked = pyqtSignal()
            def mousePressEvent(self, event):
                super().mousePressEvent(event)
                if event.button() == Qt.MouseButton.LeftButton:
                    self.clicked.emit()

        self.viewer_label = ClickableLabel("No image")
        self.viewer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viewer_label.setMinimumSize(320, 240)
        self.viewer_label.clicked.connect(self.toggleSelectCurrent)

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
            # create icon without badge initially
            icon = self._create_item_icon(p, selected=False)
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
        # ensure visuals reflect selection state (none at load)
        self.refreshThumbnailVisuals()
        self.updateDeleteButtonState()

    def refreshThumbnailVisuals(self):
        """Refresh thumbnail icons to show selection badges and a subtle background for selected items."""
        for i in range(self.thumb_list.count()):
            it = self.thumb_list.item(i)
            path = it.data(Qt.ItemDataRole.UserRole)
            selected = it.isSelected()
            it.setIcon(self._create_item_icon(path, selected=selected))
            # Optional: set a property for QSS to style selected card background if desired
            # We can setData with a role or set a custom data key; QListWidget supports selected styling
        # force repaint
        self.thumb_list.viewport().update()

    # ---------- Selection / view mode ----------
    def onSelectionChanged(self):
        selected = self.getSelectedImagePaths()
        self.updateDeleteButtonState()
        # refresh visuals so selected thumbnails show badges
        try:
            self.refreshThumbnailVisuals()
        except Exception:
            pass
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
        count = len(self.getSelectedImagePaths())
        self.delete_selected_btn.setEnabled(count > 0)
        # update selected count label
        try:
            self.selected_count.setText(self.tr(f"Selected: {count}"))
        except Exception:
            pass

    def onThumbClicked(self, item):
        """Toggle selection on click when no modifier keys are pressed."""
        mods = QApplication.keyboardModifiers()
        ctrl_or_shift = mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        if ctrl_or_shift:
            # let default multi-select behavior happen
            return
        # toggle selection state
        item.setSelected(not item.isSelected())

    def toggleSelectCurrent(self):
        """Toggle selection of the currently viewed image."""
        if not self.image_list:
            return
        idx = self.index_slider.value()
        path = self.image_list[idx]
        # find the corresponding item in thumb_list
        for i in range(self.thumb_list.count()):
            it = self.thumb_list.item(i)
            if it.data(Qt.ItemDataRole.UserRole) == path:
                it.setSelected(not it.isSelected())
                break
        # refresh visuals and counts
        try:
            self.refreshThumbnailVisuals()
        except Exception:
            pass
        self.updateDeleteButtonState()

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
        # Ask for confirmation. Prefer qfluentwidgets.MessageBox when it exposes a
        # question-like API, otherwise fall back to PyQt6 QMessageBox for safety.
        confirm_text = f'Are you sure you want to delete {len(selected)} selected image(s) and their related files?'
        proceed = False
        try:
            if hasattr(MessageBox, 'question'):
                # some qfluentwidgets versions expose a question() helper
                reply = MessageBox.question(self, 'Confirm Deletion', confirm_text)
                proceed = bool(reply)
            else:
                # fallback to QMessageBox from PyQt6
                from PyQt6.QtWidgets import QMessageBox
                resp = QMessageBox.question(self, 'Confirm Deletion', confirm_text,
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                proceed = (resp == QMessageBox.StandardButton.Yes)
        except Exception:
            # As a last resort, try a simple call and interpret truthiness
            try:
                reply = MessageBox.show(self, 'Confirm Deletion', confirm_text)
                proceed = bool(reply)
            except Exception:
                proceed = False

        if not proceed:
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

        # show summary - prefer qfluentwidgets MessageBox.information if available
        msg = f'Deleted {deleted_files} files.'
        if errors:
            msg += '\nSome files failed to delete:\n' + '\n'.join(f'{p}: {err}' for p, err in errors)
        try:
            if hasattr(MessageBox, 'information'):
                MessageBox.information(self, 'Deletion Result', msg)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, 'Deletion Result', msg)
        except Exception:
            # final fallback: print to console
            print(msg)

        # reload
        self.loadImages()
