import sys
import os

from PyQt6.QtCore import Qt, pyqtSignal, QEasingCurve, QUrl, QSize, QTimer
from PyQt6.QtGui import QIcon, QDesktopServices, QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QFrame, QWidget

from qfluentwidgets import (setThemeColor, FluentTranslator, setTheme, Theme, SplitTitleBar,
                            NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen, SystemThemeListener, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF
from ..common.config import ZH_SUPPORT_URL, EN_SUPPORT_URL, cfg
from ..common.signal_bus import signalBus
from ..common.translator import Translator
from ..common import resource

from .home_page import HomePage
from .detection_interface import DetectionInterface
from .reid_interface import ReIdInterface
from .gallery_interface import GalleryInterface
from .setting_interface import SettingInterface
# from .signUp_interface import SigUpInterface

# enable dpi scale
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

def apply_color_overlay(icon_path, color):
    pixmap = QPixmap(icon_path)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()
    return QIcon(pixmap)


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        self.initWindow()
        self.themeListener = SystemThemeListener(self)

        #create sub_interfaces
        self.homeInterface = HomePage(self)
        self.detectionInterface = DetectionInterface(self)
        self.reidentificationInterface = ReIdInterface(self)

        self.settingInterface = SettingInterface(self)

        # enable acrylic effect
        self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()
        self.splashScreen.finish()

        # start theme listener
        self.themeListener.start()

    
    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.switchToSampleCard.connect(self.switchToSample)
        # signalBus.supportSignal.connect(self.onSupport)

    def initNavigation(self):
        t = Translator()
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))

        self.navigationInterface.addSeparator()
        
        pos = NavigationItemPosition.SCROLL
        self.addSubInterface(self.detectionInterface, FIF.ZOOM, self.tr("Object Detection"), pos)
        self.addSubInterface(self.reidentificationInterface, FIF.ALBUM, self.tr("ReIdentification"), pos)

        # add custom widget to bottom
        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('Settings'), NavigationItemPosition.BOTTOM)


    def initWindow(self):
        logo = apply_color_overlay(":resource/images/mut_logo.png", QColor('white'))
        self.resize(1150, 780)
        self.setMinimumWidth(760)
        self.setWindowIcon(logo)
        self.setWindowTitle('Machine Vision Lab')

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def closeEvent(self, e):
        self.themeListener.terminate()
        self.themeListener.deleteLater()
        super().closeEvent(e)

    def _onThemeChangedFinished(self):
        super()._onThemeChangedFinished()

        # retry
        if self.isMicaEffectEnabled():
            QTimer.singleShot(100, lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()))

    def switchToSample(self, routeKey, index):
        """ switch to sample """
        interfaces = self.findChildren(GalleryInterface)
        for w in interfaces:
            if w.objectName() == routeKey:
                self.stackedWidget.setCurrentWidget(w, False)
                w.scrollToCard(index)

#         self.titleBar.titleLabel.setStyleSheet("""
#             QLabel{
#                 background: transparent;
#                 font: 13px 'Segoe UI';
#                 padding: 0 5px;
#                 color: white;
#                 font-weight: bold;                            
#             }
#         """)

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    # internationalization
    # locale = cfg.get(cfg.language).value
    # translator = FluentTranslator(locale)
    # galleryTranslator = QTranslator()
    # galleryTranslator.load(locale, "gallery", ".", ":/gallery/i18n")

    # app.installTranslator(translator)
    # app.installTranslator(galleryTranslator)


    window = MainWindow()
    window.show()
    app.exec()