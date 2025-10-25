# import sys
# from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QSizePolicy
# from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
# from PyQt6.QtMultimediaWidgets import QVideoWidget
# from PyQt6.QtCore import QUrl

# class VideoPlayer(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Simple Video Player")
#         self.setGeometry(100, 100, 800, 600)

#         self.layout = QVBoxLayout()

#         # Video Widget
#         self.video_widget = QVideoWidget()
#         self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
#         self.layout.addWidget(self.video_widget)

#         # Play Button
#         self.play_button = QPushButton("Choose Video and Play")
#         self.play_button.clicked.connect(self.open_file)
#         self.layout.addWidget(self.play_button)

#         self.setLayout(self.layout)

#         # Media Player
#         self.player = QMediaPlayer()
#         self.audio_output = QAudioOutput()
#         self.player.setAudioOutput(self.audio_output)
#         self.player.setVideoOutput(self.video_widget)

#         # Connect error signal
#         self.player.errorOccurred.connect(self.handle_error)

#     def open_file(self):
#         file_path, _ = QFileDialog.getOpenFileName(
#             self,
#             "Choose a Video",
#             "",
#             "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
#         )
#         if file_path:
#             url = QUrl.fromLocalFile(file_path)
#             self.player.setSource(url)
#             self.player.play()

#     def handle_error(self, error):
#         print(f"Error: {self.player.errorString()}")

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     player = VideoPlayer()
#     player.show()
#     sys.exit(app.exec())


import sys
import vlc
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWindow

class VLCVideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLC Video Player")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()
        
        # Video Frame Placeholder
        self.video_frame = QWidget()
        self.layout.addWidget(self.video_frame)

        # Play Button
        self.play_button = QPushButton("Choose Video and Play")
        self.play_button.clicked.connect(self.open_file)
        self.layout.addWidget(self.play_button)

        self.setLayout(self.layout)

        # VLC Instance
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a Video",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
        )
        if file_path:
            media = self.instance.media_new(file_path)
            self.player.set_media(media)
            if sys.platform.startswith('linux'):  # for Linux using the X Server
                self.player.set_xwindow(self.video_frame.winId())
            elif sys.platform == "win32":  # for Windows
                self.player.set_hwnd(self.video_frame.winId())
            elif sys.platform == "darwin":  # for MacOS
                self.player.set_nsobject(int(self.video_frame.winId()))
            self.player.play()

    def closeEvent(self, event):
        self.player.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VLCVideoPlayer()
    player.show()
    sys.exit(app.exec())