from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QScrollArea, QApplication, QFrame, QComboBox
)
from PyQt6.QtGui import QPixmap
from qfluentwidgets import (
    PushButton, MessageBox, StrongBodyLabel, FlowLayout,
    CardWidget, IconWidget, FluentIcon, SubtitleLabel,
    TransparentToolButton
)
import os
import glob
from pathlib import Path
import re
from ..common.style_sheet import StyleSheet
from ..components.image_card import ImageCard


class DataManagementInterface(QWidget):
    """Data manager that shows a large image viewer and grid of selectable image cards.

    Features:
    - Select folder to load images
    - Grid of image cards with selection overlay and download badge
    - Large viewer with prev/next navigation
    - Click anywhere (viewer or grid) to select
    - Delete selected images and related files
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('dataManagementInterface')

        self.current_directory = ""
        self.image_list = []  # ordered list of image paths
        self.current_index = -1
        self.image_cards = []  # list of ImageCard widgets
        
        self.initUI()

    def initUI(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Top row with folder selection and actions
        top = QHBoxLayout()
        self.select_folder_btn = PushButton(self.tr("Select Folder"), self)
        self.select_folder_btn.clicked.connect(self.selectFolder)
        self.selected_count = StrongBodyLabel(self.tr("Selected: 0"), self)
        self.delete_selected_btn = PushButton(self.tr("Delete Selected"), self)
        self.delete_selected_btn.setIcon(FluentIcon.DELETE)
        self.delete_selected_btn.clicked.connect(self.deleteSelected)
        self.delete_selected_btn.setEnabled(False)

        top.addWidget(self.select_folder_btn)
        top.addStretch()
        top.addWidget(self.selected_count)
        top.addWidget(self.delete_selected_btn)

        root.addLayout(top)

        # Image viewer area
        viewer_frame = QFrame(self)
        viewer_frame.setObjectName('imageViewerFrame')
        viewer_frame.setMinimumHeight(300)
        viewer_layout = QVBoxLayout(viewer_frame)
        viewer_layout.setContentsMargins(0, 0, 0, 0)

        # Viewer image (clickable)
        self.viewer_label = QLabel("No image")
        self.viewer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viewer_label.setMinimumHeight(240)
        self.viewer_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.viewer_label.mouseReleaseEvent = self._on_viewer_clicked

        # Navigation controls below viewer
        nav = QHBoxLayout()
        self.prev_btn = TransparentToolButton(FluentIcon.LEFT_ARROW, self)
        self.prev_btn.clicked.connect(self.showPrev)
        self.next_btn = TransparentToolButton(FluentIcon.RIGHT_ARROW, self)
        self.next_btn.clicked.connect(self.showNext)
        
        # Current image indicator
        self.position_label = SubtitleLabel("0 / 0")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        nav.addStretch()
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.position_label)
        nav.addWidget(self.next_btn)
        nav.addStretch()

        viewer_layout.addWidget(self.viewer_label, 1)
        viewer_layout.addLayout(nav)

        root.addWidget(viewer_frame)

        # Scrollable grid of image cards
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget(scroll)
        self.flow_layout = FlowLayout(scroll_content)
        self.flow_layout.setHorizontalSpacing(12)
        self.flow_layout.setVerticalSpacing(12)
        scroll_content.setLayout(self.flow_layout)
        scroll.setWidget(scroll_content)

        root.addWidget(scroll, 1)
        self.setLayout(root)
        StyleSheet.HOME_INTERFACE.apply(self)

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
        # Clear existing cards and paths
        for card in self.image_cards:
            self.flow_layout.removeWidget(card)
            card.deleteLater()
        self.image_cards.clear()
        self.image_list.clear()
        self.current_index = -1

        # Find image files
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp']
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(self.current_directory, ext)))
        files = sorted(files)

        # Create cards
        for path in files:
            card = ImageCard(path, self)
            card.clicked.connect(lambda p=path: self.showImage(p))
            card.selectionChanged.connect(self.updateDeleteButtonState)
            self.flow_layout.addWidget(card)
            self.image_cards.append(card)
            self.image_list.append(path)

        # Show first image if any loaded
        if self.image_list:
            self.showImage(self.image_list[0])
        else:
            self.viewer_label.setText("No images")
            self.position_label.setText("0 / 0")

        self.updateDeleteButtonState()

    def showImage(self, path):
        """Show an image in the viewer and update current index."""
        try:
            idx = self.image_list.index(path)
        except ValueError:
            return

        self.current_index = idx
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.viewer_label.setText("Failed to load image")
            return

        scaled = pixmap.scaled(
            self.viewer_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.viewer_label.setPixmap(scaled)
        self.position_label.setText(f"{idx + 1} / {len(self.image_list)}")

    def showNext(self):
        """Show the next image in the list."""
        if not self.image_list:
            return
        next_idx = (self.current_index + 1) % len(self.image_list)
        self.showImage(self.image_list[next_idx])

    def showPrev(self):
        """Show the previous image in the list."""
        if not self.image_list:
            return
        prev_idx = (self.current_index - 1) % len(self.image_list)
        self.showImage(self.image_list[prev_idx])

    def getSelectedImagePaths(self):
        """Get paths of all selected images."""
        return [card.image_path for card in self.image_cards if card.isSelected()]

    def updateDeleteButtonState(self):
        """Update delete button and selection count label."""
        selected = self.getSelectedImagePaths()
        count = len(selected)
        self.delete_selected_btn.setEnabled(count > 0)
        self.selected_count.setText(self.tr(f"Selected: {count}"))

    def resizeEvent(self, e):
        """Handle resize - update current image scaling."""
        super().resizeEvent(e)
        if self.current_index >= 0:
            self.showImage(self.image_list[self.current_index])

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
