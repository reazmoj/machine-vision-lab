# coding:utf-8
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard, ComboBox,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QStandardPaths
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QLabel, QFileDialog, QSpacerItem, QVBoxLayout, QHBoxLayout, QSizePolicy

from .segmented_interface import SegmentedInterface
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet

class DetectionInterface(ScrollArea):
    """Object Detection Interface ..."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # detection label
        self.detectionLabel = QLabel(self.tr("Object Detection"), self)

        # model path
        self.modelInThisGroup = SettingCardGroup(
            self.tr("Model path"), self.scrollWidget)
        self.modelPathCard = PushSettingCard(
            self.tr('Choose model path'),
            FIF.DOCUMENT,
            self.tr("Model directory"),
            cfg.get(cfg.modelPath),
            self.modelInThisGroup
        )
        self.modelType = ComboBoxSettingCard(
            cfg.modelType,
            FIF.MENU,
            self.tr('Model Type'),
            self.tr('Please Select your model Type.'),
            texts=['yolov5', 'yolov8', 'yolov9', 'RCNN'],
            parent=self.modelInThisGroup
        )
        

        self.tabGroup = SettingCardGroup(self.tr("Select Image Or Video"), self.scrollWidget)
        self.tabaNavigation = SegmentedInterface(self.scrollWidget)

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('objectDetectionInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.detectionLabel.setObjectName('detectionLabel')
        StyleSheet.DETECTION_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):

        self.detectionLabel.move(36, 30)

        # add cards to group
        self.modelInThisGroup.addSettingCard(self.modelPathCard)
        self.modelInThisGroup.addSettingCard(self.modelType)
        self.tabGroup.addSettingCard(self.tabaNavigation)
        # self.musicInThisPCGroup.addSettingCard(self.downloadFolderCard)


        # add model card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)

        self.modelInThisGroup.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.tabGroup.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.expandLayout.addWidget(self.modelInThisGroup)
        self.expandLayout.addWidget(self.tabGroup)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=1500,
            parent=self
        )

    def __onModelPathCardClicked(self):
        """ Model path card clicked slot """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Pytorch Files (*.pth)", options=QFileDialog.Option.ReadOnly)
        if not file_path or cfg.get(cfg.modelPath) == file_path:
            return

        cfg.set(cfg.modelPath, file_path)
        self.modelPathCard.setContent(file_path)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        
        self.modelPathCard.clicked.connect(self.__onModelPathCardClicked)

        