# coding:utf-8
from PyQt6.QtCore import  QPoint, Qt, QStandardPaths, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy, QFileDialog
from qfluentwidgets import (Pivot, qrouter, Action,Flyout, FlyoutAnimationType, InfoBar, InfoBarPosition, PushSettingCard, 
                            StateToolTip, CommandBarView)

from qfluentwidgets.multimedia import VideoWidget

from qfluentwidgets import FluentIcon as FIF

from ..common.style_sheet import StyleSheet
from ..common.config import cfg
from ..utils.detection_model import DetctionModelInfrence
from ..components.clickable_qlabel import ClickableLabel

class PivotInterface(QWidget):
    """ Pivot interface """

    Nav = Pivot

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimumSize(300, 140)

        # statetool for showing status of model processing
        self.stateTool = None

        # Allow both horizontal and vertical expansion
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Initialize pivot and stacked widget
        self.pivot = self.Nav(self)
        self.pivot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Pivot typically has fixed height

        self.stackedWidget = QStackedWidget(self)
        self.stackedWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)

        # Image Interface Setup
        self.imageWidget = QWidget(self)
        self.imageBox = QVBoxLayout(self.imageWidget)
        self.imageBox.setContentsMargins(10, 10, 10, 10)  
        

        self.imagePathCard = PushSettingCard(
            self.tr('Choose Your Image'),
            FIF.DOCUMENT,
            self.tr("Image directory"),
            "",
        )
        self.imageBox.addWidget(self.imagePathCard)

        # Create labels for the images
        self.label1 = QLabel("Original Image")
        self.label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label2 = QLabel("Processed Image")
        self.label2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.imageDisplay1 = QLabel("No image selected")
        self.imageDisplay1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imageDisplay1.setStyleSheet("background-color: lightgray; border: 1px solid black; padding: 0; margin-right: 5px;")
        self.imageDisplay1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.imageDisplay1.setScaledContents(True)
        self.imageDisplay1.setMinimumSize(300, 300)

        self.create_image_display2()

        # Create vertical layouts for each image and its label
        v_layout1 = QVBoxLayout()
        v_layout1.addWidget(self.label1)
        v_layout1.addWidget(self.imageDisplay1)

        v_layout2 = QVBoxLayout()
        v_layout2.addWidget(self.label2)
        v_layout2.addWidget(self.imageDisplay2)

        # Layout to hold both vertical layouts
        self.imageLayout = QHBoxLayout()
        self.imageLayout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.imageLayout.setSpacing(10)  # Adjust spacing as needed

        self.imageLayout.addLayout(v_layout1, stretch=1)
        self.imageLayout.addLayout(v_layout2, stretch=1)

        self.imageBox.addLayout(self.imageLayout)

        # Video Interface Setup
        self.videoWidget = QWidget(self)
        self.videoBox = QVBoxLayout(self.videoWidget)
        self.videoPathCard = PushSettingCard(
            self.tr('Choose Your Video'),
            FIF.DOCUMENT,
            self.tr("Video directory"),
            "",
        )
        self.videoBox.addWidget(self.videoPathCard)

        # QVideoWidget to display the video
        self.videoDisplay = VideoWidget(self)
        self.videoDisplay.setStyleSheet("background-color: black;")
        self.videoDisplay.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.videoDisplay.setMinimumSize(300, 300)
        # self.videoDisplay.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio) ###############################################
        self.videoBox.addWidget(self.videoDisplay)

        # Add items to pivot
        self.addSubInterface(self.imageWidget, 'imageInterface', self.tr('Image'))
        self.addSubInterface(self.videoWidget, 'videoInterface', self.tr('Video'))

        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)

        # Set the initial widget to imageWidget, not imagePathCard
        self.stackedWidget.setCurrentWidget(self.imageWidget)
        self.pivot.setCurrentItem('imageInterface')  # Use the object name of imageWidget

        # Set the default route key to 'imageInterface'
        qrouter.setDefaultRouteKey(self.stackedWidget, 'imageInterface')

        self.__connectSignalToSlot()

        # Adjust size based on content
        self.adjustSize()

    def create_image_display2(self):
        """Creates the imageDisplay2 widget. Can be overridden by subclasses."""
        self.imageDisplay2 = ClickableLabel("Processing ...")
        self.imageDisplay2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imageDisplay2.setStyleSheet("background-color: lightgray; border: 1px solid black; padding: 0; margin-left: 5px;")
        self.imageDisplay2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.imageDisplay2.setScaledContents(True)
        self.imageDisplay2.setMinimumSize(300, 300)
        self.imageDisplay2.clicked.connect(self.createCommandBarFlyout)
        self.imageDisplay2.hide()  # Initially hide the second QLabel

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())
    
    # 
    
    def __onImagePathCardClicked(self):
        """ Model path card clicked slot """
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Choose an Image"),
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
            options=QFileDialog.Option.ReadOnly
        )
        if not file_path:
            return

        ext = file_path[file_path.rfind('.'):].lower()

        if ext not in allowed_extensions:
            print(f"Warning: Unsupported image format '{ext}'. Please select a valid image file.")
            return

        cfg.set(cfg.imagePath, file_path)

        # Display the first image
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            print(f"Warning: Failed to load image '{file_path}'.")
            self.imageDisplay1.setText("Failed to load image.")
        else:
            self.imageDisplay1.setPixmap(pixmap.scaled(
                self.imageDisplay1.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            print(f"Image '{file_path}' loaded successfully.")

            # Process the image and display the result in the second QLabel
            self.processImage(cfg.get(cfg.imagePath), cfg.get(cfg.modelPath), cfg.get(cfg.galleryFolder))

    def __onVideoPathCardClicked(self):
        """ Model path card clicked slot """
        # Define allowed video extensions
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']

        # Open file dialog with video filters
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Choose a Video"),
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)",
            options=QFileDialog.Option.ReadOnly
        )
        if not file_path:
            return

        # Extract file extension
        ext = file_path[file_path.rfind('.'):].lower()

        if ext not in allowed_extensions:
            print(f"Warning: Unsupported video format '{ext}'. Please select a valid video file.")
            return

        cfg.set(cfg.videoPath, file_path)

        # Display the video
        self.videoDisplay.setVideo(QUrl.fromLocalFile(file_path))
        self.videoDisplay.play()

        # self.videoDisplay.setFullScreen(True)
        print(f"Video '{file_path}' is now playing.")

    def processImage(self, image_path, model_path, gallery_path=None):
        """ Detection Process on the image and display the result in the second QLabel """

        if self.stateTool == None:
            self.stateTool = StateToolTip(
                self.tr('Processing Model'), self.tr('Please wait patiently'), self.window())
            self.stateTool.move(self.stateTool.getSuitablePos())
            self.stateTool.show()

        self.detection_thread = DetctionModelInfrence(model_path, image_path, cfg.get(cfg.modelType))
        self.detection_thread.detection_finished.connect(self.show_result)
        self.detection_thread.start()
        

    def show_result(self, result):

        if self.stateTool:
            self.stateTool.setContent(
                self.tr('The model processing is complete!'))
            self.stateTool.setState(True)
            self.stateTool = None

        pixmap = QPixmap.fromImage(result).scaled(
            self.imageDisplay2.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.imageDisplay2.setPixmap(pixmap)

        self.imageDisplay2.show()  # Show the second QLabel after processing

    
    def createCommandBarFlyout(self):
        view = CommandBarView(self)

        view.addAction(Action(FIF.SHARE, self.tr('Share')))
        view.addAction(Action(FIF.SAVE, self.tr('Save'), triggered=self.saveImage, shortcut='Ctrl+S'))
    
        # view.addAction(Action(FIF.HEART, self.tr('Add to favorate')))
        view.addAction(Action(FIF.DELETE, self.tr('Delete')))

        # view.addHiddenAction(Action(FIF.PRINT, self.tr('Print'), shortcut='Ctrl+P'))
        # view.addHiddenAction(Action(FIF.SETTING, self.tr('Settings'), shortcut='Ctrl+S'))
        view.resizeToSuitableWidth()

        x = self.imageDisplay2.width()
        pos = self.imageDisplay2.mapToGlobal(QPoint(x, 0))
        Flyout.make(view, pos, self, FlyoutAnimationType.FADE_IN)

    def saveImage(self):
        path, ok = QFileDialog.getSaveFileName(
            parent=self,
            caption=self.tr('Save image'),
            directory=QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation),
            filter='PNG (*.png)'
        )
        if not ok:
            return

        self.imageDisplay2.image.save(path)
        self.createSuccessInfoBar()
        

    def createSuccessInfoBar(self):
        # convenient static mothod
        InfoBar.success(
            title=self.tr('Image Saving'),
            content=self.tr("Image Saved Successfully!"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=2000,
            parent=self
    )
        
    def createErrorInfoBar(self):
        InfoBar.error(
            title=self.tr('Title'),
            content=self.tr("Content"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,    # won't disappear automatically
            parent=self
        )
        
    def __connectSignalToSlot(self):
        """ connect signal to slot """
        
        self.imagePathCard.clicked.connect(self.__onImagePathCardClicked)
        self.videoPathCard.clicked.connect(self.__onVideoPathCardClicked)

    def resizeEvent(self, event):
        """ Handle window resize to adjust image display """
        super().resizeEvent(event)
        if not self.imageDisplay1.pixmap().isNull():
            self.imageDisplay1.setPixmap(self.imageDisplay1.pixmap().scaled(
                self.imageDisplay1.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        if self.imageDisplay2.isVisible() and not self.imageDisplay2.pixmap().isNull():
            self.imageDisplay2.setPixmap(self.imageDisplay2.pixmap().scaled(
                self.imageDisplay2.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        
        if self.videoDisplay:
            container_size = self.videoBox.geometry().size()
            self.videoDisplay.resize(container_size)

    def closeEvent(self, event):
        """ Handle cleanup on close """
        if hasattr(self, 'detection_thread') and self.detection_thread.isRunning():
            self.videoDisplay.stop()
            self.detection_thread.quit()
            self.detection_thread.wait()
            self.detection_thread.deleteLater()
        super().closeEvent(event)