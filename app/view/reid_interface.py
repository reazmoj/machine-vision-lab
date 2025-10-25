# coding:utf-8
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QStandardPaths
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QLabel, QFileDialog, QSpacerItem, QVBoxLayout, QHBoxLayout, QSizePolicy

from .reid_segmented_interface import ReidSegmentedInterface
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet

class ReIdInterface(ScrollArea):
    """Re Identification Interface ..."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # detection label
        self.reidLabel = QLabel(self.tr("ReIdentification"), self)

        # model path
        self.modelInThisGroup = SettingCardGroup(
            self.tr("Model And Gallery path"), self.scrollWidget)
        self.modelPathCard = PushSettingCard(
            self.tr('Choose model path'),
            FIF.DOCUMENT,
            self.tr("Model directory"),
            cfg.get(cfg.modelPath),
            self.modelInThisGroup
        )
        self.galleryPathCard = PushSettingCard(
           self.tr('Choose gallery path'),
            FIF.FOLDER, 
            self.tr("Gallery directory"),
            cfg.get(cfg.galleryFolder),
            self.modelInThisGroup
        )

        self.tabGroup = SettingCardGroup(self.tr("Select Image Or Video"), self.scrollWidget)
        self.tabaNavigation = ReidSegmentedInterface(self.scrollWidget)

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('reIdentificationInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.reidLabel.setObjectName('reidLabel')
        StyleSheet.REID_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):

        self.reidLabel.move(36, 30)

        # add cards to group
        self.modelInThisGroup.addSettingCard(self.modelPathCard)
        self.modelInThisGroup.addSettingCard(self.galleryPathCard)
        self.tabGroup.addSettingCard(self.tabaNavigation)

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
        
    def __onGalleryPathCardClicked(self):
        """ Gallery path card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.galleryFolder) == folder:
            return

        cfg.set(cfg.galleryFolder, folder)
        self.galleryPathCard.setContent(folder)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        
        self.modelPathCard.clicked.connect(self.__onModelPathCardClicked)
        self.galleryPathCard.clicked.connect(self.__onGalleryPathCardClicked)

        