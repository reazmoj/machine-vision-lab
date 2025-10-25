import sys

from PyQt6.QtCore import Qt, QTranslator, QLocale, QRect
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import setThemeColor, FluentTranslator, setTheme, Theme, SplitTitleBar, isDarkTheme
from signUp_interface import SigUpInterface


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window

def apply_color_overlay(icon_path, color):
    pixmap = QPixmap(icon_path)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()
    return QIcon(pixmap)

class SignUpWindow(Window, SigUpInterface):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # setTheme(Theme.DARK)
        setThemeColor('#28afe9')

        self.setTitleBar(SplitTitleBar(self))
        self.titleBar.raise_()

        self.login_background.setScaledContents(True)
        self.setWindowTitle('Machine Vision Lab')
        # logo_color = QColor('white') if isDarkTheme() else QColor('black')
        logo = apply_color_overlay("app/view/resource/images/mut_logo.png", QColor('white'))
        self.setWindowIcon(logo)
        self.resize(1000, 650)

        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=isDarkTheme())
        # if not isWin11():
        #     color = QColor(25, 33, 42) if isDarkTheme() else QColor(240, 244, 249)
        #     self.setStyleSheet(f"LoginWindow{{background: {color.name()}}}")

        # if sys.platform == "darwin":
        #     self.setSystemTitleBarButtonVisible(True)
        #     self.titleBar.minBtn.hide()
        #     self.titleBar.maxBtn.hide()
        #     self.titleBar.closeBtn.hide()

        self.titleBar.titleLabel.setStyleSheet("""
            QLabel{
                background: transparent;
                font: 13px 'Segoe UI';
                padding: 0 4px;
                color: white
            }
        """)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        pixmap = QPixmap("app/view/resource/images/background-2.png").scaled(
            self.login_background.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self.login_background.setPixmap(pixmap)

    def systemTitleBarRect(self, size):
        """ Returns the system title bar rect, only works for macOS """
        return QRect(size.width() - 75, 0, 75, size.height())



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Internationalization
    translator = FluentTranslator(QLocale())
    app.installTranslator(translator)

    w = SignUpWindow()
    w.show()
    app.exec()